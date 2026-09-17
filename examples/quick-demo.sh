#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/runtime${PYTHONPATH:+:$PYTHONPATH}"

echo "=== JANEF ONE: routing ==="
python3 -m janef_one route "Research the latest framework release"

echo
echo "=== JANEF ONE: self skill scan ==="
python3 -m janef_one scan-skill .

echo
echo "=== JANEF ONE: package validation ==="
python3 scripts/validate.py
