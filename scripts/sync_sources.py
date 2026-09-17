#!/usr/bin/env python3
from pathlib import Path
import argparse
import subprocess
import sys

DEFAULT_REPO = "https://github.com/asgeirtj/system_prompts_leaks.git"

def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--dest", default=".source_cache/system_prompts_leaks")
    ap.add_argument("--ref", default="main")
    args = ap.parse_args()

    dest = Path(args.dest).resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)

    if (dest / ".git").exists():
        run(["git", "fetch", "--depth", "1", "origin", args.ref], cwd=dest)
        run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=dest)
    else:
        run(["git", "clone", "--depth", "1", "--branch", args.ref, args.repo, str(dest)])

    print(dest)

if __name__ == "__main__":
    main()
