# Security Model

## Goals
- prevent subordinate skills from becoming authority sources;
- fail closed when required verification is unavailable;
- reduce accidental destructive execution;
- make state tampering detectable;
- keep source-corpus material observational rather than authoritative;
- preserve least privilege and explicit side-effect boundaries.

## Non-goals
The bundled Skill Firewall is not an antivirus engine, malware sandbox, SAST replacement, or guarantee that code is safe. Regex/static findings are only one deterministic gate.

## Skill trust levels

| Level | Meaning | Default action |
|---|---|---|
| Built-in canonical | reviewed JANEF ONE module | load on demand |
| Trusted local | owner-reviewed skill | load if task-specific |
| External signed/known | provenance known, content changed? | verify hash + scan |
| External unknown | discovered or downloaded | scan + review |
| Blocked | critical finding or policy conflict | do not load |

## State integrity
`StateStore` uses atomic replacement for state snapshots and SHA-256 chaining for journal events. This detects journal mutation; it does not prevent a fully privileged attacker from replacing both state and journal.

## Destructive actions
JANEF ONE separates planning from execution. An adapter should require explicit authorization for publishing, deleting, overwriting, sending, transferring, credential changes, production mutations, or irreversible actions.
