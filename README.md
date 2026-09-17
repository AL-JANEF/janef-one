<p align="center">
  <img src="./assets/al-janef-logo.png" alt="AL-JANEF" width="430">
</p>

<h1 align="center">JANEF ONE</h1>
<p align="center"><strong>One kernel. Every agent.</strong></p>
<p align="center">
  A portable Agent Skill and hardened Python runtime for routing, state, WorkGraphs, skill security, multi-agent planning, authorization, evidence, and reproducible verification.
</p>

<p align="center"><a href="./README_AR.md">العربية</a> · <a href="./README.md">English</a></p>

<p align="center">
  <a href="https://github.com/AL-JANEF/janef-one/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/AL-JANEF/janef-one/ci.yml?branch=main&label=quality%20gate"></a>
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-0b2748"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-00bcbc">
  <img alt="Agent Skills" src="https://img.shields.io/badge/Agent%20Skills-compatible-0b2748">
  <img alt="Version" src="https://img.shields.io/badge/version-1.0.0-00bcbc">
</p>

## What JANEF ONE is

JANEF ONE is a **master orchestration layer** for agentic work. Instead of stacking dozens of generic skills into the context window, it keeps one small kernel in control and loads specialized capabilities only when they add unique value.

```text
USER / PROJECT INTENT
        │
        ▼
┌──────────────────────────┐
│        JANEF ONE         │
│  resolve • route • gate  │
└────────────┬─────────────┘
             │
   ┌─────────┼─────────┐
   ▼         ▼         ▼
Research   Coding    Tools / Files / Browser
   │         │         │
   └─────────┼─────────┘
             ▼
       WorkGraph / Agents
             ▼
      Critic + Verifier
             ▼
     Evidence-backed result
```

JANEF ONE does **not** override a host model's system instructions, safety controls, permissions, or actual tool availability. It operates at the user/project orchestration layer.

## Why it exists

Agent ecosystems are getting larger, but more skills do not automatically produce better agents. Overlapping instructions increase context cost, routing errors, authority conflicts, and false completion claims. JANEF ONE addresses that with a single orchestration contract:

**UNDERSTAND → RESOLVE → ROUTE → GATHER → EXECUTE → VERIFY → REPORT**

A subordinate skill is loaded only when it contributes domain knowledge, a required format, or a capability contract not already covered by the kernel.

## v1.0 capabilities

| Capability | What it provides |
|---|---|
| Instruction Resolver | deterministic precedence and ambiguity exposure |
| Capability Registry | runtime-aware capability discovery and conflict detection |
| Context Governor | budgeted, deduplicated context selection |
| Persistent State | atomic JSON state with a tamper-evident event journal |
| WorkGraph | dependency-aware DAG execution, retries, verification gates |
| Recovery Manager | checkpoint and failure recovery primitives |
| Multi-Agent Scheduler | bounded, dependency-aware delegation planning |
| Skill Firewall | static pre-load scanning with allow/review/block outcomes |
| Skill Rating | value/overlap/risk scoring for subordinate skills |
| Authorization Gate | fail-closed handling of consequential side effects |
| Evidence Ledger | evidence-backed completion and integrity records |
| Benchmark Harness | deterministic regression and release checks |

## Quick start

### Use it as an Agent Skill

Clone the repository and place the `janef-one` directory in the Agent Skills location supported by your host runtime, or reference `SKILL.md` at project level.

```bash
git clone https://github.com/AL-JANEF/janef-one.git
cd janef-one
python3 scripts/validate.py
```

### Use the optional runtime

```bash
python3 -m pip install -e .
janef-one --version
janef-one route "Research the latest framework release"
janef-one scan-skill ./path/to/a/skill
janef-one state ./.janef-one-state verify
```

Without installing:

```bash
PYTHONPATH=runtime python3 -m janef_one route "Review this repository for release readiness"
```

## Quality gate

The release gate is executable and reproducible:

```bash
python3 scripts/quality_gate.py
```

It enforces package/spec validation, unit and integration tests, ≥90% runtime coverage, deterministic runtime benchmarks, syntax compilation, a self-firewall scan, clean-wheel installation, CLI smoke tests, and reproducible release packaging.

`10/10` in this repository means **all defined release gates pass**. It is not a claim that no competing agent framework can ever outperform JANEF ONE on every workload.

## v1.0 release evidence

The current release gate records:

- **102/102** unit and integration tests passing;
- **1,970/1,970** deterministic runtime benchmark checks passing;
- **90.03%** measured runtime coverage;
- **100/100** self-firewall score with an `allow` decision;
- clean-wheel installation and CLI smoke tests passing;
- reproducible ZIP packaging with identical SHA-256 on repeat builds.

These numbers describe the repository's deterministic release checks; they do not replace model-level A/B evaluation on real workloads.

## Repository layout

```text
SKILL.md                  Agent Skills entry point
SYSTEM_CORE.md            portable operating kernel
modules/                  progressively loaded orchestration modules
references/               architecture, security, benchmark references
runtime/janef_one/        optional Python runtime primitives
scripts/                  validation, benchmark, release and corpus utilities
tests/                    deterministic runtime tests
evals/                    behavioral seed cases
adapters/                 Claude, Codex, Gemini CLI, Cursor, OpenCode notes
providers/                provider-pattern research notes
assets/                   project identity assets
.github/                  CI, issue forms, PR template, Dependabot
```

## Source-fusion research

JANEF ONE can optionally analyze a configured prompt-snapshot corpus as **research input**, not as runtime authority. The public release does not bundle third-party prompt corpora.

```bash
python3 scripts/update_all.py
```

The pipeline synchronizes sources, indexes them, extracts candidate operating rules, deduplicates candidates, and produces a fusion report. Provider-specific identity, stale tool contracts, hidden policy, or conflicting behavior is not promoted automatically.

See [`SOURCE-MATRIX.md`](./SOURCE-MATRIX.md) and [`NOTICE`](./NOTICE).

## Security model

External skills and retrieved prompt material are untrusted by default. The bundled firewall is a deterministic static gate, not a malware sandbox. Real deployments should combine provenance checks, sandboxing, least privilege, explicit authorization for consequential actions, and post-action verification.

See [`SECURITY.md`](./SECURITY.md) and [`references/SECURITY_MODEL.md`](./references/SECURITY_MODEL.md).

## Supported agent environments

JANEF ONE is designed to be portable. The repository includes deployment notes for Claude Chat, Claude Code, Codex, Gemini CLI, Cursor, OpenCode, and generic Agent Skills-compatible runtimes. Live host instructions and tool schemas always take precedence over snapshot assumptions.

## Contributing

Read [`CONTRIBUTING.md`](./CONTRIBUTING.md). Changes that weaken verification, authority boundaries, security gates, or release reproducibility are rejected even if they make a benchmark easier to pass.

## License

Apache License 2.0. See [`LICENSE`](./LICENSE) and [`NOTICE`](./NOTICE).

<p align="center"><strong>Built by AL-JANEF · CODE • CREATE • BUILD</strong></p>
