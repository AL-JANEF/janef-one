# Generic Agent Adapter

Use `SYSTEM_CORE.md` as the portable system/developer-layer kernel where your own orchestration framework permits it.

Expose tool capabilities separately from the kernel and let JANEF ONE discover them at runtime.

Recommended architecture:

system/platform policy
    ↓
JANEF ONE SYSTEM_CORE
    ↓
intent + instruction resolver
    ↓
capability router
    ↓
tools / domain modules / external skills
    ↓
critic-verifier
    ↓
response

Do not concatenate every provider prompt into one giant system prompt. That creates contradictory tool contracts, stale identities, context bloat, and poor instruction salience.
