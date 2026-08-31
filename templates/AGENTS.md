# Project Agent Guide

Keep this file as a short router. Put stable repository rules here, and put
feature-specific procedures in the active Spec Kit directory or a scoped
guidance file. Do not paste full history, CI logs or unrelated specs into the
always-on instructions.

## Required context

- Validate `.specify/feature.json` before editing.
- Work in one feature worktree with one owner, branch, Feature ID and evidence
  namespace.
- Read only the active `spec.md`, `plan.md`, `tasks.md`, `quickstart.md` and
  guidance required by the risk lane.
- Stop on missing, stale or mismatched context; never infer a feature from
  timestamps or the newest directory.

## Required gates

- Reserve a collision-free Feature ID and umbrella issue before branch/spec.
- Follow `specify → clarify → plan → checklist → tasks → analyze →
  taskstoissues → implement → converge → validation` for significant work.
- Use focused checks while editing, one exact-SHA fast gate before PR, and one
  authoritative Full CI only after a frozen release candidate.
- Never commit secrets, private data, raw recordings or transcript content to
  context, evidence, specs or changelog fragments.
