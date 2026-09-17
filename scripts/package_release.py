#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
VERSION = MANIFEST["version"]
OUT = ROOT.parent / f"janef-one-v{VERSION}.zip"
SHA = OUT.with_suffix(OUT.suffix + ".sha256")

EXCLUDED_DIRS = {
    ".git", ".source_cache", ".janef-one-state", "__pycache__", ".pytest_cache",
    ".venv", "dist", "build", ".coverage", "htmlcov", "runtime/janef_one_runtime.egg-info",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_FILES = {
    "sources/catalog.json", "sources/rule_candidates.json", "sources/FUSION_CANDIDATES.md",
    "benchmarks/runtime-report.json",
}
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def excluded(rel: Path) -> bool:
    posix = rel.as_posix()
    if posix in EXCLUDED_FILES:
        return True
    if rel.suffix in EXCLUDED_SUFFIXES:
        return True
    parts = rel.parts
    if any(part in {".git", ".source_cache", ".janef-one-state", "__pycache__", ".pytest_cache", ".venv", "dist", "build", "htmlcov"} for part in parts):
        return True
    if posix.startswith("runtime/janef_one_runtime.egg-info/"):
        return True
    if rel.name == ".coverage":
        return True
    return False


files = [p for p in sorted(ROOT.rglob("*")) if p.is_file() and not excluded(p.relative_to(ROOT))]

with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in files:
        rel = Path("janef-one") / path.relative_to(ROOT)
        info = zipfile.ZipInfo(rel.as_posix(), FIXED_TIME)
        info.create_system = 3
        mode = 0o755 if (path.stat().st_mode & stat.S_IXUSR) else 0o644
        info.external_attr = (mode & 0xFFFF) << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        info.flag_bits |= 0x800  # UTF-8
        archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
SHA.write_text(f"{digest}  {OUT.name}\n", encoding="utf-8")
print(f"{OUT} | {len(files)} files | {OUT.stat().st_size} bytes | sha256={digest}")
