from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class StateEvent:
    sequence: int
    timestamp: str
    event_type: str
    payload: dict[str, Any]
    previous_hash: str
    before_state_hash: str
    after_state_hash: str
    hash: str


class StateCorruptionError(RuntimeError):
    """Raised when durable state or its journal cannot be verified."""


class StateLockTimeout(TimeoutError):
    """Raised when another writer keeps the state lock past the timeout."""


class StateStore:
    """Transactional JSON state with crash recovery and a tamper-evident journal.

    Writes use a lock + write-ahead record + fsync + atomic replace. The journal
    links every mutation to both the previous event and the before/after state
    digests. A pending write is deterministically recovered on the next open.
    """

    SCHEMA_VERSION = 2
    ZERO_HASH = "0" * 64

    def __init__(
        self,
        root: str | Path,
        *,
        lock_timeout: float = 5.0,
        stale_lock_after: float = 60.0,
    ) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.root / "state.json"
        self.journal_path = self.root / "journal.jsonl"
        self.pending_path = self.root / "pending.json"
        self.lock_path = self.root / ".state.lock"
        self.lock_timeout = lock_timeout
        self.stale_lock_after = stale_lock_after
        if lock_timeout < 0 or stale_lock_after <= 0:
            raise ValueError("invalid lock timing configuration")

        if not self.state_path.exists():
            self._atomic_write_state(self._empty_state())
        with self._locked():
            self._migrate_if_needed()
            self._recover_pending_locked()
            ok, detail = self.verify_consistency()
            if not ok:
                raise StateCorruptionError(detail)

    @classmethod
    def _empty_state(cls) -> dict[str, Any]:
        return {
            "schema_version": cls.SCHEMA_VERSION,
            "revision": 0,
            "data": {},
            "last_event_hash": cls.ZERO_HASH,
        }

    @staticmethod
    def _state_body(state: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": int(state["schema_version"]),
            "revision": int(state["revision"]),
            "data": state["data"],
        }

    @classmethod
    def _state_hash(cls, state: dict[str, Any]) -> str:
        return _digest(cls._state_body(state))

    def _read_state_raw(self) -> dict[str, Any]:
        try:
            with self.state_path.open("r", encoding="utf-8") as handle:
                state = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise StateCorruptionError(f"cannot read state: {exc}") from exc
        if not isinstance(state, dict):
            raise StateCorruptionError("state root must be an object")
        return state

    def _read_state(self) -> dict[str, Any]:
        state = self._read_state_raw()
        if state.get("schema_version") != self.SCHEMA_VERSION:
            raise StateCorruptionError("unsupported state schema version")
        if not isinstance(state.get("revision"), int) or state["revision"] < 0:
            raise StateCorruptionError("invalid state revision")
        if not isinstance(state.get("data"), dict):
            raise StateCorruptionError("state data must be an object")
        last = state.get("last_event_hash")
        if not isinstance(last, str) or not _is_sha256(last):
            raise StateCorruptionError("invalid last_event_hash")
        return state

    def _atomic_write_json(self, path: Path, value: object) -> None:
        tmp = path.with_name(path.name + ".tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        self._fsync_directory()

    def _atomic_write_state(self, state: dict[str, Any]) -> None:
        self._atomic_write_json(self.state_path, state)

    def _fsync_directory(self) -> None:
        try:
            fd = os.open(self.root, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(fd)
        except OSError:
            pass
        finally:
            os.close(fd)

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
        return True

    @contextmanager
    def _locked(self) -> Iterator[None]:
        started = time.monotonic()
        token = secrets.token_hex(16)
        owner = {"pid": os.getpid(), "created_at": _utc_now(), "token": token}
        while True:
            try:
                fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(json.dumps(owner, sort_keys=True))
                    handle.flush()
                    os.fsync(handle.fileno())
                break
            except FileExistsError:
                try:
                    stat = self.lock_path.stat()
                    age = time.time() - stat.st_mtime
                    existing = json.loads(self.lock_path.read_text(encoding="utf-8"))
                    existing_pid = int(existing.get("pid", -1)) if isinstance(existing, dict) else -1
                    if age > self.stale_lock_after and not self._pid_alive(existing_pid):
                        self.lock_path.unlink(missing_ok=True)
                        continue
                except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
                    # A malformed lock is removed only after it is stale; never
                    # steal a fresh lock whose owner cannot be established.
                    try:
                        if time.time() - self.lock_path.stat().st_mtime > self.stale_lock_after:
                            self.lock_path.unlink(missing_ok=True)
                            continue
                    except FileNotFoundError:
                        continue
                if time.monotonic() - started >= self.lock_timeout:
                    raise StateLockTimeout(f"timed out waiting for {self.lock_path}")
                time.sleep(0.02)
        try:
            yield
        finally:
            try:
                current = json.loads(self.lock_path.read_text(encoding="utf-8"))
                if isinstance(current, dict) and current.get("token") == token:
                    self.lock_path.unlink(missing_ok=True)
                    self._fsync_directory()
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                pass

    def _journal_events(self) -> list[dict[str, Any]]:
        if not self.journal_path.exists():
            return []
        events: list[dict[str, Any]] = []
        try:
            with self.journal_path.open("r", encoding="utf-8") as handle:
                for line_no, raw in enumerate(handle, start=1):
                    if not raw.strip():
                        continue
                    event = json.loads(raw)
                    if not isinstance(event, dict):
                        raise StateCorruptionError(f"journal line {line_no} is not an object")
                    events.append(event)
        except (OSError, json.JSONDecodeError) as exc:
            raise StateCorruptionError(f"cannot parse journal: {exc}") from exc
        return events

    def _append_event_raw(self, event: dict[str, Any]) -> None:
        with self.journal_path.open("a", encoding="utf-8") as handle:
            handle.write(_canonical_json(event) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self._fsync_directory()

    def _make_event(
        self,
        *,
        sequence: int,
        event_type: str,
        payload: dict[str, Any],
        previous_hash: str,
        before_state_hash: str,
        after_state_hash: str,
    ) -> dict[str, Any]:
        body = {
            "sequence": sequence,
            "timestamp": _utc_now(),
            "event_type": event_type,
            "payload": payload,
            "previous_hash": previous_hash,
            "before_state_hash": before_state_hash,
            "after_state_hash": after_state_hash,
        }
        return {**body, "hash": _digest(body)}

    def _migrate_if_needed(self) -> None:
        raw = self._read_state_raw()
        if raw.get("schema_version") == self.SCHEMA_VERSION:
            return
        if raw.get("schema_version") != 1:
            raise StateCorruptionError("unsupported state schema version")
        if not isinstance(raw.get("revision"), int) or not isinstance(raw.get("data"), dict):
            raise StateCorruptionError("invalid v1 state")

        ok, detail, previous_hash, sequence = self._verify_journal_internal(allow_legacy=True)
        if not ok:
            raise StateCorruptionError(f"cannot migrate invalid v1 journal: {detail}")

        old_revision = int(raw["revision"])
        migrated = {
            "schema_version": self.SCHEMA_VERSION,
            # Migration is itself a durable state transition and therefore
            # consumes the next journal sequence/revision.
            "revision": old_revision + 1,
            "data": raw["data"],
            "last_event_hash": previous_hash,
        }
        if sequence != migrated["revision"]:
            raise StateCorruptionError(
                f"legacy revision/journal mismatch: next sequence {sequence}, expected {migrated['revision']}"
            )
        before_hash = _digest({"schema_version": 1, "revision": old_revision, "data": raw["data"]})
        after_hash = self._state_hash(migrated)
        event = self._make_event(
            sequence=sequence,
            event_type="state.migrate.v1-v2",
            payload={"from": 1, "to": 2, "previous_revision": old_revision},
            previous_hash=previous_hash,
            before_state_hash=before_hash,
            after_state_hash=after_hash,
        )
        migrated["last_event_hash"] = event["hash"]
        self._append_event_raw(event)
        self._atomic_write_state(migrated)

    def _recover_pending_locked(self) -> None:
        if not self.pending_path.exists():
            return
        try:
            pending = json.loads(self.pending_path.read_text(encoding="utf-8"))
            event = pending["event"]
            new_state = pending["new_state"]
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise StateCorruptionError(f"invalid pending transaction: {exc}") from exc

        events = self._journal_events()
        last_hash = events[-1]["hash"] if events else self.ZERO_HASH
        if last_hash == event["previous_hash"]:
            self._append_event_raw(event)
            last_hash = event["hash"]
        elif last_hash != event["hash"]:
            raise StateCorruptionError("pending transaction does not extend current journal")

        new_state["last_event_hash"] = last_hash
        if self._state_hash(new_state) != event["after_state_hash"]:
            raise StateCorruptionError("pending transaction state digest mismatch")
        self._atomic_write_state(new_state)
        self.pending_path.unlink(missing_ok=True)
        self._fsync_directory()

    def _mutate(
        self,
        event_type: str,
        payload: dict[str, Any],
        mutator: Callable[[dict[str, Any]], None],
    ) -> int:
        if not event_type.strip():
            raise ValueError("event_type is required")
        _canonical_json(payload)  # validate JSON serializability before locking
        with self._locked():
            self._recover_pending_locked()
            state = self._read_state()
            ok, detail = self.verify_consistency()
            if not ok:
                raise StateCorruptionError(detail)

            before_hash = self._state_hash(state)
            new_state = json.loads(_canonical_json(state))
            mutator(new_state["data"])
            new_state["revision"] = int(state["revision"]) + 1
            new_state["last_event_hash"] = state["last_event_hash"]
            after_hash = self._state_hash(new_state)
            event = self._make_event(
                sequence=new_state["revision"],
                event_type=event_type,
                payload={**payload, "revision": new_state["revision"]},
                previous_hash=state["last_event_hash"],
                before_state_hash=before_hash,
                after_state_hash=after_hash,
            )
            new_state["last_event_hash"] = event["hash"]
            self._atomic_write_json(self.pending_path, {"event": event, "new_state": new_state})
            self._append_event_raw(event)
            self._atomic_write_state(new_state)
            self.pending_path.unlink(missing_ok=True)
            self._fsync_directory()
            return int(new_state["revision"])

    def get(self, key: str, default: Any = None) -> Any:
        return self._read_state()["data"].get(key, default)

    def snapshot(self) -> dict[str, Any]:
        return self._read_state()

    def set(self, key: str, value: Any, *, event_type: str = "state.set") -> int:
        if not key:
            raise ValueError("state key is required")
        _canonical_json(value)
        return self._mutate(event_type, {"key": key, "value": value}, lambda data: data.__setitem__(key, value))

    def delete(self, key: str) -> bool:
        if not key:
            raise ValueError("state key is required")
        with self._locked():
            self._recover_pending_locked()
            state = self._read_state()
            if key not in state["data"]:
                return False
        # Re-enter through the transactional path; concurrent writers are rechecked.
        def remove(data: dict[str, Any]) -> None:
            if key not in data:
                raise KeyError(key)
            del data[key]

        try:
            self._mutate("state.delete", {"key": key}, remove)
            return True
        except KeyError:
            return False

    def update(self, values: dict[str, Any], *, event_type: str = "state.update") -> int:
        if not isinstance(values, dict) or not values:
            raise ValueError("values must be a non-empty object")
        _canonical_json(values)
        return self._mutate(event_type, {"keys": sorted(values)}, lambda data: data.update(values))

    def _verify_journal_internal(self, *, allow_legacy: bool = False) -> tuple[bool, str, str, int]:
        previous_hash = self.ZERO_HASH
        expected_sequence = 1
        previous_after_hash: str | None = None
        for line_no, event in enumerate(self._journal_events(), start=1):
            if event.get("sequence") != expected_sequence:
                return False, f"sequence mismatch at line {line_no}", previous_hash, expected_sequence
            if event.get("previous_hash") != previous_hash:
                return False, f"hash-chain mismatch at line {line_no}", previous_hash, expected_sequence

            is_v2 = all(key in event for key in ("before_state_hash", "after_state_hash"))
            if not is_v2 and not allow_legacy:
                return False, f"legacy event at line {line_no}", previous_hash, expected_sequence

            if is_v2:
                body_keys = (
                    "sequence",
                    "timestamp",
                    "event_type",
                    "payload",
                    "previous_hash",
                    "before_state_hash",
                    "after_state_hash",
                )
                if previous_after_hash is not None and event["before_state_hash"] != previous_after_hash:
                    return False, f"state-chain mismatch at line {line_no}", previous_hash, expected_sequence
                previous_after_hash = event["after_state_hash"]
            else:
                body_keys = ("sequence", "timestamp", "event_type", "payload", "previous_hash")
                previous_after_hash = None

            try:
                body = {key: event[key] for key in body_keys}
            except KeyError:
                return False, f"missing journal field at line {line_no}", previous_hash, expected_sequence
            digest = _digest(body)
            if event.get("hash") != digest:
                return False, f"digest mismatch at line {line_no}", previous_hash, expected_sequence
            previous_hash = digest
            expected_sequence += 1
        return True, "ok" if expected_sequence > 1 else "empty journal", previous_hash, expected_sequence

    def verify_journal(self) -> tuple[bool, str]:
        ok, detail, _, _ = self._verify_journal_internal(allow_legacy=False)
        return ok, detail

    def verify_consistency(self) -> tuple[bool, str]:
        try:
            state = self._read_state()
            ok, detail, last_hash, next_sequence = self._verify_journal_internal(allow_legacy=False)
        except StateCorruptionError as exc:
            return False, str(exc)
        if not ok:
            return False, detail
        if state["last_event_hash"] != last_hash:
            return False, "state last_event_hash does not match journal"
        if state["revision"] != next_sequence - 1:
            return False, "state revision does not match journal sequence"
        events = self._journal_events()
        if events and events[-1].get("after_state_hash") != self._state_hash(state):
            return False, "state digest does not match journal"
        if not events and state["revision"] != 0:
            return False, "nonzero revision with empty journal"
        return True, "ok"


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(ch in "0123456789abcdef" for ch in value.lower())
