#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

REPO="AL-JANEF/janef-one"
DESC="One kernel. Every agent. A hardened Agent Skill + runtime for routing, state, WorkGraphs, skill security, authorization, evidence, and reproducible agent orchestration."
VERSION="$(python3 -c 'import json; print(json.load(open("manifest.json"))["version"])')"
TAG="v${VERSION}"
VENV="${ROOT}/.venv"
PY="${VENV}/bin/python"
PIP="${VENV}/bin/pip"
PARENT="$(dirname "$ROOT")"
DIST_DIR="${PARENT}/janef-one-dist"
ZIP="${PARENT}/janef-one-v${VERSION}.zip"
SHA="${ZIP}.sha256"
QUALITY="${PARENT}/janef-one-v${VERSION}-quality.json"
WHEEL_GLOB="${DIST_DIR}/janef_one_runtime-${VERSION}-py3-none-any.whl"

if [[ "${1:-}" != "--execute" ]]; then
  cat <<MSG
Dry-run only. JANEF ONE will be published to:
  https://github.com/${REPO}

The execute path will:
  1. create/use an isolated Python virtual environment
  2. install release tooling locally
  3. run the full 10/10 quality gate
  4. build the runtime wheel and reproducible source archive
  5. create/update the GitHub repository metadata
  6. push main and tag ${TAG}
  7. create/update the GitHub Release with ZIP, SHA-256, quality report, and wheel

Execute with:
  bash scripts/publish_github.sh --execute
MSG
  exit 0
fi

command -v git >/dev/null || { echo "git is required" >&2; exit 1; }
command -v gh >/dev/null || { echo "GitHub CLI (gh) is required" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }

gh auth status

# PEP 668-safe installation: never modify Homebrew/system Python.
if [[ ! -x "$PY" ]]; then
  echo "==> creating isolated virtual environment"
  python3 -m venv "$VENV"
fi

echo "==> installing JANEF ONE release tooling in .venv"
"$PY" -m pip install --upgrade pip setuptools >/dev/null
"$PY" -m pip install -e '.[dev]' >/dev/null

echo "==> full quality gate"
"$PY" scripts/quality_gate.py

echo "==> build release wheel"
mkdir -p "$DIST_DIR"
# Remove only JANEF ONE wheel artifacts from the dedicated release directory.
find "$DIST_DIR" -maxdepth 1 -type f -name 'janef_one_runtime-*.whl' -delete
"$PY" -m pip wheel . --no-deps --no-build-isolation -w "$DIST_DIR" >/dev/null

[[ -f "$ZIP" ]] || { echo "missing release archive: $ZIP" >&2; exit 1; }
[[ -f "$SHA" ]] || { echo "missing SHA-256 file: $SHA" >&2; exit 1; }
[[ -f "$QUALITY" ]] || { echo "missing quality report: $QUALITY" >&2; exit 1; }
WHEEL="$(find "$DIST_DIR" -maxdepth 1 -type f -name "janef_one_runtime-${VERSION}-*.whl" -print -quit)"
[[ -n "$WHEEL" && -f "$WHEEL" ]] || { echo "missing runtime wheel" >&2; exit 1; }

# Validate the SHA file before publication.
EXPECTED="$(awk '{print $1}' "$SHA")"
ACTUAL="$(shasum -a 256 "$ZIP" | awk '{print $1}')"
[[ "$EXPECTED" == "$ACTUAL" ]] || { echo "SHA-256 mismatch before publication" >&2; exit 1; }

echo "==> initialize repository"
if [[ ! -d .git ]]; then
  git init -b main
fi

git add .
if ! git diff --cached --quiet; then
  git commit -m "feat: launch JANEF ONE v${VERSION}"
fi

if gh repo view "$REPO" >/dev/null 2>&1; then
  echo "Repository already exists: $REPO"
else
  gh repo create "$REPO" --public --description "$DESC" --source=. --remote=origin
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "https://github.com/${REPO}.git"
fi

# Make repository presentation deterministic and discoverable.
gh repo edit "$REPO" \
  --description "$DESC" \
  --enable-issues=true \
  --add-topic ai-agents \
  --add-topic agent-skills \
  --add-topic agent-orchestration \
  --add-topic multi-agent \
  --add-topic workgraph \
  --add-topic security \
  --add-topic python \
  --add-topic claude-code \
  --add-topic codex

echo "==> push main"
git push -u origin main

HEAD_SHA="$(git rev-parse HEAD)"
if git rev-parse "$TAG" >/dev/null 2>&1; then
  TAG_SHA="$(git rev-list -n 1 "$TAG")"
  [[ "$TAG_SHA" == "$HEAD_SHA" ]] || {
    echo "Local tag $TAG already points to a different commit; refusing to rewrite a release tag." >&2
    exit 1
  }
else
  git tag -a "$TAG" -m "JANEF ONE ${TAG}"
fi

REMOTE_TAG="$(git ls-remote origin "refs/tags/${TAG}" | awk '{print $1}')"
if [[ -z "$REMOTE_TAG" ]]; then
  git push origin "$TAG"
else
  echo "Remote tag already exists: $TAG"
fi

echo "==> publish GitHub Release assets"
ASSETS=("$ZIP" "$SHA" "$QUALITY" "$WHEEL")
if gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
  gh release upload "$TAG" "${ASSETS[@]}" --repo "$REPO" --clobber
  gh release edit "$TAG" --repo "$REPO" \
    --title "JANEF ONE ${TAG} — One kernel. Every agent." \
    --notes-file RELEASE_NOTES_v1.0.0.md
else
  gh release create "$TAG" "${ASSETS[@]}" \
    --repo "$REPO" \
    --title "JANEF ONE ${TAG} — One kernel. Every agent." \
    --notes-file RELEASE_NOTES_v1.0.0.md
fi

cat <<MSG

PUBLISHED SUCCESSFULLY
Repository: https://github.com/${REPO}
Release:    https://github.com/${REPO}/releases/tag/${TAG}
SHA-256:   ${ACTUAL}

Manual GitHub UI step remaining:
  Settings -> General -> Social preview -> Upload assets/social-preview.png
MSG
