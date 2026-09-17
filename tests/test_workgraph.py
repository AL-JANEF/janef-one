import unittest

from janef_one.workgraph import WorkGraph, WorkGraphError, WorkNode


class WorkGraphTests(unittest.TestCase):
    def test_graph_executes_dependencies_with_verification(self):
        graph = WorkGraph([
            WorkNode("inspect", "read"),
            WorkNode("change", "edit", depends_on=("inspect",)),
            WorkNode("verify", "test", depends_on=("change",)),
        ])
        handlers = {
            "read": lambda node: "observed",
            "edit": lambda node: "changed",
            "test": lambda node: "passed",
        }
        report = graph.execute(handlers, verifier=lambda node, output: bool(output))
        self.assertTrue(report.ok)
        self.assertEqual(report.succeeded, ("inspect", "change", "verify"))

    def test_cycle_rejected(self):
        with self.assertRaises(WorkGraphError):
            WorkGraph([
                WorkNode("a", "x", depends_on=("b",)),
                WorkNode("b", "x", depends_on=("a",)),
            ])

    def test_missing_verifier_fails_closed(self):
        graph = WorkGraph([WorkNode("a", "x", requires_verification=True)])
        report = graph.execute({"x": lambda node: "result"})
        self.assertFalse(report.ok)
        self.assertEqual(report.failed, ("a",))


if __name__ == "__main__":
    unittest.main()

class WorkGraphEdgeTests(unittest.TestCase):
    def test_retry_then_success(self):
        attempts = {"n": 0}
        graph = WorkGraph([WorkNode("n", "flaky", max_attempts=2)])
        def handler(node):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise RuntimeError("first")
            return "ok"
        report = graph.execute({"flaky": handler}, verifier=lambda n, out: out == "ok")
        self.assertTrue(report.ok)
        self.assertEqual(report.attempts, 2)

    def test_failed_dependency_blocks_child(self):
        graph = WorkGraph([WorkNode("a", "bad"), WorkNode("b", "ok", depends_on=("a",))])
        report = graph.execute({"bad": lambda n: (_ for _ in ()).throw(RuntimeError("x")), "ok": lambda n: "ok"}, verifier=lambda n, out: True)
        self.assertEqual(report.failed, ("a",))
        self.assertEqual(report.blocked, ("b",))

    def test_missing_handler_fails(self):
        graph = WorkGraph([WorkNode("a", "missing", requires_verification=False)])
        report = graph.execute({})
        self.assertEqual(report.failed, ("a",))

    def test_roundtrip_serialization(self):
        graph = WorkGraph([WorkNode("a", "x", requires_verification=False, metadata={"k": "v"})])
        graph.execute({"x": lambda n: {"ok": True}})
        restored = WorkGraph.from_dict(graph.to_dict())
        self.assertEqual(restored.nodes["a"].status.value, "succeeded")
        self.assertEqual(restored.nodes["a"].metadata, {"k": "v"})

    def test_invalid_payload_rejected(self):
        with self.assertRaises(WorkGraphError): WorkGraph.from_dict({})
        with self.assertRaises(WorkGraphError): WorkGraph.from_dict({"nodes": ["bad"]})

    def test_parallel_missing_handler_fails_and_blocks(self):
        graph = WorkGraph([WorkNode("a", "missing"), WorkNode("b", "ok", depends_on=("a",))])
        report = graph.execute_parallel({"ok": lambda n: "ok"}, verifier=lambda n, out: True)
        self.assertEqual(report.failed, ("a",))
        self.assertEqual(report.blocked, ("b",))

    def test_reset_preserves_succeeded_when_requested(self):
        graph = WorkGraph([WorkNode("a", "x", requires_verification=False)])
        graph.execute({"x": lambda n: "ok"})
        graph.reset(include_succeeded=False)
        self.assertEqual(graph.nodes["a"].status.value, "succeeded")
        graph.reset()
        self.assertEqual(graph.nodes["a"].status.value, "pending")

    def test_invalid_execution_parameters(self):
        graph = WorkGraph([WorkNode("a", "x", requires_verification=False)])
        with self.assertRaises(ValueError): graph.execute({"x": lambda n: "ok"}, retry_delay=-1)
        with self.assertRaises(ValueError): graph.execute_parallel({"x": lambda n: "ok"}, max_workers=0)
        with self.assertRaises(ValueError): graph.execute_parallel({"x": lambda n: "ok"}, retry_delay=-1)
