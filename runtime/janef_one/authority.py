from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable


class AuthorityLevel(IntEnum):
    """Lower numeric values have higher authority."""

    PLATFORM = 10
    DEVELOPER = 20
    USER = 30
    PROJECT = 40
    KERNEL = 50
    SUBORDINATE_SKILL = 60
    DEFAULT = 70


@dataclass(frozen=True, slots=True)
class Instruction:
    text: str
    authority: AuthorityLevel
    topic: str
    source: str = ""
    ordinal: int = 0

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("instruction text is required")
        if not self.topic.strip():
            raise ValueError("instruction topic is required")
        if self.ordinal < 0:
            raise ValueError("instruction ordinal must be >= 0")


@dataclass(frozen=True, slots=True)
class Resolution:
    winners: tuple[Instruction, ...]
    shadowed: tuple[Instruction, ...]
    ambiguous: tuple[tuple[Instruction, Instruction], ...] = ()


def _topic(value: str) -> str:
    return " ".join(value.casefold().split())


def resolve_instructions(instructions: Iterable[Instruction]) -> Resolution:
    """Resolve instructions deterministically per declared topic.

    Highest authority wins. At equal authority, the larger ordinal (newer
    instruction) wins. Equal authority+ordinal with differing text is exposed
    as ambiguity rather than silently hidden; a stable source/text tie-breaker
    still produces a deterministic winner for callers that need one.
    """

    best: dict[str, Instruction] = {}
    shadowed: list[Instruction] = []
    ambiguous: list[tuple[Instruction, Instruction]] = []
    for item in instructions:
        topic = _topic(item.topic)
        current = best.get(topic)
        if current is None:
            best[topic] = item
            continue
        incoming_rank = (int(item.authority), -item.ordinal)
        current_rank = (int(current.authority), -current.ordinal)
        if incoming_rank < current_rank:
            shadowed.append(current)
            best[topic] = item
        elif incoming_rank > current_rank:
            shadowed.append(item)
        else:
            if item.text != current.text:
                ambiguous.append((current, item))
            winner = min((current, item), key=lambda x: (x.source, x.text))
            loser = item if winner is current else current
            best[topic] = winner
            shadowed.append(loser)

    winners = tuple(sorted(best.values(), key=lambda i: (int(i.authority), _topic(i.topic), -i.ordinal, i.source)))
    return Resolution(winners=winners, shadowed=tuple(shadowed), ambiguous=tuple(ambiguous))
