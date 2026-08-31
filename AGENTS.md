# Development Process Harness — Agent Guide

This repository is the portable, dependency-free governance core. Keep it
generic: project-specific product, privacy, signing, deployment and data rules
belong in a consumer adapter.

## Operating rules

- Read this file, then only the README and files needed for the current task.
- Never commit secrets, credentials, signed URLs, private data, raw audio,
  transcript text or machine-specific absolute paths.
- Keep releases immutable SemVer tags. Update `CHANGELOG.md`, migration notes
  and rollback ref together; never rewrite an existing tag.
- Prefer stdlib/native code and the smallest safe diff. Preserve fail-closed
  validation at trust boundaries and leave one runnable self-test for new
  non-trivial behavior.
- Consumer projects must pin a release/ref and provide their own adapter for
  build, health, signing and deployment behavior.

## Checks

```sh
(cd sample && ../bin/harness-check --spec specs/001-example/spec.md)
PYTHONPATH=src python3 -c 'import dev_harness; print(dev_harness.__version__)'
```

Do not add GRAF product gates or private paths to this repository.
