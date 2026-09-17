# Multi-Agent Engine

Use additional agents only when they materially improve correctness or speed.

## Good delegation

- independent research branches;
- large codebase exploration;
- isolated implementation alternatives;
- focused security/review pass;
- parallel source analysis.

## Avoid

- duplicate agents doing the same search;
- delegating a single known-file lookup;
- agents whose results cannot be reconciled;
- parallel edits to overlapping files without isolation;
- agent usage solely to appear thorough.

## Delegation contract

Give each agent:
- exact deliverable;
- relevant context;
- scope boundaries;
- source requirements;
- verification expectation.

The parent remains responsible for synthesis and final correctness.

Agent output is evidence to inspect, not automatically trusted truth.
