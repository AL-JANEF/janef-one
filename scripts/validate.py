#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))

required = {
    "SKILL.md",
    "SYSTEM_CORE.md",
    "SOURCE-MATRIX.md",
    "README.md",
    "LICENSE",
    "NOTICE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "RELEASING.md",
    "manifest.json",
    "pyproject.toml",
    "references/ARCHITECTURE.md",
    "references/SECURITY_MODEL.md",
    "references/BENCHMARK_PROTOCOL.md",
    "references/AGENT_SKILLS_COMPATIBILITY.md",
}
required.update(f"modules/{name}" for name in manifest["modules"])
required.update(f"providers/{name}" for name in manifest["providers"])
required.update(f"adapters/{name}" for name in manifest["adapters"])
required.update(manifest["source_pipeline"])

missing = sorted(path for path in required if not (root / path).exists())
if missing:
    print("Missing required files:", *[f"- {x}" for x in missing], sep="\n")
    sys.exit(1)

skill = (root / "SKILL.md").read_text(encoding="utf-8")
lines = skill.splitlines()
if len(lines) > 500:
    raise SystemExit(f"SKILL.md exceeds 500 lines: {len(lines)}")
if not lines or lines[0] != "---":
    raise SystemExit("SKILL.md must begin with YAML frontmatter")
try:
    fm_end = lines[1:].index("---") + 1
except ValueError as exc:
    raise SystemExit("SKILL.md frontmatter is not closed") from exc
frontmatter = "\n".join(lines[1:fm_end])
name_match = re.search(r"^name:\s*([^\s]+)\s*$", frontmatter, re.M)
desc_match = re.search(r"^description:\s*(.+)$", frontmatter, re.M)
if not name_match or name_match.group(1) != "janef-one":
    raise SystemExit("SKILL.md name must be janef-one")
if not desc_match or not (1 <= len(desc_match.group(1).strip()) <= 1024):
    raise SystemExit("SKILL.md description must be 1..1024 characters")
if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name_match.group(1)):
    raise SystemExit("SKILL.md name is not valid kebab-case")

if manifest.get("entrypoint") != "SKILL.md":
    raise SystemExit("manifest entrypoint mismatch")

version = manifest.get("version", "")
if not re.fullmatch(r"\d+\.\d+\.\d+", version):
    raise SystemExit(f"manifest.json version {version!r} is not a valid X.Y.Z release version")

# manifest.json is the canonical version source. pyproject.toml's [project]
# version and the installed runtime's __version__ cannot be *derived* from it
# at import/build time (manifest.json is not shipped inside the built wheel),
# so they are independently maintained literals that must be kept identical
# to the canonical value. This check is what prevents version drift between
# package metadata and release files, rather than trusting them to agree.
pyproject_text = (root / "pyproject.toml").read_text(encoding="utf-8")
pyproject_match = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', pyproject_text)
if not pyproject_match:
    raise SystemExit("pyproject.toml is missing a [project] version field")
if pyproject_match.group(1) != version:
    raise SystemExit(f"version drift: manifest.json={version!r} pyproject.toml={pyproject_match.group(1)!r}")

init_text = (root / "runtime/janef_one/__init__.py").read_text(encoding="utf-8")
init_match = re.search(r'(?m)^__version__\s*=\s*"([^"]+)"\s*$', init_text)
if not init_match:
    raise SystemExit("runtime/janef_one/__init__.py is missing __version__")
if init_match.group(1) != version:
    raise SystemExit(f"version drift: manifest.json={version!r} runtime/janef_one/__init__.py={init_match.group(1)!r}")

release_notes = root / f"RELEASE_NOTES_v{version}.md"
if not release_notes.exists():
    raise SystemExit(f"missing release notes for current version: {release_notes.name}")

cases = json.loads((root / "evals/cases.json").read_text(encoding="utf-8"))
ids = [case["id"] for case in cases]
if len(ids) != len(set(ids)):
    raise SystemExit("duplicate eval IDs")
if len(cases) < 15:
    raise SystemExit("expected at least 15 seed eval cases")

print(
    f"OK: JANEF ONE {manifest['version']} | {len(manifest['modules'])} modules | "
    f"{len(manifest['providers'])} provider profiles | {len(cases)} seed evals | SKILL.md {len(lines)} lines"
)
