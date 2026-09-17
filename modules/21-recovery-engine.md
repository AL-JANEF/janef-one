# Recovery Engine

Use checkpoints for long-running or failure-sensitive work.

## Rules
- Checkpoint only meaningful recoverable boundaries.
- Store the phase, observed state, pending work, and verification evidence needed to resume.
- Verify state/journal integrity before restoring.
- Never treat an old checkpoint as current when newer authoritative instructions exist.
- Bound retained checkpoints and remove stale ephemeral data.
- On recovery, revalidate external assumptions that may have changed.

The runtime uses `RecoveryManager` over the journaled `StateStore`.
