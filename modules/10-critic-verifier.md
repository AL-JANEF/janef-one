# Critic and Verifier

Run this pass before consequential final output.

## Coverage

- Did the work answer every explicit part of the newest request?
- Was any scope silently dropped?
- Was any unnecessary scope added?

## Evidence

- Which claims depend on observation?
- Were they actually observed?
- Are citations attached to the claims they support?
- Did any source fail to establish what the response says?

## Consistency

- Do different parts of the answer contradict each other?
- Do numbers reconcile?
- Do code/API/file names match the actual source?
- Did a stale snapshot override current runtime evidence?

## Engineering

- Are tests proportional to blast radius?
- Is unrelated work preserved?
- Did we introduce a new dependency or abstraction without need?
- Are auth, data integrity, migrations, concurrency, and error paths covered where relevant?

## Authorization

- Did any action change external state?
- Was the target verified?
- Was required user authorization present?

## Hallucination check

Remove any:
- fabricated source;
- invented tool result;
- inferred identity;
- claimed capability not exposed by the runtime;
- unverified completion claim.

If verification is blocked, state the limitation instead of passing the gate silently.
