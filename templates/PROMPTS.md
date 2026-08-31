# Reusable Codex Prompts

Используйте один prompt для одной bounded-фазы. Перед записью агент обязан
прочитать применимые инструкции и сделать read-only preflight. Commit, push,
deploy и другие внешние изменения требуют отдельного подтверждения владельца.

## Orientation

```text
Прочитай AGENTS.md и только нужные scoped guidance, затем PLANS.md, GOALS.md,
PROMPTS.md и активный .specify/feature.json. Проверь branch, exact HEAD,
worktree и remote read-only. Выведи Feature ID, task IDs, scope, ограничения,
риски и следующий безопасный шаг. Файлы не меняй.
```

## Plan one phase

```text
Прочитай AGENTS.md, PLANS.md, GOALS.md и соответствующие spec/plan/tasks.
Сделай read-only preflight и подготовь только один bounded phase file в
harness/build/. Укажи цель, входы, non-goals, зависимости, approval gate,
red/green/refactor/verification, acceptance criteria и metadata-only evidence.
Не начинай реализацию и не меняй другие файлы.
```

## Execute one approved phase

```text
После проверки approval gate прочитай AGENTS.md, GOALS.md, PLANS.md, выбранный
build-файл, активный context и tasks.md. Выполни только этот phase: сначала
минимальная failing check, затем минимальная реализация, затем focused checks.
Не начинай следующую фазу. Commit/push/deploy выполняй только после отдельного
подтверждения. В конце обнови phase context и build-log только существенными
решениями и evidence.
```

## Verify and hand off

```text
Прочитай применимые инструкции и выбранный build-файл. Проведи только
указанные focused и broader checks, проверь exact SHA и чистоту worktree,
сохрани metadata-only evidence без secrets/private data/raw audio/transcripts.
Сообщи Feature ID, task IDs, SHA, файлы, команды, результаты, blockers и один
следующий безопасный шаг. Не утверждай PASS для непроверенных gate.
```

## Review or remediate

```text
Сделай read-only review текущей фазы по GOALS.md, spec/plan/tasks, acceptance
criteria и evidence. Сгруппируй findings по severity и укажи точный файл и
минимальное исправление. Не исправляй автоматически и не меняй checklist,
который принадлежит reviewer.
```

## Complete and hand off

```text
Проверь, что acceptance criteria и обязательные checks действительно PASS,
evidence привязан к exact SHA, scope не расширен, а context не дублирует
AGENTS/plan/build-log. Подготовь handoff и остановись; не запускай следующую
фазу, release, merge или deploy.
```
