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
- Atomic Feature ID reservation ledger and collision checks across local refs.
- Changelog fragment and Legacy Impact templates.
- SHA-bound CI evidence and pull-request metadata validators.
- Fail-closed event identity and metadata-only CI receipt contracts.
- Generic JSON schemas and copyable CI evidence / pull-request templates under
  `schemas/` and `templates/`.
- Copyable short `AGENTS.md`, feature workflow, Dev adapter, Legacy Impact and
  release-train templates under `templates/`.
- OpenAI-style `GOALS.md`/`PROMPTS.md` plus bounded phase, context and build-log
  templates under `templates/`; consumers fill them with project-specific
  content instead of expanding always-on instructions.
- Release-candidate contracts and adapter interfaces.
- Dev manifest adapter interface with lock/atomic-promotion semantics.
- A bounded `skills/development-process/SKILL.md` for Codex-compatible agents.
- Self-test, secret/path/provenance scan and clean sample-project quickstart.

## Portable package

`src/dev_harness` and `bin/harness-check` are dependency-free and contain no
product runtime or private product rules. From this directory, install in
another repository with `python -m pip install .`, or use the executable
source-tree launcher `./bin/harness-check` without installing the package. The
sample project under `sample/` is the publish smoke fixture. The following
commands are the source-tree self-check and must work from a clean checkout:

```sh
PYTHONDONTWRITEBYTECODE=1 ./bin/harness-check --self-test
(cd sample && PYTHONDONTWRITEBYTECODE=1 ../bin/harness-check --spec specs/001-example/spec.md)
PYTHONDONTWRITEBYTECODE=1 ./bin/harness-check --package-root .
PYTHONDONTWRITEBYTECODE=1 ./bin/harness-check --context-check . --package-root .
```

The validator API is also available without installing dependencies:

```python
from dev_harness.validators import ci_evidence, pr_metadata

assert ci_evidence(evidence) == []
assert pr_metadata(pull_request_body, "216") == []
```

Reserve a Feature ID before creating a branch or Spec Kit feature. Point
`--feature-id-ledger` at one shared coordinator path when several worktrees
allocate IDs concurrently; the command takes an OS file lock and atomically
updates the append-only ledger. It also scans local specs, fragments and Git
refs, and fails closed on a collision:

```sh
./bin/harness-check --reserve-feature-id --owner agent-name \
  --umbrella-issue 6090 --feature-id-ledger /shared/graf/feature-ids.json
```

The output is the newly reserved ID (for example `Feature ID: F230`). Creating
the corresponding GitHub umbrella issue is a separate tracker operation; put
its number in the reservation record and do not treat a local ledger as a
replacement for GitHub's issue canon.

Validate a PR body in CI with the same dependency-free CLI:

```sh
./bin/harness-check --pr-body-file "$RUNNER_TEMP/pr-body.md" --feature-id F230
```

`--context-check` checks the layered `AGENTS.md` / `AGENTS.override.md` files
against the 32 KiB always-on budget and reports duplicated stable rules. Keep
phase prompts, specs and build logs outside those files so they are loaded only
when the current phase needs them.

The portable CI contract API is dependency-free as well:

```python
from dev_harness.ci_contracts import ci_receipt, release_train, resolve_event_identity

# Native GitHub merge_group payloads can omit the group id and PR mapping.
# Supply those values from the trusted adapter instead of guessing them.
identity = resolve_event_identity(
    event_payload,
    "merge_group",
    merge_group_id=trusted_group_id,
    pull_request_numbers=trusted_pr_numbers,
)
assert ci_receipt(receipt_payload) == []
assert release_train(train_payload) == []
```

`ci_evidence()` enforces exact-SHA evidence, non-ambiguous status, required
commands/digests and authoritative full-run metadata. `pr_metadata()` enforces
the feature ID, umbrella issue, task ID, SHA, issue linkage, Legacy Impact and
required PR sections. JSON Schemas document the structural contract; these
Python validators perform the cross-field checks that JSON Schema cannot
express.

Release-train receipts are lineage-bound: every declared PR and merge group
must have one matching receipt. PR receipts target `source_sha`; merge-group
and authoritative receipts target `synthetic_merge_sha` when present, otherwise
authoritative CI targets `post_merge_sha` or `source_sha`. An `approved` train
must include a passed authoritative receipt.

The package scan is intentionally run before building or installing the
package: generated `build/`, `*.egg-info/` and bytecode files are not
publishable. The wheel installs schemas, templates and the bounded skill under
`share/development-process-harness/`; the source distribution also includes
the sample and launcher. A consumer may run the same checks from its CI after
extracting this directory as the repository root.

Project adapters may add real build, health, signing and deployment probes, but
must preserve the exact-SHA, loopback-only, one-active-target and fail-closed
contracts. Each published version is immutable SemVer and requires a checksum,
migration notes, secret/path scan and a rollback ref.

The current public release is pinned at
`https://github.com/yshishenya/graf-development-harness/releases/tag/v0.1.12`.
This branch prepares the next candidate `v0.1.13`; it is not a public release
until the PR is merged and the immutable tag and GitHub Release exist.
Consumers must keep pinning the published immutable release and update its
migration notes and rollback ref together.

Migration from `v0.1.12` to `v0.1.13` adds generic event identity, metadata-only
CI receipts, release-train lineage, atomic Feature ID allocation, bounded
context checks and reusable process templates. It also validates schema version
and risk lane, accepts arbitrary RFC3339 fractional-second precision, and
requires `known_limitations` in changelog fragments. Migration from `v0.1.11`
to `v0.1.12` made CI-evidence credential detection fail closed for every bearer
token, including short tokens and the common `Authorization: Bearer ...` form.
Migration from `v0.1.10` to `v0.1.11`
fixed the runtime package-version declaration. The portable feature-context
schema and copyable templates were introduced in `v0.1.10`. Consumers should
run the same self-test and package scan after updating their pinned ref.
Rollback is the immutable `v0.1.12` ref.
