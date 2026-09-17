#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
env = os.environ.copy()
env["PYTHONPATH"] = str(ROOT / "runtime") + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
raise SystemExit(subprocess.run(
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"],
    cwd=ROOT,
    env=env,
).returncode)
