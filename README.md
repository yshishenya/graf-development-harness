# Development Process Harness

This directory is the extraction boundary for the reusable public harness. It
must contain only generic rules, schemas, validators, templates, self-tests and
adapter interfaces. GRAF product-specific capture, privacy, deletion, signing,
provider and production gates remain in this repository's adapter.

## Non-negotiable boundaries

- Never commit secrets, API keys, credentials, signed URLs, raw audio,
  transcript text, private meeting content or machine-specific absolute paths.
- Pin every harness version by immutable commit/tag and document migration and
  rollback.
- Keep root project instructions short; load active feature context explicitly
  from per-worktree state.
- Use one active Dev manifest and one installed app when a consumer has the same
  single-application requirement; do not create a hidden parallel runtime.

## Planned portable contents

- Feature claim and bounded-context schemas/validators.
- Changelog fragment and Legacy Impact templates.
- SHA-bound CI evidence and pull-request metadata validators.
- Generic JSON schemas and copyable CI evidence / pull-request templates under
  `schemas/` and `templates/`.
- Release-candidate contracts and adapter interfaces.
- Dev manifest adapter interface with lock/atomic-promotion semantics.
- Self-test, secret/path/provenance scan and clean sample-project quickstart.

## Portable package

`src/dev_harness` and `bin/harness-check` are dependency-free and contain no
product runtime or private product rules. From this directory, install in
another repository with `python -m pip install .` or run the CLI directly. The
sample project under `sample/` is the publish smoke fixture. The following
commands are the source-tree self-check and must work from a clean checkout:

```sh
PYTHONDONTWRITEBYTECODE=1 ./bin/harness-check --self-test
(cd sample && PYTHONDONTWRITEBYTECODE=1 ../bin/harness-check --spec specs/001-example/spec.md)
PYTHONDONTWRITEBYTECODE=1 ./bin/harness-check --package-root .
```

The validator API is also available without installing dependencies:

```python
from dev_harness.validators import ci_evidence, pr_metadata

assert ci_evidence(evidence) == []
assert pr_metadata(pull_request_body, "216") == []
```

`ci_evidence()` enforces exact-SHA evidence, non-ambiguous status, required
commands/digests and authoritative full-run metadata. `pr_metadata()` enforces
the feature ID, umbrella issue, task ID, SHA, issue linkage, Legacy Impact and
required PR sections. JSON Schemas document the structural contract; these
Python validators perform the cross-field checks that JSON Schema cannot
express.

The package scan is intentionally run before building or installing the
package: generated `build/`, `*.egg-info/` and bytecode files are not
publishable. A consumer may run the same checks from its CI after extracting
this directory as the repository root.

Project adapters may add real build, health, signing and deployment probes, but
must preserve the exact-SHA, loopback-only, one-active-target and fail-closed
contracts. Each published version is immutable SemVer and requires a checksum,
migration notes, secret/path scan and a rollback ref.

The current public release is pinned at
`https://github.com/yshishenya/graf-development-harness/releases/tag/v0.1.5`;
`v0.1.4` remains the rollback ref. A consumer must pin the immutable release
and update its migration notes and rollback ref together.

The next planned release is `v0.1.6`. Until it is cut, keep `VERSION` and the
package metadata at the current published version and treat the new files as
unreleased changes. Publish only after the clean self-check, package scan,
provenance scan and immutable tag/release procedure pass.
