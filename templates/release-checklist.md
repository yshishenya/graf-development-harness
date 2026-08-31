# Release train checklist

- [ ] Approved PRs are listed with Feature IDs, task IDs and exact SHAs.
- [ ] Candidate is frozen; source SHA and changelog digest are immutable.
- [ ] One authoritative Full CI ran for this candidate and passed.
- [ ] Failed, stale, interrupted or skipped-gate evidence is rejected.
- [ ] Compatibility/migration impact and known limitations are documented.
- [ ] CalVer is used for products/services; SemVer for reusable harnesses.
- [ ] Tag, GitHub Release, Russian release notes and rollback ref agree.
- [ ] Post-publication attestation links the exact tag, SHA and Release URL.
- [ ] No production execution occurs without the explicit release approval gate.
