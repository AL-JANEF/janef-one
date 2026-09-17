import json
import tempfile
import unittest
from pathlib import Path

from janef_one.state import StateStore


class StateTests(unittest.TestCase):
    def test_state_round_trip_and_journal(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(tmp)
            self.assertEqual(store.set("project", {"status": "active"}), 1)
            self.assertEqual(store.get("project"), {"status": "active"})
            self.assertEqual(store.verify_journal(), (True, "ok"))

    def test_journal_detects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(tmp)
            store.set("x", 1)
            line = json.loads(store.journal_path.read_text(encoding="utf-8"))
            line["payload"]["value"] = 2
            store.journal_path.write_text(json.dumps(line) + "\n", encoding="utf-8")
            ok, _ = store.verify_journal()
            self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()

class StateEdgeTests(unittest.TestCase):
    def test_update_delete_and_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            store = StateStore(td)
            store.update({"a": 1, "b": 2})
            self.assertEqual(store.get("missing", 9), 9)
            self.assertTrue(store.delete("a"))
            self.assertFalse(store.delete("a"))
            self.assertEqual(store.get("b"), 2)
            self.assertEqual(store.snapshot()["revision"], 2)

    def test_invalid_inputs(self):
        with tempfile.TemporaryDirectory() as td:
            store = StateStore(td)
            with self.assertRaises(ValueError): store.set("", 1)
            with self.assertRaises(ValueError): store.delete("")
            with self.assertRaises(ValueError): store.update({})
            with self.assertRaises(ValueError): store._mutate("", {}, lambda data: None)

    def test_corrupt_state_detected(self):
        with tempfile.TemporaryDirectory() as td:
            store = StateStore(td)
            store.state_path.write_text("{bad", encoding="utf-8")
            ok, detail = store.verify_consistency()
            self.assertFalse(ok)
            self.assertIn("cannot read state", detail)

    def test_state_last_hash_mismatch_detected(self):
        with tempfile.TemporaryDirectory() as td:
            store = StateStore(td)
            store.set("x", 1)
            raw = json.loads(store.state_path.read_text(encoding="utf-8"))
            raw["last_event_hash"] = "0" * 64
            store.state_path.write_text(json.dumps(raw), encoding="utf-8")
            ok, detail = store.verify_consistency()
            self.assertFalse(ok)
            self.assertIn("last_event_hash", detail)

class StateMigrationRecoveryTests(unittest.TestCase):
    def test_v1_empty_state_migrates_to_v2_consistently(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "state.json").write_text(json.dumps({"schema_version": 1, "revision": 0, "data": {"legacy": True}}), encoding="utf-8")
            store = StateStore(root)
            snap = store.snapshot()
            self.assertEqual(snap["schema_version"], 2)
            self.assertEqual(snap["revision"], 1)
            self.assertTrue(store.get("legacy"))
            self.assertEqual(store.verify_consistency(), (True, "ok"))

    def test_pending_transaction_recovers_after_journal_append(self):
        with tempfile.TemporaryDirectory() as td:
            store = StateStore(td)
            state = store.snapshot()
            before = store._state_hash(state)
            new_state = json.loads(json.dumps(state))
            new_state["data"]["recovered"] = 1
            new_state["revision"] = 1
            after = store._state_hash(new_state)
            event = store._make_event(
                sequence=1, event_type="state.set", payload={"key": "recovered", "value": 1, "revision": 1},
                previous_hash=state["last_event_hash"], before_state_hash=before, after_state_hash=after,
            )
            new_state["last_event_hash"] = event["hash"]
            store._atomic_write_json(store.pending_path, {"event": event, "new_state": new_state})
            reopened = StateStore(td)
            self.assertEqual(reopened.get("recovered"), 1)
            self.assertFalse(reopened.pending_path.exists())
            self.assertEqual(reopened.verify_consistency(), (True, "ok"))

    def test_invalid_pending_transaction_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            store = StateStore(td)
            store.pending_path.write_text("{bad", encoding="utf-8")
            with self.assertRaises(Exception):
                StateStore(td)

class StateValidationTests(unittest.TestCase):
    def test_invalid_lock_config_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError): StateStore(td, lock_timeout=-1)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError): StateStore(td, stale_lock_after=0)

class StateFormatCoverageTests(unittest.TestCase):
    def test_non_object_state_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/"state.json").write_text("[]", encoding="utf-8")
            with self.assertRaises(Exception): StateStore(root)

    def test_unsupported_schema_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/"state.json").write_text(json.dumps({"schema_version":99,"revision":0,"data":{},"last_event_hash":"0"*64}), encoding="utf-8")
            with self.assertRaises(Exception): StateStore(root)
