from __future__ import annotations

from dataclasses import dataclass

from .firewall import SkillScanResult


@dataclass(frozen=True, slots=True)
class SkillScore:
    safety: int
    unique_capability: int
    context_efficiency: int
    benchmark_gain: int
    overlap_penalty: int
    total: int
    decision: str


def score_skill(
    scan: SkillScanResult,
    *,
    unique_capability: int,
    context_efficiency: int,
    benchmark_gain: int = 50,
    overlap: int = 50,
) -> SkillScore:
    for name, value in (
        ("unique_capability", unique_capability),
        ("context_efficiency", context_efficiency),
        ("benchmark_gain", benchmark_gain),
        ("overlap", overlap),
    ):
        if not 0 <= value <= 100:
            raise ValueError(f"{name} must be between 0 and 100")

    safety = scan.score
    total = round(
        safety * 0.35
        + unique_capability * 0.25
        + context_efficiency * 0.15
        + benchmark_gain * 0.20
        + (100 - overlap) * 0.05
    )
    if scan.decision == "block":
        decision = "reject"
    elif total >= 80 and unique_capability >= 60:
        decision = "subordinate"
    elif total >= 60:
        decision = "review"
    else:
        decision = "reject"
    return SkillScore(safety, unique_capability, context_efficiency, benchmark_gain, overlap, total, decision)
