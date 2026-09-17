import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path

from janef_one.authorization import ActionClass, ActionRequest, AuthorizationGate, AuthorizationGrant
from janef_one.context import ContextBudgetError, ContextGovernor, ContextItem
from janef_one.evidence import EvidenceIntegrityError, EvidenceLedger
from janef_one.state import StateLockTimeout, StateStore
from janef_one.workgraph import WorkGraph, WorkNode


class HardeningTests(unittest.TestCase):
    def test_authorization_grant_scope_expiry_and_single_use(self):
        grant = AuthorizationGrant("g", frozenset({ActionClass.PRODUCTION}), ("prod/*",), time.time() + 60, True)
        gate = AuthorizationGate((grant,))
        req = ActionRequest("deploy", ActionClass.PRODUCTION, target="prod/api", target_verified=True)
        self.assertTrue(gate.decide(req).allowed)
        self.assertFalse(gate.decide(req).allowed)
        wrong = ActionRequest("deploy", ActionClass.PRODUCTION, target="dev/api", target_verified=True)
        self.assertFalse(AuthorizationGate((grant,)).decide(wrong).allowed)

    def test_required_context_fails_closed(self):
        item = ContextItem("r", "x" * 1000, "system", required=True)
        with self.assertRaises(ContextBudgetError):
            ContextGovernor().select([item], budget_tokens=1)

    def test_evidence_tampering_is_detected_on_reload(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "evidence.jsonl"
            ledger = EvidenceLedger(path)
            ledger.add("tests passed", evidence_type="test", source="runner", observed=True, detail={"ok": True})
            row = json.loads(path.read_text(encoding="utf-8"))
            row["claim"] = "forged"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaises(EvidenceIntegrityError):
                EvidenceLedger(path)

    def test_state_lock_does_not_steal_live_owner(self):
        with tempfile.TemporaryDirectory() as td:
            store = StateStore(td, lock_timeout=0.05, stale_lock_after=0.01)
            store.lock_path.write_text(json.dumps({"pid": os.getpid(), "created_at": "now", "token": "other"}), encoding="utf-8")
            old = time.time() - 60
            os.utime(store.lock_path, (old, old))
            with self.assertRaises(StateLockTimeout):
                with store._locked():
                    pass

    def test_parallel_workgraph_executes_independent_wave(self):
        graph = WorkGraph([WorkNode("a", "x"), WorkNode("b", "x"), WorkNode("c", "x", depends_on=("a", "b"))])
        lock = threading.Lock(); seen = []
        def handler(node):
            with lock:
                seen.append(node.id)
            return node.id
        report = graph.execute_parallel({"x": handler}, verifier=lambda n, out: n.id == out, max_workers=2)
        self.assertTrue(report.ok)
        self.assertEqual(set(report.succeeded), {"a", "b", "c"})
        self.assertEqual(seen[-1], "c")


if __name__ == "__main__":
    unittest.main()
