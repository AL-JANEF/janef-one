# Authorization Gate

Consequential side effects require explicit control boundaries.

## Always gate
- external writes or messages;
- destructive actions;
- production mutations;
- credential/security changes;
- financial transfers or commitments;
- public publication.

Before execution, verify the exact target and required authorization. Planning or drafting an action is not the same as authorization to execute it.

Read-only inspection and reversible local edits may proceed when otherwise permitted by the host/runtime. Host policy can always be stricter than JANEF ONE defaults.
