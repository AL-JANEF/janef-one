# Agent Skills Compatibility

JANEF ONE follows the open Agent Skills directory model: a required `SKILL.md` with YAML frontmatter plus optional scripts and reference resources.

Design constraints:
- `name` is lowercase kebab-case and matches the skill directory name when installed as `janef-one`.
- `description` states both capability and trigger intent.
- `SKILL.md` remains below the recommended 500-line boundary.
- detailed material is split into one-level resource paths for progressive disclosure.
- runtime code is optional; the skill remains readable even when the host cannot execute bundled Python.

Authoritative format reference: https://agentskills.io/specification
