import unittest

from janef_one.authority import AuthorityLevel, Instruction, resolve_instructions


class AuthorityTests(unittest.TestCase):
    def test_higher_authority_wins(self):
        resolution = resolve_instructions([
            Instruction("skill says A", AuthorityLevel.SUBORDINATE_SKILL, "format", ordinal=2),
            Instruction("user says B", AuthorityLevel.USER, "format", ordinal=1),
        ])
        self.assertEqual(resolution.winners[0].text, "user says B")

    def test_later_same_authority_wins(self):
        resolution = resolve_instructions([
            Instruction("old", AuthorityLevel.USER, "tone", ordinal=1),
            Instruction("new", AuthorityLevel.USER, "tone", ordinal=2),
        ])
        self.assertEqual(resolution.winners[0].text, "new")


if __name__ == "__main__":
    unittest.main()

class AuthorityEdgeTests(unittest.TestCase):
    def test_ambiguity_is_exposed(self):
        res = resolve_instructions([
            Instruction("A", AuthorityLevel.USER, "x", "b", 1),
            Instruction("B", AuthorityLevel.USER, "x", "a", 1),
        ])
        self.assertEqual(len(res.ambiguous), 1)
        self.assertEqual(res.winners[0].text, "B")

    def test_invalid_instruction_rejected(self):
        with self.assertRaises(ValueError): Instruction("", AuthorityLevel.USER, "x")
        with self.assertRaises(ValueError): Instruction("x", AuthorityLevel.USER, "")
        with self.assertRaises(ValueError): Instruction("x", AuthorityLevel.USER, "x", ordinal=-1)
