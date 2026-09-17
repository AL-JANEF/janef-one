from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .firewall import SkillFirewall, SkillScanResult


class SkillDiscoveryError(ValueError):
    pass


class SkillActivationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SkillRoot:
    path: Path
    scope: str
    priority: int


@dataclass(frozen=True, slots=True)
class SkillRecord:
    name: str
    description: str
    location: Path
    scope: str
    priority: int
    compatibility: str = ""

    @property
    def directory(self) -> Path:
        return self.location.parent


@dataclass(frozen=True, slots=True)
class SkillActivation:
    skill: SkillRecord
    body: str
    resources: tuple[str, ...]
    scan: SkillScanResult


_FRONTMATTER_NAME = re.compile(r"^name:\s*['\"]?([a-z0-9]+(?:-[a-z0-9]+)*)['\"]?\s*$", re.M)
_FRONTMATTER_DESCRIPTION = re.compile(r"^description:\s*(.+?)\s*$", re.M)
_FRONTMATTER_COMPATIBILITY = re.compile(r"^compatibility:\s*(.+?)\s*$", re.M)


def _split_skill(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SkillDiscoveryError("SKILL.md is missing opening YAML frontmatter")
    try:
        end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise SkillDiscoveryError("SKILL.md frontmatter is not closed") from exc
    return "\n".join(lines[1:end]), "\n".join(lines[end + 1 :]).strip()


def _clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value.strip()


def parse_skill(path: str | Path, *, scope: str = "unknown", priority: int = 0) -> SkillRecord:
    location = Path(path).resolve()
    if location.name != "SKILL.md" or not location.is_file() or location.is_symlink():
        raise SkillDiscoveryError(f"invalid skill entrypoint: {location}")
    if location.stat().st_size > 512_000:
        raise SkillDiscoveryError("SKILL.md exceeds 512KB discovery limit")
    text = location.read_text(encoding="utf-8")
    frontmatter, _ = _split_skill(text)
    name_match = _FRONTMATTER_NAME.search(frontmatter)
    desc_match = _FRONTMATTER_DESCRIPTION.search(frontmatter)
    if not name_match or not desc_match:
        raise SkillDiscoveryError("SKILL.md requires valid name and description")
    name = name_match.group(1)
    description = _clean_scalar(desc_match.group(1))
    if not description:
        raise SkillDiscoveryError("skill description is empty")
    if len(name) > 64:
        raise SkillDiscoveryError("skill name exceeds 64 characters")
    if len(description) > 1024:
        raise SkillDiscoveryError("skill description exceeds 1024 characters")
    if name != location.parent.name:
        raise SkillDiscoveryError(
            f"skill name {name!r} must match parent directory {location.parent.name!r}"
        )
    compat_match = _FRONTMATTER_COMPATIBILITY.search(frontmatter)
    compatibility = _clean_scalar(compat_match.group(1)) if compat_match else ""
    if len(compatibility) > 500:
        raise SkillDiscoveryError("skill compatibility exceeds 500 characters")
    return SkillRecord(name, description, location, scope, priority, compatibility)


class SkillRegistry:
    """Discover and activate Agent Skills using bounded progressive disclosure."""

    def __init__(
        self,
        roots: Iterable[SkillRoot] = (),
        *,
        firewall: SkillFirewall | None = None,
        max_depth: int = 6,
        max_directories: int = 2000,
        max_resources: int = 200,
    ) -> None:
        if max_depth < 1 or max_directories < 1 or max_resources < 1:
            raise ValueError("skill discovery limits must be positive")
        self.roots = tuple(roots)
        self.firewall = firewall or SkillFirewall()
        self.max_depth = max_depth
        self.max_directories = max_directories
        self.max_resources = max_resources
        self._skills: dict[str, SkillRecord] = {}
        self.diagnostics: list[str] = []

    def discover(self) -> tuple[SkillRecord, ...]:
        found: dict[str, SkillRecord] = {}
        diagnostics: list[str] = []
        directories_seen = 0
        for root in sorted(self.roots, key=lambda r: (r.priority, r.scope, str(r.path))):
            base = root.path.expanduser().resolve()
            if not base.exists() or not base.is_dir() or base.is_symlink():
                diagnostics.append(f"skip unavailable skill root: {base}")
                continue
            for candidate in sorted(base.rglob("SKILL.md")):
                try:
                    rel = candidate.relative_to(base)
                except ValueError:
                    continue
                depth = len(rel.parts) - 1
                if depth > self.max_depth:
                    continue
                directories_seen += 1
                if directories_seen > self.max_directories:
                    diagnostics.append(f"discovery stopped at max_directories={self.max_directories}")
                    self._skills = found
                    self.diagnostics = diagnostics
                    return self.catalog()
                if candidate.is_symlink() or any(part in {".git", "node_modules", "__pycache__", ".venv"} for part in rel.parts):
                    continue
                try:
                    record = parse_skill(candidate, scope=root.scope, priority=root.priority)
                except (OSError, UnicodeDecodeError, SkillDiscoveryError) as exc:
                    diagnostics.append(f"skip {candidate}: {exc}")
                    continue
                existing = found.get(record.name)
                if existing is None or record.priority > existing.priority:
                    if existing is not None:
                        diagnostics.append(
                            f"skill collision {record.name}: {record.location} overrides {existing.location}"
                        )
                    found[record.name] = record
                elif record.priority == existing.priority:
                    # Deterministic same-scope tie-breaker: lexical path wins.
                    winner = min(existing, record, key=lambda x: str(x.location))
                    loser = record if winner is existing else existing
                    found[record.name] = winner
                    diagnostics.append(f"skill collision {record.name}: kept {winner.location}, skipped {loser.location}")
                else:
                    diagnostics.append(f"skill collision {record.name}: kept higher-priority {existing.location}")
        self._skills = found
        self.diagnostics = diagnostics
        return self.catalog()

    def catalog(self) -> tuple[SkillRecord, ...]:
        return tuple(sorted(self._skills.values(), key=lambda row: row.name))

    def get(self, name: str) -> SkillRecord | None:
        return self._skills.get(name)

    def activate(self, name: str, *, allow_review: bool = False) -> SkillActivation:
        record = self._skills.get(name)
        if record is None:
            raise SkillActivationError(f"unknown skill: {name}")
        scan = self.firewall.scan(record.directory)
        if scan.decision == "block" or (scan.decision == "review" and not allow_review):
            raise SkillActivationError(f"skill {name!r} failed firewall gate: {scan.decision}")
        text = record.location.read_text(encoding="utf-8")
        _, body = _split_skill(text)
        resources: list[str] = []
        base = record.directory.resolve()
        for path in sorted(base.rglob("*")):
            if path.is_symlink() or not path.is_file() or path == record.location:
                continue
            if any(part in {".git", "__pycache__", "node_modules", ".venv"} for part in path.relative_to(base).parts):
                continue
            try:
                resolved = path.resolve(strict=True)
                resolved.relative_to(base)
            except (OSError, ValueError):
                continue
            resources.append(path.relative_to(base).as_posix())
            if len(resources) >= self.max_resources:
                break
        return SkillActivation(record, body, tuple(resources), scan)
