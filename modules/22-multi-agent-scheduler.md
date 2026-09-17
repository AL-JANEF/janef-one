# Multi-Agent Scheduler

Parallel agents are an optimization, not a default.

## Delegate only when
- tasks are materially independent;
- parallelism reduces latency or improves independent verification;
- duplicated work is intentionally useful;
- risk and coordination overhead are acceptable.

## Avoid delegation when
- one small task can be completed directly;
- agents would inspect the same context redundantly;
- the action is high-risk and requires a single controlled authority path;
- dependencies force serial work anyway.

Plan dependency-safe waves, cap concurrency, and keep final verification centralized.
