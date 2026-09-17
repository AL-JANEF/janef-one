import unittest

from janef_one.capabilities import Capability, CapabilityConflictError, CapabilityRegistry


class CapabilityTests(unittest.TestCase):
    def test_choose_prefers_higher_utility(self):
        reg = CapabilityRegistry([
            Capability("a", "search", quality=80, priority=80, risk=10, cost=20, tags=frozenset({"fresh"})),
            Capability("b", "search", quality=60, priority=50, risk=5, cost=10, tags=frozenset({"fresh"})),
        ])
        self.assertEqual(reg.choose(kind="search", required_tags={"fresh"}).name, "a")

    def test_duplicate_requires_explicit_replace(self):
        reg = CapabilityRegistry([Capability("a", "tool")])
        with self.assertRaises(CapabilityConflictError):
            reg.register(Capability("a", "tool"))
        reg.register(Capability("a", "tool", quality=99), replace=True)
        self.assertEqual(reg.get("a").quality, 99)

    def test_filters_unavailable_and_risk(self):
        reg = CapabilityRegistry([
            Capability("safe", "tool", risk=10),
            Capability("risky", "tool", risk=90),
            Capability("off", "tool", available=False),
        ])
        self.assertEqual([x.name for x in reg.available(kind="tool", max_risk=20)], ["safe"])

    def test_invalid_bounds(self):
        with self.assertRaises(ValueError):
            Capability("x", "tool", risk=101)
        with self.assertRaises(ValueError):
            CapabilityRegistry().available(max_risk=-1)


if __name__ == "__main__":
    unittest.main()
