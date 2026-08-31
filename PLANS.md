# Development Process Harness Roadmap

Этот файл — источник долгосрочного плана reusable harness. Короткие правила
для каждого запуска остаются в `AGENTS.md`, а task-specific процедура — в
`skills/development-process/SKILL.md`.

## Цель

Дать любому consumer-репозиторию минимальный dependency-free набор контрактов
для параллельной разработки, bounded agent context, exact-SHA CI, редких
release trains, changelog fragments, Legacy Impact и безопасного Dev adapter.

## Фазы

1. **Contract core** — event identity, CI receipt, release-train и feature
   context schemas/validators; malformed input всегда fail-closed.
2. **Consumer adapter** — один Dev target, loopback origins, lock,
   atomic promotion, health/smoke и reversible rollback. Production rules
   остаются в consumer-проекте.
3. **Release** — immutable SemVer tag, checksum, русские notes, migration
   notes, rollback ref и package-content proof.
4. **Evolution** — backwards-compatible additions only; breaking changes
   требуют новой major версии и migration guide.

## Definition of done для версии

- `AGENTS.md` короткий и содержит только router/boundaries.
- С scoped skill загружается только нужная процедура.
- Self-test, clean sample, package-safety и malformed-input checks проходят.
- Wheel и sdist содержат ожидаемые schemas/templates/skill без secrets,
  private paths, raw audio или transcript text.
- Версия совпадает в `VERSION`, package metadata и runtime.
- Есть immutable tag, checksum, release notes и rollback ref.
- Consumer lock обновляется только после публикации и remote CI.

## Operator gates

Maintainer review и remote CI обязательны до публикации. Harness не выполняет
production deploy, migration, signing или удаление legacy: consumer adapter
должен предоставить свои отдельные гейты. Непрошедший gate означает блокировку,
а не автоматическое ослабление проверки.
