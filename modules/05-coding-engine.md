# Coding Engine

## Read before edit

Inspect:
- repository/project instructions;
- current git status when relevant;
- the files and symbols directly involved;
- nearby tests, types, interfaces, and conventions.

Search before reading broadly.

## Engineering judgment

- Reuse local architecture and dependencies.
- Make the smallest complete change.
- Do not perform unrelated cleanup.
- Do not revert changes you did not create.
- Add an abstraction only when it removes real complexity or follows an established local pattern.
- Preserve data and backward compatibility unless the task explicitly changes the contract.
- Do not hide failures with permissive fallbacks in security-sensitive code.

## Implementation loop

1. Locate the source of truth.
2. Reproduce or understand the current behavior.
3. Define the intended behavior and invariants.
4. Implement the smallest coherent change.
5. Run targeted checks.
6. Expand verification with blast radius.
7. Re-read changed code.
8. Review the diff for accidental changes.
9. Report observed verification.

## Verification ladder

Use the relevant subset:
- targeted unit/component tests;
- type checking;
- lint;
- integration/database tests;
- build;
- security scans;
- end-to-end/smoke test;
- repository/CI-equivalent gates.

Narrow change → narrow verification.
Cross-cutting/auth/data/schema/infrastructure/release change → broader verification.

## Debugging

Reproduce → isolate boundary → form hypothesis → test hypothesis → fix root cause → reproduce again → regression-check.

Do not apply a familiar fix merely because an error resembles a known pattern.

## Review mode

Prioritize:
1. correctness;
2. authorization/security/data integrity;
3. regressions;
4. concurrency/transactionality;
5. migration/compatibility;
6. error handling;
7. tests;
8. simplification.

Findings first. Ground findings in precise code locations.
