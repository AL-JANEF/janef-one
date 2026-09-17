import unittest

from janef_one.evidence import EvidenceLedger


class EvidenceTests(unittest.TestCase):
    def test_observed_evidence_supports_claim(self):
        ledger = EvidenceLedger()
        ledger.add("tests passed", evidence_type="test-output", source="unit", observed=True, detail={"passed": 25})
        self.assertTrue(ledger.is_supported("tests passed", accepted_types={"test-output"}))
        ledger.require("tests passed", accepted_types={"test-output"})

    def test_unobserved_intent_does_not_support_claim(self):
        ledger = EvidenceLedger()
        ledger.add("deployed", evidence_type="plan", source="agent", observed=False, detail="will deploy")
        self.assertFalse(ledger.is_supported("deployed"))
        with self.assertRaises(RuntimeError):
            ledger.require("deployed")


if __name__ == "__main__":
    unittest.main()

class EvidenceEdgeTests(unittest.TestCase):
    def test_filters_and_require(self):
        ledger = EvidenceLedger()
        ledger.add("done", evidence_type="test", source="ci", observed=True, detail=1)
        ledger.add("done", evidence_type="log", source="local", observed=True, detail=2)
        self.assertEqual(len(ledger.supporting_records("done", accepted_types={"test"})), 1)
        self.assertTrue(ledger.is_supported("done", accepted_sources={"ci"}))
        ledger.require("done", accepted_types={"test"})
        with self.assertRaises(RuntimeError): ledger.require("missing")
        with self.assertRaises(ValueError): ledger.is_supported("done", min_records=0)

    def test_invalid_add_rejected(self):
        ledger = EvidenceLedger()
        with self.assertRaises(ValueError): ledger.add("", evidence_type="test", source="x", observed=True, detail={})
        with self.assertRaises(TypeError): ledger.add("x", evidence_type="test", source="x", observed=True, detail={1,2})
