#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

root = Path(__file__).resolve().parents[1]

def run(script):
    subprocess.run([sys.executable, str(root/"scripts"/script)], cwd=root, check=True)

for script in ("sync_sources.py", "index_sources.py", "extract_rules.py", "build_fusion_layer.py"):
    run(script)

print("JANEF ONE source corpus synchronized, indexed, and fused into candidate rules.")
