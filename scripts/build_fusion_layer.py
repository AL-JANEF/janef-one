#!/usr/bin/env python3
from pathlib import Path
import argparse, json

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="sources/rule_candidates.json")
    ap.add_argument("--out", default="sources/FUSION_CANDIDATES.md")
    ap.add_argument("--limit", type=int, default=80, help="max rules per category")
    args = ap.parse_args()

    data = json.loads(Path(args.rules).read_text(encoding="utf-8"))
    by_cat = {}
    for rule in data["rules"]:
        for cat in rule["categories"]:
            by_cat.setdefault(cat, []).append(rule)

    lines = [
        "# Fusion Candidates",
        "",
        "Generated automatically from the local prompt corpus.",
        "",
        "These are **candidate rules, not authority**. JANEF ONE must resolve conflicts, remove provider-specific assumptions, and verify portability before promoting a candidate into canonical modules.",
        "",
    ]
    for cat in sorted(by_cat):
        lines += [f"## {cat}", ""]
        rows = by_cat[cat][:args.limit]
        for r in rows:
            providers = sorted({o["provider"] for o in r["occurrences"]})
            exemplar = r["occurrences"][0]
            lines.append(
                f"- **{r['provider_count']} provider(s), {r['occurrence_count']} occurrence(s)** — "
                f"{r['normalized']}  \n"
                f"  Sources: {', '.join(providers)}; exemplar `{exemplar['path']}:{exemplar['line']}`"
            )
        lines.append("")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)

if __name__ == "__main__":
    main()
