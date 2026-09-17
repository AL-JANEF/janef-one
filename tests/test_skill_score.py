import unittest

from janef_one.firewall import SkillScanResult
from janef_one.skill_score import score_skill


class SkillScoreTests(unittest.TestCase):
    def test_blocked_scan_forces_reject(self):
        score = score_skill(
            SkillScanResult(score=95, decision="block"),
            unique_capability=100,
            context_efficiency=100,
            benchmark_gain=100,
            overlap=0,
        )
        self.assertEqual(score.decision, "reject")

    def test_unique_safe_skill_can_be_subordinate(self):
        score = score_skill(
            SkillScanResult(score=100, decision="allow"),
            unique_capability=95,
            context_efficiency=90,
            benchmark_gain=85,
            overlap=10,
        )
        self.assertEqual(score.decision, "subordinate")
        self.assertGreaterEqual(score.total, 80)


if __name__ == "__main__":
    unittest.main()

class SkillScoreEdgeTests(unittest.TestCase):
    def test_invalid_dimensions_rejected(self):
        scan = SkillScanResult(score=100, decision="allow")
        for kwargs in (
            {"unique_capability": -1, "context_efficiency": 50},
            {"unique_capability": 50, "context_efficiency": 101},
            {"unique_capability": 50, "context_efficiency": 50, "benchmark_gain": 101},
            {"unique_capability": 50, "context_efficiency": 50, "overlap": -1},
        ):
            with self.assertRaises(ValueError): score_skill(scan, **kwargs)

    def test_low_score_rejects_and_mid_score_reviews(self):
        low = score_skill(SkillScanResult(score=10, decision="allow"), unique_capability=0, context_efficiency=0, benchmark_gain=0, overlap=100)
        self.assertEqual(low.decision, "reject")
        mid = score_skill(SkillScanResult(score=100, decision="allow"), unique_capability=40, context_efficiency=80, benchmark_gain=50, overlap=50)
        self.assertIn(mid.decision, {"review", "subordinate"})
