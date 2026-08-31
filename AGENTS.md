# Portable Harness Agent Guide

This directory contains the generic, dependency-free governance core. Keep
project-specific product, privacy, signing, deployment and data rules in the
consumer adapter.

## Rules

- Read this file and only the README/files needed for the current task.
- Never commit secrets, credentials, signed URLs, private data, raw audio,
  transcript text or machine-specific absolute paths.
- Keep releases immutable SemVer tags. Update changelog, migration notes and
  rollback ref together; never rewrite an existing tag.
- Prefer stdlib/native code and the smallest safe diff. Preserve fail-closed
  validation and leave one runnable self-test for new non-trivial behavior.
- Consumers pin an immutable release and provide their own adapter for build,
  health, signing and deployment behavior. When upgrading to `v0.1.10`, add
  `branch` and `source_sha` to existing feature pointers before running the
  checker; see README.md for the migration and checksum/provenance record.
- For a complete repeatable workflow, load `skills/development-process/SKILL.md`;
  keep this always-on file as the short router.
- Codex instruction files are layered global → project → nested directory;
  `AGENTS.override.md` takes precedence over `AGENTS.md` at the same level and
  the closest non-empty file wins. Keep this file short (the default combined
  instruction limit is 32 KiB) and put task-specific rules in scoped docs.

## Check

```sh
PYTHONDONTWRITEBYTECODE=1 ./bin/harness-check --self-test
sample_check_dir=$(mktemp -d)
harness_root=$(pwd)
git archive HEAD sample | tar -x -C "$sample_check_dir"
(cd "$sample_check_dir/sample" && PYTHONDONTWRITEBYTECODE=1 "$harness_root/bin/harness-check" --spec specs/001-example/spec.md)
PYTHONDONTWRITEBYTECODE=1 ./bin/harness-check --package-root .
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -c 'import dev_harness; print(dev_harness.__version__)'
```

Для pull request используется trusted workflow
`.github/workflows/pr-metadata.yml`: он передаёт body как данные в
`--pr-body` и проверяет Feature ID, issue/task links, exact SHA, lane,
evidence и Legacy Impact. Локально тот же контракт проверяется так:

```sh
PYTHONDONTWRITEBYTECODE=1 ./bin/harness-check --pr-body /path/to/pr-body.md --feature-id 222
```

Публикация выполняется только через reviewer-approved GitHub Release:
`release-assets.yml` сверяет tag с `VERSION`, запускает package-safety до
сборки, прикладывает wheel/sdist, codeload source archive, `SHA256SUMS` и
`RELEASE-PROVENANCE.json`. Workflow не меняет исходный tag и не публикует
артефакты без exact source SHA.

Run these commands from the harness repository root. They are intentionally
dependency-free and are the minimum required check before publishing a
release. Run the package scan before creating build artifacts; generated
bytecode, `build/` and `*.egg-info/` must not be included in a release.
