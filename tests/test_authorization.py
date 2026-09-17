import unittest

from janef_one.authorization import ActionClass, ActionRequest, AuthorizationGate


class AuthorizationTests(unittest.TestCase):
    def test_read_only_allowed(self):
        decision = AuthorizationGate().decide(ActionRequest("inspect", ActionClass.READ_ONLY))
        self.assertTrue(decision.allowed)

    def test_production_requires_target_and_authorization(self):
        gate = AuthorizationGate()
        self.assertFalse(gate.decide(ActionRequest("deploy", ActionClass.PRODUCTION)).allowed)
        self.assertFalse(gate.decide(ActionRequest("deploy", ActionClass.PRODUCTION, target_verified=True)).allowed)
        self.assertTrue(gate.decide(ActionRequest(
            "deploy",
            ActionClass.PRODUCTION,
            target="prod/service-a",
            target_verified=True,
            explicit_authorization=True,
        )).allowed)


if __name__ == "__main__":
    unittest.main()

class AuthorizationEdgeTests(unittest.TestCase):
    def test_reusable_grant(self):
        import time
        from janef_one.authorization import AuthorizationGrant
        grant = AuthorizationGrant("g", frozenset({ActionClass.PUBLICATION}), ("repo/*",), time.time() + 60, False)
        gate = AuthorizationGate((grant,))
        req = ActionRequest("publish", ActionClass.PUBLICATION, target="repo/main", target_verified=True)
        self.assertTrue(gate.decide(req).allowed)
        self.assertTrue(gate.decide(req).allowed)

    def test_expired_grant_rejected(self):
        import time
        from janef_one.authorization import AuthorizationGrant
        grant = AuthorizationGrant("g", frozenset({ActionClass.PUBLICATION}), ("repo/*",), time.time() - 1)
        gate = AuthorizationGate((grant,))
        req = ActionRequest("publish", ActionClass.PUBLICATION, target="repo/main", target_verified=True)
        self.assertFalse(gate.decide(req).allowed)

    def test_duplicate_grant_rejected(self):
        import time
        from janef_one.authorization import AuthorizationGrant
        grant = AuthorizationGrant("g", frozenset({ActionClass.PUBLICATION}), ("*",), time.time() + 60)
        with self.assertRaises(ValueError): AuthorizationGate((grant, grant))
        gate = AuthorizationGate((grant,))
        with self.assertRaises(ValueError): gate.add_grant(grant)

    def test_grant_validation_and_empty_action(self):
        import time
        from janef_one.authorization import AuthorizationGrant
        with self.assertRaises(ValueError): AuthorizationGrant("", frozenset({ActionClass.PUBLICATION}), ("*",), time.time()+1)
        with self.assertRaises(ValueError): AuthorizationGrant("g", frozenset(), ("*",), time.time()+1)
        with self.assertRaises(ValueError): AuthorizationGrant("g", frozenset({ActionClass.PUBLICATION}), (), time.time()+1)
        with self.assertRaises(ValueError): ActionRequest("", ActionClass.READ_ONLY)
