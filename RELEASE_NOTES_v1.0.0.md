# JANEF ONE v1.0.0 — One kernel. Every agent.

JANEF ONE is the first stable release of AL-JANEF's portable agent orchestration kernel.

### Highlights

- master Agent Skill with progressive disclosure;
- deterministic instruction precedence and intent routing;
- persistent state and tamper-evident event journal;
- WorkGraph dependency execution with verification gates;
- context budgeting and recovery primitives;
- bounded multi-agent scheduling;
- static Skill Firewall and subordinate-skill scoring;
- fail-closed authorization for consequential actions;
- evidence ledger for completion claims;
- deterministic benchmark and regression harness;
- adapters for Claude, Codex, Gemini CLI, Cursor, OpenCode, and generic runtimes;
- reproducible release packaging and clean-install validation.

### Release quality

Run `python3 scripts/quality_gate.py` to reproduce the repository's release gates locally. The release is considered `10/10` only when every defined gate passes.

### Security

Third-party skills and prompt corpora are treated as untrusted inputs. External prompt snapshots are not bundled in this release. See `SECURITY.md` and `NOTICE`.
