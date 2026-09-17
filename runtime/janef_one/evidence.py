from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    sequence: int
    claim: str
    evidence_type: str
    source: str
    observed: bool
    detail: Any
    timestamp: str
    previous_hash: str
    digest: str


class EvidenceIntegrityError(RuntimeError):
    pass


class EvidenceLedger:
    """Append-only, hash-chained ledger for evidence-backed completion claims."""

    ZERO_HASH = "0" * 64

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self._records: list[EvidenceRecord] = []
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists():
                self._load()

    def _load(self) -> None:
        assert self.path is not None
        rows: list[EvidenceRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_no, raw in enumerate(handle, start=1):
                if not raw.strip():
                    continue
                try:
                    row = json.loads(raw)
                    rows.append(EvidenceRecord(**row))
                except (json.JSONDecodeError, TypeError) as exc:
                    raise EvidenceIntegrityError(f"invalid evidence record at line {line_no}: {exc}") from exc
        self._records = rows
        ok, detail = self.verify()
        if not ok:
            raise EvidenceIntegrityError(detail)

    def _persist(self, record: EvidenceRecord) -> None:
        if self.path is None:
            return
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def add(self, claim: str, *, evidence_type: str, source: str, observed: bool, detail: Any) -> EvidenceRecord:
        if not claim.strip() or not evidence_type.strip() or not source.strip():
            raise ValueError("claim, evidence_type, and source are required")
        # Fail before mutation if detail is not serializable.
        json.dumps(detail, ensure_ascii=False)
        previous_hash = self._records[-1].digest if self._records else self.ZERO_HASH
        body = {
            "sequence": len(self._records) + 1,
            "claim": claim,
            "evidence_type": evidence_type,
            "source": source,
            "observed": observed,
            "detail": detail,
            "timestamp": _now(),
            "previous_hash": previous_hash,
        }
        record = EvidenceRecord(**body, digest=_digest(body))
        self._persist(record)
        self._records.append(record)
        return record

    def records(self, claim: str | None = None) -> tuple[EvidenceRecord, ...]:
        rows: Iterable[EvidenceRecord] = self._records
        if claim is not None:
            rows = (row for row in rows if row.claim == claim)
        return tuple(rows)

    def verify(self) -> tuple[bool, str]:
        previous_hash = self.ZERO_HASH
        for expected_sequence, record in enumerate(self._records, start=1):
            if record.sequence != expected_sequence:
                return False, f"sequence mismatch at record {expected_sequence}"
            if record.previous_hash != previous_hash:
                return False, f"hash-chain mismatch at record {expected_sequence}"
            body = {
                "sequence": record.sequence,
                "claim": record.claim,
                "evidence_type": record.evidence_type,
                "source": record.source,
                "observed": record.observed,
                "detail": record.detail,
                "timestamp": record.timestamp,
                "previous_hash": record.previous_hash,
            }
            expected = _digest(body)
            if record.digest != expected:
                return False, f"digest mismatch at record {expected_sequence}"
            previous_hash = expected
        return True, "ok"

    def supporting_records(
        self,
        claim: str,
        *,
        accepted_types: set[str] | None = None,
        accepted_sources: set[str] | None = None,
    ) -> tuple[EvidenceRecord, ...]:
        rows: list[EvidenceRecord] = []
        for record in self._records:
            if record.claim != claim or not record.observed:
                continue
            if accepted_types is not None and record.evidence_type not in accepted_types:
                continue
            if accepted_sources is not None and record.source not in accepted_sources:
                continue
            rows.append(record)
        return tuple(rows)

    def is_supported(
        self,
        claim: str,
        *,
        accepted_types: set[str] | None = None,
        accepted_sources: set[str] | None = None,
        min_records: int = 1,
    ) -> bool:
        if min_records < 1:
            raise ValueError("min_records must be >= 1")
        return len(
            self.supporting_records(
                claim,
                accepted_types=accepted_types,
                accepted_sources=accepted_sources,
            )
        ) >= min_records

    def require(
        self,
        claim: str,
        *,
        accepted_types: set[str] | None = None,
        accepted_sources: set[str] | None = None,
        min_records: int = 1,
    ) -> None:
        ok, detail = self.verify()
        if not ok:
            raise EvidenceIntegrityError(detail)
        if not self.is_supported(
            claim,
            accepted_types=accepted_types,
            accepted_sources=accepted_sources,
            min_records=min_records,
        ):
            raise RuntimeError(f"completion claim lacks sufficient observed evidence: {claim}")
