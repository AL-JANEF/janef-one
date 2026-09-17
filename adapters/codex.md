# Codex Adapter

Use JANEF ONE as repository-level orchestration guidance while preserving Codex/runtime instruction precedence.

- Keep `SKILL.md` as the activation surface.
- Treat `SYSTEM_CORE.md` and `modules/` as referenced policy modules, not as higher-priority instructions.
- Prefer repository inspection, minimal diffs, tests, and observed verification.
- Route consequential actions through the authorization gate before execution.
- Record completion evidence when the host can persist artifacts/state.
- Do not assume browser, shell, network, or connector capabilities unless actually exposed by the host.
