# Changelog

## 1.0.1 — 2026-09-19

- Skill Firewall: allowlist trust-boundary enforcement, fails closed if the configured allowlist resolves inside the scanned candidate root.
- Skill Firewall: prevented candidates from approving their own findings via an in-package allowlist.
- Skill Firewall: scan `tests`/`test`/`evals`/`fixtures` executable surfaces in full; only narrow passive rule codes are relaxed there.
- Skill Firewall: removed the path-based exemption for the scanner's own rule-declaration region.
- Skill Firewall: scan extensionless scripts with a shebang as executable surfaces.
- Skill Firewall: normalize deterministic basic shell obfuscation (`$IFS`, quote-split concatenation) before rule matching.
- Added adversarial Skill Firewall tests for the above.
- `scripts/quality_gate.py` now derives its PASS/FAIL score mechanically from gates that actually ran, instead of reporting a fixed score.
- `scripts/validate.py` now validates `manifest.json`'s version format and checks `pyproject.toml`/`runtime/janef_one/__init__.py` for version drift.
- Pinned GitHub Actions to exact commit SHAs.
- `release.yml` now gates publish on exact-tag-SHA CI and CodeQL runs (`workflow_call`) instead of a direct-publish-on-tag path.
- `scripts/publish_github.sh` refuses to stage untracked, non-ignored paths.
- Documented that reviewed-exception approval and `explicit_authorization`/`target_verified` are trusted host inputs, not skill/candidate claims.

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
