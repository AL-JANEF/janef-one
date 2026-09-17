from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Iterable


def estimate_tokens(text: str) -> int:
    """Deterministic conservative token estimate for budgeting, not billing."""
    # 3.5 chars/token is intentionally conservative across mixed prose/code.
    return max(1, (len(text) * 2 + 6) // 7)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def _fingerprint(text: str) -> str:
    return hashlib.sha256(_normalize(text).encode("utf-8")).hexdigest()


def _shingles(text: str, size: int = 4) -> set[tuple[str, ...]]:
    words = re.findall(r"\w+", _normalize(text), flags=re.UNICODE)
    if len(words) < size:
        return {tuple(words)} if words else set()
    return {tuple(words[i : i + size]) for i in range(len(words) - size + 1)}


def _near_duplicate(a: str, b: str, threshold: float = 0.90) -> bool:
    sa, sb = _shingles(a), _shingles(b)
    if not sa or not sb:
        return False
    return len(sa & sb) / len(sa | sb) >= threshold


class ContextBudgetError(ValueError):
    """Raised when required context cannot fit the declared context budget."""


@dataclass(frozen=True, slots=True)
class ContextItem:
    id: str
    content: str
    source: str
    relevance: int = 50
    trust: int = 50
    recency: int = 50
    required: bool = False
    authority: int = 0

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("context id is required")
        if not self.source:
            raise ValueError("context source is required")
        for name, value in (
            ("relevance", self.relevance),
            ("trust", self.trust),
            ("recency", self.recency),
            ("authority", self.authority),
        ):
            if not 0 <= value <= 100:
                raise ValueError(f"{name} must be between 0 and 100")

    @property
    def tokens(self) -> int:
        return estimate_tokens(self.content)

    @property
    def utility(self) -> float:
        # Authority is intentionally weak here. Real instruction authority is
        # resolved separately; this only prioritizes already-admitted context.
        return self.relevance * 0.50 + self.trust * 0.25 + self.recency * 0.15 + self.authority * 0.10


@dataclass(frozen=True, slots=True)
class ContextSelection:
    selected: tuple[ContextItem, ...]
    dropped: tuple[ContextItem, ...]
    estimated_tokens: int
    budget_tokens: int
    required_tokens: int

    @property
    def utilization(self) -> float:
        if self.budget_tokens == 0:
            return 1.0 if self.estimated_tokens else 0.0
        return self.estimated_tokens / self.budget_tokens


class ContextGovernor:
    """Select high-value context under a hard deterministic token budget.

    Required context is fail-closed: if it cannot fit, selection raises instead
    of silently dropping it. Exact and near duplicates are removed before
    allocation, preserving the strongest representative.
    """

    def __init__(self, *, near_duplicate_threshold: float = 0.90) -> None:
        if not 0.0 <= near_duplicate_threshold <= 1.0:
            raise ValueError("near_duplicate_threshold must be between 0 and 1")
        self.near_duplicate_threshold = near_duplicate_threshold

    @staticmethod
    def _rank(item: ContextItem) -> tuple[bool, float, int, str]:
        return (item.required, item.utility, -item.tokens, item.id)

    def _deduplicate(self, items: Iterable[ContextItem]) -> tuple[list[ContextItem], list[ContextItem]]:
        exact: dict[str, ContextItem] = {}
        dropped: list[ContextItem] = []
        for item in items:
            fp = _fingerprint(item.content)
            previous = exact.get(fp)
            if previous is None:
                exact[fp] = item
            elif self._rank(item) > self._rank(previous):
                dropped.append(previous)
                exact[fp] = item
            else:
                dropped.append(item)

        retained: list[ContextItem] = []
        for item in sorted(exact.values(), key=lambda x: (-int(x.required), -x.utility, x.id)):
            match_index: int | None = None
            for idx, existing in enumerate(retained):
                if _near_duplicate(item.content, existing.content, self.near_duplicate_threshold):
                    match_index = idx
                    break
            if match_index is None:
                retained.append(item)
                continue
            existing = retained[match_index]
            if self._rank(item) > self._rank(existing):
                dropped.append(existing)
                retained[match_index] = item
            else:
                dropped.append(item)
        return retained, dropped

    def select(
        self,
        items: Iterable[ContextItem],
        *,
        budget_tokens: int,
        allow_required_overflow: bool = False,
    ) -> ContextSelection:
        if budget_tokens < 0:
            raise ValueError("budget_tokens must be >= 0")
        unique, duplicates = self._deduplicate(items)
        required = sorted((x for x in unique if x.required), key=lambda x: (-x.utility, x.id))
        optional = sorted(
            (x for x in unique if not x.required),
            key=lambda x: (-(x.utility / max(1, x.tokens)), -x.utility, x.id),
        )
        required_tokens = sum(item.tokens for item in required)
        if required_tokens > budget_tokens and not allow_required_overflow:
            raise ContextBudgetError(
                f"required context needs {required_tokens} tokens but budget is {budget_tokens}"
            )

        selected: list[ContextItem] = list(required)
        dropped: list[ContextItem] = list(duplicates)
        used = required_tokens
        effective_budget = max(budget_tokens, required_tokens) if allow_required_overflow else budget_tokens
        for item in optional:
            if used + item.tokens <= effective_budget:
                selected.append(item)
                used += item.tokens
            else:
                dropped.append(item)

        return ContextSelection(
            selected=tuple(selected),
            dropped=tuple(dropped),
            estimated_tokens=used,
            budget_tokens=budget_tokens,
            required_tokens=required_tokens,
        )
