# Security policy

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Use GitHub's
private **Report a vulnerability** action on the repository Security tab. Include
the affected version or commit, a short reproduction, impact, and any safe
mitigation. Do not include credentials, personal data, raw recordings,
transcripts, or signed URLs in the report.

We will acknowledge a report when it is received, keep the report private while
it is investigated, and publish a remediation note only after a fix or agreed
mitigation is available. This repository contains a generic development
harness; product-specific secrets and deployment incidents belong in the
consumer project's private security channel.

## Supported versions

Only the latest immutable release and the current default branch receive
security fixes. Pin consumers to an immutable release or commit and keep the
previous known-good release as the rollback reference.
