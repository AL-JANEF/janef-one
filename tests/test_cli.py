import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from janef_one.cli import main


class CLITests(unittest.TestCase):
    def test_route_command(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["route", "research latest news"])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(buf.getvalue())["primary"], "research")

    def test_scan_command(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "tmp-skill"
            root.mkdir()
            (root / "SKILL.md").write_text("---\nname: tmp-skill\ndescription: Temporary safe skill\n---\nRead only.\n", encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main(["scan-skill", str(root)])
            self.assertEqual(rc, 0)
            self.assertIn(json.loads(buf.getvalue())["decision"], {"allow", "review"})


if __name__ == "__main__":
    unittest.main()

class CLIStateTests(unittest.TestCase):
    def test_state_show_and_verify(self):
        with tempfile.TemporaryDirectory() as td:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main(["state", td, "show"])
            self.assertEqual(rc, 0)
            self.assertEqual(json.loads(buf.getvalue())["revision"], 0)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main(["state", td, "verify"])
            self.assertEqual(rc, 0)
            self.assertTrue(json.loads(buf.getvalue())["ok"])
