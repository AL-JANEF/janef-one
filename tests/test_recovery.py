import tempfile
import unittest

from janef_one.recovery import RecoveryManager
from janef_one.state import StateStore


class RecoveryTests(unittest.TestCase):
    def test_checkpoint_and_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = RecoveryManager(StateStore(tmp), max_checkpoints=2)
            manager.checkpoint("a", "inspect", {"done": ["read"]})
            manager.checkpoint("b", "edit", {"done": ["read", "edit"]})
            self.assertEqual(manager.latest().checkpoint_id, "b")
            self.assertEqual(manager.restore("a").phase, "inspect")

    def test_checkpoint_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = RecoveryManager(StateStore(tmp), max_checkpoints=2)
            manager.checkpoint("a", "one", {})
            manager.checkpoint("b", "two", {})
            manager.checkpoint("c", "three", {})
            self.assertIsNone(manager.restore("a"))


if __name__ == "__main__":
    unittest.main()

class RecoveryEdgeTests(unittest.TestCase):
    def test_validation_and_missing_restore(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            store = StateStore(td)
            with self.assertRaises(ValueError): RecoveryManager(store, max_checkpoints=0)
            mgr = RecoveryManager(store)
            with self.assertRaises(ValueError): mgr.checkpoint("", "phase", {})
            with self.assertRaises(ValueError): mgr.checkpoint("id", "", {})
            self.assertIsNone(mgr.restore("missing"))
