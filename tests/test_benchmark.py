import json
import tempfile
import unittest
from pathlib import Path

from janef_one.benchmark import BenchmarkCase, load_cases, run_cases


class BenchmarkTests(unittest.TestCase):
    def test_load_and_run(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "cases.json"
            path.write_text(json.dumps([{"id": "x", "prompt": "hello", "assertions": ["contains hello"]}]), encoding="utf-8")
            cases = load_cases(path)
            report = run_cases(cases, lambda case: case.prompt, lambda case, out, assertion: ("hello" in out, assertion))
            self.assertEqual(report.passed, 1)
            self.assertEqual(report.total, 1)
            self.assertEqual(report.assertion_rate, 1.0)

    def test_zero_assertions_is_well_defined(self):
        report = run_cases([BenchmarkCase("x", "p", ())], lambda case: "", lambda *args: (True, ""))
        self.assertEqual(report.assertion_rate, 1.0)
        self.assertEqual(report.passed, 1)


if __name__ == "__main__":
    unittest.main()
