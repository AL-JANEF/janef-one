from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .state import StateStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class Checkpoint:
    checkpoint_id: str
    created_at: str
    phase: str
    payload: dict[str, Any]


class RecoveryManager:
    """Durable checkpoints stored through StateStore's atomic/journaled writes."""

    INDEX_KEY = "recovery.checkpoints"

    def __init__(self, store: StateStore, *, max_checkpoints: int = 20) -> None:
        if max_checkpoints < 1:
            raise ValueError("max_checkpoints must be >= 1")
        self.store = store
        self.max_checkpoints = max_checkpoints

    def checkpoint(self, checkpoint_id: str, phase: str, payload: dict[str, Any]) -> Checkpoint:
        if not checkpoint_id or not phase:
            raise ValueError("checkpoint_id and phase are required")
        item = Checkpoint(checkpoint_id, _now(), phase, payload)
        rows = list(self.store.get(self.INDEX_KEY, []))
        rows = [row for row in rows if row.get("checkpoint_id") != checkpoint_id]
        rows.append({
            "checkpoint_id": item.checkpoint_id,
            "created_at": item.created_at,
            "phase": item.phase,
            "payload": item.payload,
        })
        rows = rows[-self.max_checkpoints :]
        self.store.set(self.INDEX_KEY, rows, event_type="recovery.checkpoint")
        return item

    def latest(self) -> Checkpoint | None:
        rows = self.store.get(self.INDEX_KEY, [])
        if not rows:
            return None
        row = rows[-1]
        return Checkpoint(**row)

    def restore(self, checkpoint_id: str) -> Checkpoint | None:
        rows = self.store.get(self.INDEX_KEY, [])
        for row in reversed(rows):
            if row.get("checkpoint_id") == checkpoint_id:
                return Checkpoint(**row)
        return None
