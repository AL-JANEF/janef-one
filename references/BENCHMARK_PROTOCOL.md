# Benchmark Protocol

JANEF ONE releases should be evaluated with a reproducible A/B protocol.

## Minimum comparison
- Baseline agent/runtime without JANEF ONE.
- Same model/runtime with JANEF ONE enabled.
- Same tool access and task inputs.
- Blind or deterministic judging where practical.

## Metrics
1. Task success rate.
2. Assertion pass rate.
3. Critical safety violations.
4. False completion claims.
5. Tool/skill routing errors.
6. Verification omissions.
7. Recovery success.
8. Context tokens and tool calls when available.

## Release policy
- Zero known critical safety regressions in the release suite.
- No statistically/materially significant correctness regression in core categories.
- Any claimed improvement must include the case set, model/runtime version, date, judge method, and confidence/limitations.

The repository ships benchmark infrastructure and seed cases. It does not claim universal 10/10 performance until evidence exists.
