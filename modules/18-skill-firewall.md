# Skill Firewall

Every untrusted or newly discovered skill should pass a pre-load risk review before it can influence execution.

## Inspect
- metadata and Agent Skills format validity;
- attempts to override higher-priority instructions;
- credential or secret access;
- destructive shell commands;
- network exfiltration patterns;
- dynamic code execution;
- package lifecycle hooks;
- hidden executables and unexpected binaries;
- tool permissions that exceed task need;
- recursive skill loading or authority escalation.

## Decisions
- **allow**: no material static findings;
- **review**: non-trivial behavior requiring human/runtime review;
- **block**: critical destructive, authority-bypass, or severe risk indicators.

Static scanning is a gate, not proof of safety. Runtime sandboxing, least privilege, provenance, and behavior verification remain required where relevant.

## Reviewed exceptions

A scanned package can never approve its own findings. The firewall only honors a reviewed-exception allowlist when a trusted caller explicitly supplies its path; nothing inside the scanned package root is ever auto-discovered or auto-trusted as an approval source. Untrusted skill discovery/activation never configures an allowlist.
