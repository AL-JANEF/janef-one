#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, re

def headings(text):
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        if re.match(r"^#{1,6}\s+\S", line):
            out.append({"line": i, "heading": line.strip()})
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=".source_cache/system_prompts_leaks")
    ap.add_argument("--out", default="sources/catalog.json")
    args = ap.parse_args()

    root = Path(args.source).resolve()
    output = Path(args.out).resolve()
    if not root.exists():
        raise SystemExit("Source cache not found. Run scripts/sync_sources.py first.")

    entries = []
    for p in sorted(root.rglob("*.md")):
        if ".git" in p.parts:
            continue
        raw = p.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        rel = p.relative_to(root).as_posix()
        provider = rel.split("/", 1)[0] if "/" in rel else "root"
        entries.append({
            "path": rel,
            "provider": provider,
            "bytes": len(raw),
            "lines": text.count("\n") + 1,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "headings": headings(text),
        })

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "source_root": str(root),
        "count": len(entries),
        "entries": entries,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Indexed {len(entries)} markdown files -> {output}")

if __name__ == "__main__":
    main()
