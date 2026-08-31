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
- A bounded `skills/development-process/SKILL.md` for Codex-compatible agents.
- Self-test, secret/path/provenance scan and clean sample-project quickstart.

## Portable package

`src/dev_harness` and `bin/harness-check` are dependency-free and contain no
product runtime or private product rules. From this directory, install in
another repository with `python -m pip install .` or run the CLI directly. The
sample project under `sample/` is the publish smoke fixture. The following
commands are the source-tree self-check and must work from a clean checkout:

```sh
PYTHONDONTWRITEBYTECODE=1 ./bin/harness-check --self-test
sample_check_dir=$(mktemp -d)
harness_root=$(pwd)
git archive HEAD sample | tar -x -C "$sample_check_dir"
(cd "$sample_check_dir/sample" && PYTHONDONTWRITEBYTECODE=1 "$harness_root/bin/harness-check" --spec specs/001-example/spec.md)
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
metadata-only provenance evidence, migration notes, secret/path scan and a
rollback ref. Before publishing, run the checks above against the final
commit, record that exact commit SHA in the release notes and PR body, and
publish a SHA-256 checksum next to each release artifact (for example,
`sha256sum dist/* > SHA256SUMS`). Keep the checksum and source commit in the
release provenance record; do not generate or commit build artifacts here.

The next public release candidate is `v0.1.10` and will be pinned at
`https://github.com/yshishenya/graf-development-harness/releases/tag/v0.1.10`
only after its reviewer gate, tag and GitHub Release are complete. Until then,
consumers must continue to pin the current public immutable `v0.1.9` release;
it is also the rollback ref for the `v0.1.10` migration. A consumer must pin
the immutable release and update its migration notes and rollback ref together.

Migration from `v0.1.9` to `v0.1.10` requires existing `.specify/feature.json`
files to add the active `branch` and full 40-character `source_sha` fields;
the values must match the checkout used by the consumer. From the consumer
root, run `git branch --show-current` and `git rev-parse HEAD`, write those two
values into the pointer, then run `harness-check` before changing files. A
pointer missing either field is intentionally rejected; this explicit
migration keeps stale context fail-closed. It also makes CI
evidence timestamps strict RFC3339 UTC (with at most six fractional digits),
rejects unknown `-00:00` offsets and standard `Authorization: Bearer` token
syntax, and requires an explicit command/result in PR evidence. Consumers
should update their pointer and PR template, then run the same self-test and
package scan against the pinned immutable ref. Rollback is the immutable
`v0.1.9` ref.

The trusted `pull_request_target` workflow validates PR metadata from the base
branch, so a fork cannot replace the validator. It requires the canonical
sections, numeric Feature ID, umbrella issue, Spec task ID, explicit issue
link, exact source SHA, concrete validation lane, command/result evidence and
Legacy Impact classification. Run the same check locally with:

```sh
PYTHONDONTWRITEBYTECODE=1 ./bin/harness-check --pr-body /path/to/pr-body.md --feature-id 222
```

The `release-assets.yml` workflow runs only after a reviewer-approved GitHub
Release is published. It verifies the immutable tag and exact commit, runs the
package-safety gate before building, downloads the codeload archive addressed
by that commit, and uploads package files together with `SHA256SUMS` and
`RELEASE-PROVENANCE.json` as release assets. The provenance record contains
the repository, exact commit, codeload URL and digest for reproducible
verification; ordinary PR CI does not generate release assets.
