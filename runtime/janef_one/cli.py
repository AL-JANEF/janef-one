from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from . import __version__
from .firewall import SkillFirewall
from .router import route_intent
from .state import StateStore


def _cmd_route(args: argparse.Namespace) -> int:
    print(json.dumps(asdict(route_intent(args.text)), ensure_ascii=False, indent=2))
    return 0


def _cmd_scan(args: argparse.Namespace) -> int:
    result = SkillFirewall().scan(args.path)
    payload = {
        "score": result.score,
        "decision": result.decision,
        "findings": [asdict(finding) for finding in result.findings],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 2 if result.decision == "block" else 0


def _cmd_state(args: argparse.Namespace) -> int:
    store = StateStore(args.path)
    if args.action == "verify":
        ok, detail = store.verify_journal()
        print(json.dumps({"ok": ok, "detail": detail}, indent=2))
        return 0 if ok else 3
    print(json.dumps(store.snapshot(), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="janef-one", description="JANEF ONE runtime utilities")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    route = sub.add_parser("route", help="classify a task and show the modules to load")
    route.add_argument("text")
    route.set_defaults(func=_cmd_route)

    scan = sub.add_parser("scan-skill", help="statically scan an Agent Skill package")
    scan.add_argument("path", type=Path)
    scan.set_defaults(func=_cmd_scan)

    state = sub.add_parser("state", help="inspect or verify persistent state")
    state.add_argument("path", type=Path)
    state.add_argument("action", choices=("show", "verify"))
    state.set_defaults(func=_cmd_state)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
