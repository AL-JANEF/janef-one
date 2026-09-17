import unittest

from janef_one.router import route_intent


class RouterTests(unittest.TestCase):
    def test_research_freshness(self):
        route = route_intent("Research the latest market news and verify sources")
        self.assertEqual(route.primary, "research")
        self.assertTrue(route.needs_freshness)

    def test_deploy_requires_authorization_gate(self):
        route = route_intent("Deploy this code to production")
        self.assertEqual(route.primary, "coding")
        self.assertTrue(route.needs_authorization_gate)


if __name__ == "__main__":
    unittest.main()
