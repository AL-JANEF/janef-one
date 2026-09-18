# JANEF ONE — Quick Demo

This demo uses the repository runtime directly. No global Python installation changes are required.

## 1. Intent routing

```bash
PYTHONPATH=runtime python3 -m janef_one route "Research the latest framework release"
```

Expected shape:

```json
{
  "primary": "research",
  "modules": ["research-engine", "source-trust", "critic-verifier"],
  "needs_freshness": true,
  "needs_authorization_gate": false
}
```

## 2. Skill security gate

```bash
PYTHONPATH=runtime python3 -m janef_one scan-skill .
```

The scanner reports a score, decision, and findings. JANEF ONE's own v1.0.1 release self-scan is required to reach `100/100` with `allow` before release.

## 3. Persistent state integrity

```bash
PYTHONPATH=runtime python3 -m janef_one state ./.janef-one-state verify
```

State uses a tamper-evident event journal and recovery checks.

## 4. Full repository gate

```bash
python3 scripts/quality_gate.py
```

This executes the repository's validation, tests, coverage threshold, deterministic benchmark, compilation, self-firewall, clean wheel installation, CLI smoke checks, and reproducible packaging gates.

## What to explore next

- `SKILL.md` — the compact Agent Skills entry point.
- `SYSTEM_CORE.md` — the portable execution contract.
- `modules/` — progressively disclosed orchestration modules.
- `examples/workgraph.json` — WorkGraph example.
- `references/SECURITY_MODEL.md` — security boundaries.
