# Contributing to JANEF ONE

Contributions should improve correctness, security, portability, measurable capability, recovery, context efficiency, or developer experience.

## Development setup

```bash
git clone https://github.com/AL-JANEF/janef-one.git
cd janef-one
python3 -m pip install -e '.[dev]'
```

## Required checks

For normal changes:

```bash
python3 scripts/validate.py
python3 scripts/test_runtime.py
python3 scripts/benchmark_runtime.py
```

For runtime, security, release, packaging, or architecture changes:

```bash
python3 scripts/quality_gate.py
```

A change must not weaken a gate just to make the build pass.

## Core-module promotion

A rule or workflow enters the canonical core only when it is portable, compatible with higher-priority host policy, operationally useful, non-duplicative, testable or verifiable, independent of stale provider identity/tool assumptions, and documented with provenance when derived from external research.

Do not wholesale-copy third-party system prompts into canonical modules. Prefer normalized behavioral principles and original implementation.

## Pull requests

Keep changes focused. Include the problem, the smallest complete implementation, verification evidence, and security impact when relevant. Preserve unrelated behavior and avoid new dependencies unless they materially improve correctness or safety.
