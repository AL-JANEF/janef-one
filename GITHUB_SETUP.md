# GitHub launch setup

JANEF ONE is prepared for `AL-JANEF/janef-one`.

## One-command publication

From the repository root on macOS/Linux:

```bash
bash scripts/publish_github.sh --execute
```

The script is PEP 668-safe: it creates and uses `.venv` automatically and never installs into the Homebrew/system Python environment.

It then runs the full release quality gate, builds the source ZIP and Python wheel, verifies SHA-256 integrity, creates or reuses the public GitHub repository, configures discovery topics, pushes `main`, publishes the version tag, and creates/updates the GitHub Release with all required release artifacts.

## Release assets

Each release carries:

- `janef-one-vX.Y.Z.zip`
- `janef-one-vX.Y.Z.zip.sha256`
- `janef-one-vX.Y.Z-quality.json`
- `janef_one_runtime-X.Y.Z-py3-none-any.whl`

## Repository branding

The repository includes:

- `assets/al-janef-logo.svg` — scalable SVG container preserving the supplied master logo exactly.
- `assets/al-janef-logo.png` — supplied master raster artwork.
- `assets/social-preview.svg` — scalable social/marketing artwork.
- `assets/social-preview.png` — GitHub-ready 1280×640 social preview.

GitHub currently requires the social preview image to be selected through the repository UI. After publication open:

**Settings → General → Social preview → Edit → Upload `assets/social-preview.png`**

## Recommended repository settings

- Visibility: Public
- Default branch: `main`
- Issues: Enabled
- Require CI before merge once branch protection/rulesets are configured
- Keep release tags immutable

## Suggested description

> One kernel. Every agent. A hardened Agent Skill + runtime for routing, state, WorkGraphs, skill security, authorization, evidence, and reproducible agent orchestration.

## Topics

`ai-agents`, `agent-skills`, `agent-orchestration`, `multi-agent`, `workgraph`, `security`, `python`, `claude-code`, `codex`
