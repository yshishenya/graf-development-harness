---
name: development-process
description: Run a bounded, evidence-first feature, CI, release and legacy workflow in a consumer repository.
---

# Development process

Use this skill when a task changes product behavior, infrastructure, release
metadata or agent governance.

1. Read the consumer root `AGENTS.md`, then only the scoped guidance named by
   that file. Do not load historical specs or complete CI logs into context.
2. Require an explicit per-worktree feature pointer under
   `.specify/feature.json`; never infer a feature from timestamps or the newest
   directory. Validate the pointer before editing.
3. Keep one worktree, branch, owner, changelog fragment and evidence namespace
   per Feature ID. Reserve the ID against local refs and the GitHub tracker
   before creating a spec.
4. Use the repository's risk lane and Spec Kit order. For significant work,
   complete specify → clarify → plan → checklist → tasks → analyze →
   taskstoissues → implement → converge → validation.
5. Run focused checks during editing and one fast, exact-SHA gate before PR.
   Freeze a release candidate before the single authoritative Full CI run;
   stale, interrupted or skipped-gate evidence cannot authorize release.
   For a release train, require a synthetic merge SHA, link the candidate with
   `--train`, attest the single Full CI receipt with `train-attest`, and pass
   only the resulting `*-go.json` train to `decide --train`.
6. Test a selected SHA in the consumer's single Dev target with a lock,
   atomic manifest, smoke checks and reversible promotion. Keep production
   origins, credentials and data outside the Dev adapter.
7. Add a `Legacy Impact` decision to every feature and PR. Remove new legacy
   immediately; existing legacy is retired in separately owned slices with an
   owner, expiry, trigger, validation and rollback.
8. Do not commit, publish, deploy or close tracker items until the consumer's
   required reviewer and approval gates are complete. Preserve metadata-only
   evidence and never write secrets or private user data into it.

## Context handoff

At the end of a turn, report only: Feature ID, task IDs, exact SHA, files
changed, checks run, evidence paths, blockers and the next safe action. Start a
fresh thread or use compaction when the task changes scope; do not paste the
entire previous transcript into a new prompt.
