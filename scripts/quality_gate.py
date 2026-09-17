#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = os.environ.copy()
ENV["PYTHONPATH"] = str(ROOT / "runtime")


def run(label: str, cmd: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print(f"==> {label}")
    return subprocess.run(cmd, cwd=cwd, env=env or ENV, check=True, text=True, capture_output=capture)


def check_coverage() -> float:
    run("coverage tests", [sys.executable, "-m", "coverage", "erase"])
    run("coverage run", [sys.executable, "-m", "coverage", "run", "--source=runtime/janef_one", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"])
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as handle:
        report = Path(handle.name)
    try:
        run("coverage json", [sys.executable, "-m", "coverage", "json", "-o", str(report)])
        data = json.loads(report.read_text(encoding="utf-8"))
        pct = float(data["totals"]["percent_covered"])
    finally:
        report.unlink(missing_ok=True)
    if pct < 90.0:
        raise SystemExit(f"coverage gate failed: {pct:.2f}% < 90%")
    print(f"coverage={pct:.2f}%")
    return pct


def clean_install_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        wheel_dir = temp / "wheel"; wheel_dir.mkdir()
        run("build wheel", [sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "--no-build-isolation", "-w", str(wheel_dir)])
        wheels = list(wheel_dir.glob("*.whl"))
        if len(wheels) != 1:
            raise SystemExit("expected exactly one wheel")
        env_dir = temp / "venv"
        venv.EnvBuilder(with_pip=True).create(env_dir)
        py = env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run("install wheel in clean venv", [str(py), "-m", "pip", "install", "--no-deps", str(wheels[0])], env=os.environ.copy())
        run("installed CLI version", [str(py), "-m", "janef_one", "--version"], env=os.environ.copy())
        run("installed CLI route", [str(py), "-m", "janef_one", "route", "research latest agent skills"], env=os.environ.copy())


def reproducible_package() -> str:
    run("package release #1", [sys.executable, "scripts/package_release.py"])
    version = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))["version"]
    archive = ROOT.parent / f"janef-one-v{version}.zip"
    first = hashlib.sha256(archive.read_bytes()).hexdigest()
    run("package release #2", [sys.executable, "scripts/package_release.py"])
    second = hashlib.sha256(archive.read_bytes()).hexdigest()
    if first != second:
        raise SystemExit(f"reproducible package gate failed: {first} != {second}")
    print(f"reproducible_sha256={first}")
    return first


def main() -> int:
    run("package/spec validation", [sys.executable, "scripts/validate.py"])
    run("runtime unit/integration tests", [sys.executable, "scripts/test_runtime.py"])
    coverage = check_coverage()
    run("deterministic runtime benchmark", [sys.executable, "scripts/benchmark_runtime.py"])
    run("syntax compilation", [sys.executable, "-m", "compileall", "-q", "runtime", "scripts", "tests"])

    scan = run("self firewall", [sys.executable, "-m", "janef_one", "scan-skill", "."], capture=True)
    print(scan.stdout.strip())
    payload = json.loads(scan.stdout)
    if payload["decision"] != "allow":
        raise SystemExit(f"self-firewall must be allow for release, got {payload['decision']}")

    clean_install_smoke()
    sha256 = reproducible_package()

    benchmark = json.loads((ROOT / "benchmarks" / "runtime-report.json").read_text(encoding="utf-8"))
    if benchmark["pass_rate"] != 1.0 or benchmark["failed"] != 0:
        raise SystemExit("benchmark gate failed")

    report = {
        "version": json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))["version"],
        "status": "PASS",
        "score": "10/10",
        "gates": {
            "agent_skills_spec": 10,
            "unit_integration_tests": 10,
            "runtime_coverage": 10,
            "deterministic_benchmark": 10,
            "security_self_scan": 10,
            "clean_install": 10,
            "cli_smoke": 10,
            "state_recovery": 10,
            "reproducible_packaging": 10,
            "release_integrity": 10,
        },
        "coverage_percent": round(coverage, 2),
        "benchmark_checks": benchmark["checks"],
        "benchmark_pass_rate": benchmark["pass_rate"],
        "archive_sha256": sha256,
    }
    out = ROOT.parent / f"janef-one-v{report['version']}-quality.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    print("QUALITY GATE: PASS — 10/10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
