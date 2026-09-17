import unittest

from janef_one.context import ContextBudgetError, ContextGovernor, ContextItem


class ContextGovernorTests(unittest.TestCase):
    def test_prefers_required_and_high_utility(self):
        items = [
            ContextItem("required", "critical fact", "file", relevance=100, trust=100, required=True),
            ContextItem("good", "high value evidence", "web", relevance=90, trust=90, recency=90),
            ContextItem("low", "background " * 100, "notes", relevance=10, trust=20, recency=10),
        ]
        selection = ContextGovernor().select(items, budget_tokens=30)
        ids = {item.id for item in selection.selected}
        self.assertIn("required", ids)
        self.assertIn("good", ids)
        self.assertNotIn("low", ids)

    def test_deduplicates_content(self):
        items = [
            ContextItem("a", "same content", "one", relevance=50),
            ContextItem("b", " same   content ", "two", relevance=90),
        ]
        selection = ContextGovernor().select(items, budget_tokens=100)
        self.assertEqual([item.id for item in selection.selected], ["b"])


if __name__ == "__main__":
    unittest.main()

class ContextEdgeTests(unittest.TestCase):
    def test_validation_and_overflow(self):
        with self.assertRaises(ValueError): ContextItem("", "x", "s")
        with self.assertRaises(ValueError): ContextItem("x", "x", "", relevance=1)
        with self.assertRaises(ValueError): ContextItem("x", "x", "s", trust=101)
        with self.assertRaises(ValueError): ContextGovernor(near_duplicate_threshold=1.1)
        with self.assertRaises(ValueError): ContextGovernor().select([], budget_tokens=-1)
        required = ContextItem("r", "x" * 100, "s", required=True)
        sel = ContextGovernor().select([required], budget_tokens=1, allow_required_overflow=True)
        self.assertIn(required, sel.selected)
        self.assertGreater(sel.estimated_tokens, sel.budget_tokens)

    def test_near_duplicate_prefers_stronger(self):
        a = ContextItem("a", "alpha beta gamma delta epsilon", "s", relevance=10)
        b = ContextItem("b", "alpha beta gamma delta epsilon", "s", relevance=90)
        sel = ContextGovernor().select([a, b], budget_tokens=100)
        self.assertEqual([x.id for x in sel.selected], ["b"])

class ContextSelectionTests(unittest.TestCase):
    def test_utilization_zero_and_nonzero_budget(self):
        from janef_one.context import ContextSelection
        self.assertEqual(ContextSelection((), (), 0, 0, 0).utilization, 0.0)
        self.assertEqual(ContextSelection((), (), 1, 0, 0).utilization, 1.0)
        self.assertEqual(ContextSelection((), (), 5, 10, 0).utilization, 0.5)
