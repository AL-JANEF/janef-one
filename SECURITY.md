# Security Policy

## Reporting a vulnerability

Do not open a public issue containing exploit details, credentials, private keys, or sensitive user data. Use GitHub private security advisories: https://github.com/AL-JANEF/janef-one/security/advisories/new

## Security scope

Security-relevant components include:
- `runtime/janef_one/firewall.py`;
- authority and instruction resolution;
- persistent-state integrity;
- WorkGraph verification gates;
- source-corpus ingestion scripts;
- CI/release validation.

## Design stance

External skills and retrieved prompt material are untrusted by default. JANEF ONE does not claim that static scanning alone makes a skill safe. Host runtimes should combine provenance checks, sandboxing, least privilege, explicit authorization for side effects, and verification.
