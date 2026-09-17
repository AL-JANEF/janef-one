from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    id: str
    prompt: str
    assertions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CaseResult:
    id: str
    passed: bool
    passed_assertions: int
    total_assertions: int
    notes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    cases: tuple[CaseResult, ...]

    @property
    def passed(self) -> int:
        return sum(1 for case in self.cases if case.passed)

    @property
    def total(self) -> int:
        return len(self.cases)

    @property
    def assertion_rate(self) -> float:
        denom = sum(case.total_assertions for case in self.cases)
        if denom == 0:
            return 1.0
        return sum(case.passed_assertions for case in self.cases) / denom


def load_cases(path: str | Path) -> list[BenchmarkCase]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    result: list[BenchmarkCase] = []
    for item in raw:
        assertions = item.get("assertions") or item.get("expect") or []
        result.append(BenchmarkCase(id=item["id"], prompt=item["prompt"], assertions=tuple(assertions)))
    return result


def run_cases(
    cases: Iterable[BenchmarkCase],
    executor: Callable[[BenchmarkCase], str],
    judge: Callable[[BenchmarkCase, str, str], tuple[bool, str]],
) -> BenchmarkReport:
    results: list[CaseResult] = []
    for case in cases:
        output = executor(case)
        notes: list[str] = []
        passed_count = 0
        for assertion in case.assertions:
            passed, note = judge(case, output, assertion)
            passed_count += int(passed)
            notes.append(note)
        total = len(case.assertions)
        results.append(CaseResult(case.id, passed_count == total, passed_count, total, tuple(notes)))
    return BenchmarkReport(tuple(results))
