import unittest

from janef_one.scheduler import AgentTask, MultiAgentScheduler


class SchedulerTests(unittest.TestCase):
    def test_parallelizes_independent_high_benefit_tasks(self):
        schedule = MultiAgentScheduler().plan([
            AgentTask("research-a", parallel_benefit=90),
            AgentTask("research-b", parallel_benefit=85),
            AgentTask("synthesize", depends_on=("research-a", "research-b"), parallel_benefit=10),
        ])
        self.assertEqual(schedule.waves[0], ("research-a", "research-b"))
        self.assertEqual(schedule.waves[1], ("synthesize",))
        self.assertEqual(schedule.mode, "parallel")

    def test_high_risk_task_not_parallelized(self):
        schedule = MultiAgentScheduler().plan([
            AgentTask("prod-a", parallel_benefit=100, risk=90),
            AgentTask("prod-b", parallel_benefit=100, risk=90),
        ])
        self.assertEqual(schedule.mode, "serial")


if __name__ == "__main__":
    unittest.main()

class SchedulerEdgeTests(unittest.TestCase):
    def test_empty_schedule(self):
        self.assertEqual(MultiAgentScheduler().plan([]).mode, "none")

    def test_budget_defers_task_and_dependents(self):
        tasks = [
            AgentTask("a", estimated_cost=5),
            AgentTask("b", depends_on=("a",), estimated_cost=1),
        ]
        schedule = MultiAgentScheduler().plan(tasks, max_total_cost=1)
        self.assertEqual(set(schedule.deferred), {"a", "b"})
        self.assertEqual(schedule.total_cost, 0)

    def test_cycle_rejected(self):
        with self.assertRaises(ValueError):
            MultiAgentScheduler().plan([AgentTask("a", ("b",)), AgentTask("b", ("a",))])

    def test_unknown_dependency_rejected(self):
        with self.assertRaises(ValueError):
            MultiAgentScheduler().plan([AgentTask("a", ("missing",))])

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            MultiAgentScheduler().plan([AgentTask("a"), AgentTask("a")])

    def test_invalid_parameters_rejected(self):
        scheduler = MultiAgentScheduler()
        for kwargs in (
            {"parallel_threshold": -1}, {"max_parallel": 0},
            {"high_risk_threshold": 101}, {"max_total_cost": -1},
        ):
            with self.assertRaises(ValueError):
                scheduler.plan([AgentTask("a")], **kwargs)

    def test_invalid_task_fields(self):
        with self.assertRaises(ValueError): AgentTask("")
        with self.assertRaises(ValueError): AgentTask("a", parallel_benefit=101)
        with self.assertRaises(ValueError): AgentTask("a", risk=-1)
        with self.assertRaises(ValueError): AgentTask("a", estimated_cost=0)
