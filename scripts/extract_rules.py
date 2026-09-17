#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, re

CATEGORIES = {
    "instruction_resolution": ["instruction", "priority", "override", "system", "developer", "user request"],
    "tool_use": ["tool", "call", "bash", "shell", "browser", "computer", "mcp", "connector"],
    "research": ["search", "research", "source", "citation", "web", "current", "latest", "verify"],
    "coding": ["code", "repo", "repository", "edit", "test", "lint", "build", "git", "implementation"],
    "memory_context": ["memory", "context", "remember", "preference", "profile"],
    "files_artifacts": ["file", "pdf", "document", "spreadsheet", "slides", "artifact", "image"],
    "safety_authorization": ["safety", "refuse", "permission", "authorize", "delete", "destructive", "credential", "secret"],
    "response": ["response", "answer", "format", "tone", "concise", "markdown", "heading", "bullet"],
    "agents_planning": ["agent", "subagent", "plan", "parallel", "delegate", "task"],
    "verification": ["verify", "verification", "observed", "passed", "failed", "check", "validate"],
}

MODAL = re.compile(
    r"\b(must|must not|never|always|should|should not|do not|don't|prefer|use|avoid|"
    r"before|after|when|only|cannot|can't|required|important|critical|make sure)\b",
    re.I,
)

def normalize(s):
    s = re.sub(r"`[^`]+`", "`<literal>`", s)
    s = re.sub(r"https?://\S+", "<url>", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def classify(text):
    low = text.lower()
    scored = []
    for cat, keys in CATEGORIES.items():
        score = sum(1 for k in keys if k in low)
        if score:
            scored.append((score, cat))
    scored.sort(reverse=True)
    return [c for _, c in scored[:3]] or ["other"]

def candidates_from_file(path, provider, rel):
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    heading = ""
    for lineno, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if s.startswith("#"):
            heading = s.lstrip("#").strip()
            continue
        if not s or len(s) < 18 or len(s) > 1200:
            continue
        bullet = s.startswith(("-", "*", "1.", "2.", "3.", "4.", "5."))
        if not (bullet or MODAL.search(s)):
            continue
        cleaned = re.sub(r"^[-*]\s+", "", s)
        cleaned = re.sub(r"^\d+\.\s+", "", cleaned)
        norm = normalize(cleaned)
        if len(norm) < 18:
            continue
        out.append({
            "provider": provider,
            "path": rel,
            "line": lineno,
            "heading": heading,
            "text": cleaned,
            "normalized": norm,
            "categories": classify(cleaned + " " + heading),
        })
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=".source_cache/system_prompts_leaks")
    ap.add_argument("--out", default="sources/rule_candidates.json")
    args = ap.parse_args()

    root = Path(args.source).resolve()
    output = Path(args.out).resolve()
    if not root.exists():
        raise SystemExit("Source cache not found. Run scripts/sync_sources.py first.")

    all_rows = []
    for p in sorted(root.rglob("*.md")):
        if ".git" in p.parts:
            continue
        rel = p.relative_to(root).as_posix()
        provider = rel.split("/", 1)[0] if "/" in rel else "root"
        all_rows.extend(candidates_from_file(p, provider, rel))

    # Exact normalized dedupe while retaining provenance.
    grouped = {}
    for row in all_rows:
        key = hashlib.sha256(row["normalized"].lower().encode()).hexdigest()
        if key not in grouped:
            grouped[key] = {
                "id": key[:16],
                "normalized": row["normalized"],
                "categories": set(row["categories"]),
                "occurrences": [],
            }
        grouped[key]["categories"].update(row["categories"])
        grouped[key]["occurrences"].append({
            k: row[k] for k in ("provider", "path", "line", "heading", "text")
        })

    rules = []
    for item in grouped.values():
        item["categories"] = sorted(item["categories"])
        item["provider_count"] = len({x["provider"] for x in item["occurrences"]})
        item["occurrence_count"] = len(item["occurrences"])
        rules.append(item)

    rules.sort(key=lambda x: (-x["provider_count"], -x["occurrence_count"], x["normalized"].lower()))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "source": str(root),
        "raw_candidates": len(all_rows),
        "deduped_rules": len(rules),
        "rules": rules,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Extracted {len(all_rows)} candidates -> {len(rules)} deduped rules -> {output}")

if __name__ == "__main__":
    main()
