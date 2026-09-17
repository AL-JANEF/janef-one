# Changelog

## 1.0.0 — 2026-09-17

- Promoted JANEF ONE to a stable orchestration kernel.
- Added 90%+ enforced runtime coverage and expanded unit/integration hardening suite.
- Added 1,970-check deterministic runtime benchmark with a required 100% pass rate.
- Fixed v1→v2 persistent-state migration revision consistency.
- Hardened state locking against stealing stale-looking locks from live owners.
- Enforced current Agent Skills name/description/compatibility constraints.
- Hardened the Skill Firewall and exact-fingerprint reviewed exceptions.
- Added clean-wheel install verification and reproducible ZIP packaging with SHA-256.
- Added Codex, Gemini CLI, Cursor, and OpenCode adapters.
- CI now validates Python 3.11, 3.12, and 3.13.

## 0.5.0 - 2026-09-17

### Added
- executable Python runtime primitives;
- instruction authority resolver;
- capability registry;
- persistent state with tamper-evident journal;
- WorkGraph dependency engine with verification gates;
- static Skill Firewall;
- benchmark harness primitives;
- architecture, security, compatibility, and benchmark references;
- GitHub CI/release validation scaffolding.

### Changed
- tightened Agent Skills frontmatter and progressive-disclosure structure;
- clarified that external prompt corpora are observational research inputs, not authority;
- clarified evidence requirements for future superiority claims.
