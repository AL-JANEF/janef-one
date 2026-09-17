from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


class CapabilityConflictError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Capability:
    name: str
    kind: str
    description: str = ""
    provider: str = "local"
    available: bool = True
    risk: int = 0
    quality: int = 50
    priority: int = 50
    cost: int = 50
    tags: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.name or not self.kind:
            raise ValueError("capability name and kind are required")
        for name, value in (
            ("risk", self.risk),
            ("quality", self.quality),
            ("priority", self.priority),
            ("cost", self.cost),
        ):
            if not 0 <= value <= 100:
                raise ValueError(f"{name} must be between 0 and 100")

    @property
    def utility(self) -> float:
        return self.quality * 0.45 + self.priority * 0.30 + (100 - self.risk) * 0.20 + (100 - self.cost) * 0.05


class CapabilityRegistry:
    """Runtime capability registry with explicit collision handling.

    Silent replacement is prohibited because stale or malicious discovery must
    not invisibly change which tool/agent is selected.
    """

    def __init__(self, capabilities: Iterable[Capability] = ()) -> None:
        self._items: dict[str, Capability] = {}
        for capability in capabilities:
            self.register(capability)

    def register(self, capability: Capability, *, replace: bool = False) -> None:
        existing = self._items.get(capability.name)
        if existing is not None and not replace:
            raise CapabilityConflictError(f"capability already registered: {capability.name}")
        self._items[capability.name] = capability

    def unregister(self, name: str) -> Capability | None:
        return self._items.pop(name, None)

    def get(self, name: str) -> Capability | None:
        return self._items.get(name)

    def available(
        self,
        *,
        kind: str | None = None,
        tags: set[str] | None = None,
        max_risk: int = 100,
    ) -> list[Capability]:
        if not 0 <= max_risk <= 100:
            raise ValueError("max_risk must be between 0 and 100")
        result = [item for item in self._items.values() if item.available and item.risk <= max_risk]
        if kind is not None:
            result = [item for item in result if item.kind == kind]
        if tags:
            result = [item for item in result if tags.issubset(item.tags)]
        return sorted(result, key=lambda c: (-c.utility, c.risk, c.cost, c.name))

    def choose(
        self,
        *,
        kind: str,
        required_tags: set[str] | None = None,
        max_risk: int = 100,
    ) -> Capability | None:
        candidates = self.available(kind=kind, tags=required_tags, max_risk=max_risk)
        return candidates[0] if candidates else None

    def snapshot(self) -> list[dict[str, object]]:
        return [
            {
                "name": item.name,
                "kind": item.kind,
                "description": item.description,
                "provider": item.provider,
                "available": item.available,
                "risk": item.risk,
                "quality": item.quality,
                "priority": item.priority,
                "cost": item.cost,
                "utility": round(item.utility, 3),
                "tags": sorted(item.tags),
            }
            for item in sorted(self._items.values(), key=lambda c: c.name)
        ]
