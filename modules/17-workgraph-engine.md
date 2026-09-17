# WorkGraph Engine

Use WorkGraph for multi-step tasks with dependencies, verification gates, bounded retries, or recovery requirements.

## Graph rules
1. Express dependencies explicitly.
2. Reject cycles unless a future runtime explicitly supports controlled loops.
3. Block downstream nodes when a required dependency fails.
4. Require verification for consequential nodes by default.
5. Bound retries; never retry indefinitely.
6. Keep side effects outside planning/validation stages.
7. Preserve evidence for node outputs and failures.
8. Parallelize only dependency-independent nodes when the runtime can do so safely.

A node is not successful merely because its handler returned. If verification is required, the verifier must accept the observed output.
