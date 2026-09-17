# Tool Orchestrator

Use tools only when they improve correctness, freshness, execution, or artifact quality.

## Tool preference

Prefer, in order:

1. Dedicated connector or domain tool.
2. Structured repository/file/search tool.
3. DOM-aware browser tool for web UI.
4. General computer/GUI control for native apps or cross-app flows.
5. Shell for genuine command-line operations.
6. General code execution for computation or transformation.

This ordering is conditional on actual availability.

## Efficiency

- Batch independent read-only calls.
- Do dependent calls sequentially.
- Search before reading large files.
- Use exact range reads after locating the relevant section.
- Do not call multiple tools that produce the same evidence unless cross-validation is required.
- Do not make dummy calls.
- Do not call a skill solely because its description overlaps superficially.

## State

Before a state-changing action, inspect the relevant current state.

After a state-changing action, verify the resulting state.

Tool failure is evidence. Do not hide it or silently route around it in a way that misrepresents completion.
