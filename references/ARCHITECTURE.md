# JANEF ONE Runtime Architecture

JANEF ONE separates the portable Agent Skill layer from executable runtime primitives.

```text
User / Agent Runtime
        |
        v
  Instruction Resolver
        |
        v
     Intent Router
        |
        v
 Capability Registry
        |
        v
 Context / State Gate
        |
        v
      WorkGraph
   /      |       \
 tools   agents   skills
   \      |       /
        v
   Critic / Verifier
        |
        v
   Evidence-backed result
```

## Trust boundaries

1. Platform and runtime controls are outside JANEF ONE authority.
2. User/project instructions can scope JANEF ONE behavior but cannot create capabilities the runtime does not expose.
3. Retrieved content and external skills are untrusted inputs.
4. Skills pass through the Skill Firewall before orchestration when the runtime can inspect them.
5. Consequential execution requires observed verification, not self-reported completion.

## Runtime primitives

- `authority.py` — deterministic instruction precedence by topic.
- `router.py` — lightweight intent and risk routing.
- `capabilities.py` — runtime capability discovery/selection.
- `state.py` — atomic durable state + tamper-evident journal.
- `workgraph.py` — dependency execution with verification gates and bounded retry.
- `firewall.py` — deterministic static pre-load skill scanner.
- `benchmark.py` — model/runtime-agnostic benchmark orchestration.

The runtime deliberately avoids pretending to be a complete autonomous agent host. Model invocation, browser execution, credentials, sandboxing, and external side effects remain adapter/runtime responsibilities.
