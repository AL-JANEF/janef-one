# JANEF ONE v1.0.1 — Security Hardening

Security-hardening release for the Skill Firewall trust boundary and the release/CI integrity chain. No new features, no architectural changes.

### Skill Firewall trust boundary

- **Allowlist trust-boundary enforcement**: the reviewed-exception allowlist is now only ever honored from a path a trusted caller explicitly supplies. `scan()` fails closed with a critical `allowlist.untrusted-source` finding if the configured allowlist resolves to the scanned candidate root, or anywhere underneath it (symlinks and path traversal included).
- **Candidate self-approval prevention**: nothing inside a scanned package can cause its own findings to be approved — the allowlist location is never auto-discovered from the candidate root.
- **Fixture/test executable-surface scanning**: `tests`, `test`, `evals`, and `fixtures` directories are no longer excluded from scanning outright. Only a narrow set of passive, non-executable-surface rule codes are relaxed there; executable and script/config surfaces inside those directories are always scanned in full.
- **Path-spoof exemption removal**: the prior path-based exemption for the firewall's own `RULES` declaration region was removed in favor of full scanning.
- **Extensionless shebang scanning**: scripts without a recognized file extension are now scanned as executable surfaces when their content starts with a shebang, instead of being treated as opaque binaries.
- **Deterministic basic obfuscation normalization**: simple, deterministic shell obfuscation (`$IFS` whitespace substitution, quote-split string concatenation) is normalized before rule matching on executable surfaces.
- **Adversarial firewall tests**: expanded test coverage exercising the above (self-approval, fixture scanning, shebang detection, obfuscation normalization) with adversarial fixtures.

### Release and CI integrity

- **Mechanically derived quality-gate evidence**: `scripts/quality_gate.py` now records each gate's pass/fail as it actually executes rather than reporting a fixed `10/10`; the report score and status are derived from what ran.
- **Canonical version validation**: `scripts/validate.py` now checks `manifest.json`'s version against a strict `X.Y.Z` format and verifies `pyproject.toml` and `runtime/janef_one/__init__.py` are not drifted from it, plus that release notes exist for the current version.
- **GitHub Actions SHA pinning**: `actions/checkout`, `actions/setup-python`, and `github/codeql-action/*` are pinned to exact commit SHAs (with version comments) instead of floating tags.
- **Exact-revision CI + CodeQL release gating**: `ci.yml` and `codeql.yml` are now reusable via `workflow_call`. `release.yml` invokes both as jobs against the exact tag SHA and gates publish on `needs: [ci, codeql]`, removing the previous direct-publish-on-tag path.
- **Safer publication staging**: `scripts/publish_github.sh` refuses to run a blind `git add .`; it fails closed if any untracked, non-ignored path is present so nothing unexpected is silently staged for publication.
- **Authorization trust-boundary documentation**: `modules/18-skill-firewall.md` and `modules/24-authorization-gate.md` now document that reviewed-exception approval and `explicit_authorization`/`target_verified` are trusted host/operator inputs, never claims a skill, document, or candidate package can make about itself.

### Scope note

The Skill Firewall remains a static, deterministic pattern and structure scanner over an Agent Skill package. This release hardens its trust boundaries and detection coverage; it does not turn it into a runtime malware sandbox, and static scanning remains a gate rather than proof of safety.

### Release quality

Run `python3 scripts/quality_gate.py` to reproduce the repository's release gates locally.

### Security

Third-party skills and prompt corpora are treated as untrusted inputs. External prompt snapshots are not bundled in this release. See `SECURITY.md` and `NOTICE`.
