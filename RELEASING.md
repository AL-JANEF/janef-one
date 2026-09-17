# Releasing JANEF ONE

## Pre-release gate

```bash
PYTHONPATH=runtime python3 scripts/release_check.py
```

A release is blocked by validation/test failure or a critical self-firewall finding.

## Package

```bash
python3 scripts/package_release.py
```

The package excludes the external prompt source cache, generated candidate catalogs, bytecode, local state, and Git internals.

## GitHub publication checklist

1. Create the repository with the intended owner and visibility.
2. Push the validated source tree; do not push `.source_cache/`.
3. Enable branch protection for the default branch.
4. Require the `CI / validate-and-test` status checks.
5. Enable private vulnerability reporting / GitHub Security Advisories.
6. Review repository topics, description, and license display.
7. Create a version tag only after CI passes on the exact commit.
8. Attach the release ZIP generated from that commit.
9. Publish benchmark claims only when the referenced benchmark artifacts are included or linked.

Do not publish external prompt corpora inside JANEF ONE releases.
