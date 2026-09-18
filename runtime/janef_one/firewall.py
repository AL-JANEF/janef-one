from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Finding:
    severity: str
    code: str
    message: str
    path: str
    line: int
    fingerprint: str


@dataclass(frozen=True, slots=True)
class SkillScanResult:
    score: int
    decision: str
    findings: tuple[Finding, ...] = field(default_factory=tuple)
    approved_findings: tuple[Finding, ...] = field(default_factory=tuple)
    scanned_files: int = 0
    scanned_bytes: int = 0


@dataclass(frozen=True, slots=True)
class _Rule:
    severity: str
    code: str
    weight: int
    pattern: re.Pattern[str]
    executable_only: bool = False


class SkillFirewall:
    """Bounded deterministic static pre-load scanner for Agent Skill packages.

    The scanner treats skill instructions and executable surfaces separately,
    refuses symlink indirection, caps resource consumption, and supports exact
    hash-based reviewed exceptions. It is a gate, not a malware sandbox.
    """

    RULES: tuple[_Rule, ...] = (
        _Rule(
            "critical",
            "prompt.override",
            50,
            re.compile(
                r"^\s*(?:[-*]\s*)?(?:you\s+(?:must|should)\s+)?"
                r"(?:ignore|disregard|override|bypass)\b.{0,100}\b"
                r"(?:system|developer|previous|higher[- ]priority|safety)\b.{0,50}\b(?:instructions?|rules?|policy)",
                re.I,
            ),
        ),
        _Rule(
            "high",
            "authority.claim",
            30,
            re.compile(
                r"\b(?:this skill|these instructions|this prompt)\b.{0,80}"
                r"\b(?:highest authority|supersedes all|cannot be overridden|root authority|above system)\b",
                re.I,
            ),
        ),
        _Rule(
            "high",
            "secrets.read",
            30,
            re.compile(
                r"\b(?:cat|type|open|read_text|readFile|source|copy|cp)\b.{0,120}"
                r"(?:~?/\.ssh|\.aws/credentials|\.config/gcloud|(?:^|[/\\])\.env\b|private[_-]?key|id_rsa)",
                re.I,
            ),
        ),
        _Rule(
            "critical",
            "destructive.shell",
            55,
            re.compile(
                r"\brm\s+(?:-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b|"
                r"\bmkfs(?:\.|\s)|\bdd\s+if=|\bshutdown\b|\breboot\b|"
                r"\b(?:diskutil\s+erase|format\s+[a-z]:)",
                re.I,
            ),
        ),
        _Rule(
            "critical",
            "download.pipe-shell",
            50,
            re.compile(r"\b(?:curl|wget)\b[^\n|]{0,240}\|\s*(?:sudo\s+)?(?:ba)?sh\b", re.I),
            executable_only=True,
        ),
        _Rule(
            "high",
            "network.exfil",
            35,
            re.compile(
                r"\b(?:curl|wget|requests\.(?:post|put)|httpx\.(?:post|put))\b.{0,180}"
                r"\b(?:token|secret|credential|password|\.env|private[_-]?key|id_rsa)\b",
                re.I,
            ),
            executable_only=True,
        ),
        _Rule(
            "high",
            "privilege.escalation",
            30,
            re.compile(r"\bsudo\b|\bchmod\s+777\b|\bchown\s+-R\b", re.I),
            executable_only=True,
        ),
        _Rule(
            "high",
            "persistence.install",
            30,
            re.compile(
                r"\b(?:crontab|launchctl|schtasks|systemctl\s+enable|rc\.local|startup)\b",
                re.I,
            ),
            executable_only=True,
        ),
        _Rule(
            "high",
            "shell.exec",
            25,
            re.compile(r"\bos\.system\s*\(|\bshell\s*=\s*True\b", re.I),
            executable_only=True,
        ),
        _Rule(
            "medium",
            "dynamic.exec",
            12,
            re.compile(
                r"\b(?:eval|exec)\s*\(|child_process\.(?:exec|spawn)|subprocess\.(?:Popen|run|call|check_output)\b",
                re.I,
            ),
            executable_only=True,
        ),
        _Rule(
            "high",
            "encoded.exec",
            25,
            re.compile(r"(?:base64\.b64decode|frombase64string).{0,160}\b(?:exec|eval|invoke-expression)\b", re.I),
            executable_only=True,
        ),
        _Rule(
            "medium",
            "package.lifecycle",
            15,
            re.compile(r'["\'](?:preinstall|postinstall|prepare)["\']\s*:', re.I),
            executable_only=True,
        ),
    )

    TEXT_SUFFIXES = {".md", ".txt", ".py", ".sh", ".bash", ".zsh", ".js", ".mjs", ".cjs", ".ts", ".json", ".yaml", ".yml", ".toml", ".ps1"}
    EXEC_SUFFIXES = {".py", ".sh", ".bash", ".zsh", ".js", ".mjs", ".cjs", ".ts", ".ps1"}
    EXCLUDED_PARTS = {".git", "__pycache__", ".source_cache", ".venv", "node_modules", "dist", "build"}
    FIXTURE_PARTS = {"tests", "test", "evals", "fixtures"}
    # Non-executable_only rules that are prone to false positives on descriptive
    # or sample text data. Only relaxed for passive (non-executable-surface)
    # files inside FIXTURE_PARTS directories; executable/script/config surfaces
    # get full scanning everywhere, including inside these directories.
    PASSIVE_FIXTURE_LENIENT_CODES = {"destructive.shell", "prompt.override", "authority.claim", "secrets.read"}
    ALLOWLIST_NAME = ".janef-one-firewall-allowlist.json"

    # Deterministic normalizations for straightforward shell/script obfuscation:
    # $IFS-based whitespace substitution and quote-split string concatenation.
    _DEOBFUSCATION_STEPS: tuple[tuple[re.Pattern[str], str], ...] = (
        (re.compile(r"\$\{IFS\}|\$IFS\b"), " "),
        (re.compile(r"""(['"])\s*\+\s*(?=['"])"""), ""),
        (re.compile(r"""['"]"""), ""),
    )

    def __init__(
        self,
        *,
        max_files: int = 5000,
        max_file_bytes: int = 2_000_000,
        max_total_bytes: int = 50_000_000,
        allowlist_path: str | Path | None = None,
    ) -> None:
        if min(max_files, max_file_bytes, max_total_bytes) < 1:
            raise ValueError("scan limits must be positive")
        self.max_files = max_files
        self.max_file_bytes = max_file_bytes
        self.max_total_bytes = max_total_bytes
        # Reviewed exceptions are only ever honored from a path the *caller*
        # explicitly names (trusted host/operator input). A scanned package
        # can never cause its own findings to be approved: nothing inside
        # `root` is ever auto-discovered or auto-trusted as an allowlist.
        self.allowlist_path = Path(allowlist_path) if allowlist_path is not None else None

    @staticmethod
    def _fingerprint(code: str, path: str, message: str) -> str:
        normalized = re.sub(r"\s+", " ", message).strip()
        return hashlib.sha256(f"{code}\0{path}\0{normalized}".encode("utf-8")).hexdigest()

    def _finding(self, severity: str, code: str, message: str, path: str, line: int) -> Finding:
        return Finding(severity, code, message, path, line, self._fingerprint(code, path, message))

    @classmethod
    def _deobfuscate(cls, line: str) -> str:
        result = line
        for pattern, repl in cls._DEOBFUSCATION_STEPS:
            result = pattern.sub(repl, result)
        return result

    @staticmethod
    def _has_shebang(path: Path) -> bool:
        try:
            with path.open("rb") as handle:
                head = handle.read(64)
        except OSError:
            return False
        return head.startswith(b"#!")

    def _load_allowlist(self) -> set[str]:
        """Load reviewed-exception fingerprints from an explicitly trusted path.

        The allowlist location is never auto-discovered from inside the
        scanned package root; it is only ever the path a trusted caller
        explicitly configured on this instance (e.g. host/CI code scanning
        its own reviewed repository, or an operator-supplied `--allowlist`).
        A scanned candidate package cannot cause its own files to be read as
        approvals: nothing about `scan()`'s `root` argument feeds this path.
        If the caller did not configure an allowlist, there are no approvals
        (fail closed: every finding stays active). If the caller configured
        a path and it is missing or malformed, that is treated as ambiguous
        approval provenance and the scan blocks rather than silently
        granting zero or partial exceptions.
        """
        if self.allowlist_path is None:
            return set()
        path = self.allowlist_path
        if not path.is_file():
            raise ValueError(f"configured firewall allowlist does not exist: {path}")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid firewall allowlist: {exc}") from exc
        if raw.get("version") != 1 or not isinstance(raw.get("approvals"), list):
            raise ValueError("firewall allowlist must have version=1 and approvals[]")
        approved: set[str] = set()
        for row in raw["approvals"]:
            if not isinstance(row, dict):
                raise ValueError("invalid firewall approval entry")
            fp = row.get("fingerprint")
            reason = row.get("reason")
            if not isinstance(fp, str) or not re.fullmatch(r"[0-9a-f]{64}", fp):
                raise ValueError("invalid firewall approval fingerprint")
            if not isinstance(reason, str) or len(reason.strip()) < 10:
                raise ValueError("firewall approval requires a meaningful reason")
            approved.add(fp)
        return approved

    def scan(self, root: str | Path) -> SkillScanResult:
        root_path = Path(root).resolve()
        findings: list[Finding] = []
        if not root_path.is_dir():
            finding = self._finding("critical", "format.not-directory", "skill root must be a directory", ".", 1)
            return SkillScanResult(0, "block", (finding,), (), 0, 0)

        try:
            approved_fingerprints = self._load_allowlist()
        except ValueError as exc:
            finding = self._finding("critical", "allowlist.invalid", str(exc), self.ALLOWLIST_NAME, 1)
            return SkillScanResult(0, "block", (finding,), (), 0, 0)

        skill_file = root_path / "SKILL.md"
        if not skill_file.exists():
            findings.append(self._finding("critical", "format.missing-skill", "SKILL.md is required", "SKILL.md", 1))
        elif skill_file.is_symlink():
            findings.append(self._finding("critical", "filesystem.symlink", "SKILL.md must not be a symlink", "SKILL.md", 1))
        else:
            self._check_frontmatter(skill_file, findings, root_path.name)

        file_count = 0
        total_bytes = 0
        paths = sorted(root_path.rglob("*"))
        for path in paths:
            rel_path = path.relative_to(root_path)
            if any(part in self.EXCLUDED_PARTS for part in rel_path.parts):
                continue
            if path.is_symlink():
                findings.append(self._finding("high", "filesystem.symlink", "symlinks are not allowed in skill packages", rel_path.as_posix(), 1))
                continue
            if not path.is_file():
                continue
            file_count += 1
            if file_count > self.max_files:
                findings.append(self._finding("critical", "resource.file-count", f"scan exceeds max_files={self.max_files}", rel_path.as_posix(), 1))
                break
            try:
                size = path.stat().st_size
            except OSError as exc:
                findings.append(self._finding("high", "filesystem.stat", str(exc), rel_path.as_posix(), 1))
                continue
            total_bytes += size
            if total_bytes > self.max_total_bytes:
                findings.append(self._finding("critical", "resource.total-bytes", f"scan exceeds max_total_bytes={self.max_total_bytes}", rel_path.as_posix(), 1))
                break

            suffix = path.suffix.lower()
            is_known_text = suffix in self.TEXT_SUFFIXES
            # Extensionless scripts (no recognized suffix) are still executable
            # surfaces when they carry a shebang; content must be scanned like
            # any other script, not silently treated as an opaque binary.
            has_shebang = False if is_known_text else self._has_shebang(path)

            if size > self.max_file_bytes and (is_known_text or has_shebang):
                findings.append(self._finding("high", "resource.file-bytes", f"text file exceeds max_file_bytes={self.max_file_bytes}", rel_path.as_posix(), 1))
                continue
            if not is_known_text and not has_shebang:
                # Executable unknown binaries are not valid passive skill resources.
                if os.access(path, os.X_OK):
                    findings.append(self._finding("high", "binary.executable", "unrecognized executable file in skill package", rel_path.as_posix(), 1))
                continue

            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                findings.append(self._finding("medium", "text.invalid-utf8", "declared text file is not valid UTF-8", rel_path.as_posix(), 1))
                continue
            rel = rel_path.as_posix()
            executable = has_shebang or self._is_executable_surface(rel_path)
            in_fixture_dir = any(part in self.FIXTURE_PARTS for part in rel_path.parts)
            lines = text.splitlines()
            for line_no, line in enumerate(lines, start=1):
                for rule in self.RULES:
                    if rule.executable_only and not executable:
                        continue
                    if in_fixture_dir and not executable and rule.code in self.PASSIVE_FIXTURE_LENIENT_CODES:
                        # Passive (non-executable-surface) sample/fixture data
                        # may narrowly avoid content-pattern findings. This
                        # never applies to executable/script/config surfaces,
                        # which are always scanned in full, including inside
                        # tests/fixtures directories.
                        continue
                    matched = rule.pattern.search(line)
                    if not matched and executable:
                        matched = rule.pattern.search(self._deobfuscate(line))
                    if matched:
                        message = line.strip()[:300]
                        findings.append(self._finding(rule.severity, rule.code, message, rel, line_no))

        approved: list[Finding] = []
        active: list[Finding] = []
        for finding in findings:
            if finding.fingerprint in approved_fingerprints:
                approved.append(finding)
            else:
                active.append(finding)

        weights = {rule.code: rule.weight for rule in self.RULES}
        weights.update({
            "format.missing-skill": 100,
            "format.not-directory": 100,
            "format.frontmatter": 35,
            "format.name-mismatch": 35,
            "filesystem.symlink": 40,
            "filesystem.stat": 20,
            "resource.file-count": 100,
            "resource.total-bytes": 100,
            "resource.file-bytes": 25,
            "binary.executable": 35,
            "text.invalid-utf8": 10,
            "allowlist.invalid": 100,
        })
        risk = min(100, sum(weights.get(item.code, 5) for item in active))
        if any(item.severity == "critical" for item in active) or risk >= 70:
            decision = "block"
        elif risk >= 10 or any(item.severity == "high" for item in active):
            decision = "review"
        else:
            decision = "allow"
        return SkillScanResult(
            score=max(0, 100 - risk),
            decision=decision,
            findings=tuple(active),
            approved_findings=tuple(approved),
            scanned_files=file_count,
            scanned_bytes=total_bytes,
        )

    @classmethod
    def _is_executable_surface(cls, rel_path: Path) -> bool:
        if rel_path.name in {"package.json", "pyproject.toml"}:
            return True
        if rel_path.suffix.lower() in cls.EXEC_SUFFIXES:
            return True
        return any(part in {"scripts", "hooks", "bin"} for part in rel_path.parts)

    def _check_frontmatter(self, path: Path, findings: list[Finding], directory_name: str) -> None:
        lines = path.read_text(encoding="utf-8").splitlines()
        valid = len(lines) >= 4 and lines[0].strip() == "---"
        end = -1
        if valid:
            try:
                end = lines[1:].index("---") + 1
            except ValueError:
                valid = False
        name = ""
        if valid:
            block = "\n".join(lines[1:end])
            name_match = re.search(r"^name:\s*([-a-z0-9]+)\s*$", block, re.M)
            desc_match = re.search(r"^description:\s*(.+)$", block, re.M)
            valid = bool(name_match and desc_match and desc_match.group(1).strip())
            if name_match:
                name = name_match.group(1)
        if not valid:
            findings.append(self._finding("high", "format.frontmatter", "invalid or incomplete SKILL.md frontmatter", "SKILL.md", 1))
            return
        if directory_name and directory_name != name:
            findings.append(self._finding("high", "format.name-mismatch", f"skill name {name!r} does not match directory {directory_name!r}", "SKILL.md", 1))
