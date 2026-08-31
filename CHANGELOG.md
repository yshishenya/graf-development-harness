# Changelog

## [0.1.9] - 2026-08-31

### Исправлено

- Portable `Legacy Impact` теперь требует корректную будущую ISO-дату expiry для compatibility exceptions.
- Package-safety scan проверяет credential assignments и в документации, не принимая реальные ключи за безопасный пример.

### Совместимость

- Python 3.9+; CLI и validator API обратно совместимы с `v0.1.8`.
- Откат: immutable `v0.1.8`.

### Проверки

- Self-test, clean sample smoke-test и recursive package-safety/provenance scan — PASS.

### Ограничения

- Product-specific capture, privacy, signing, deployment и data gates остаются adapter-контрактом потребителя.

## [0.1.8] - 2026-08-31

### Исправлено

- Усилена проверка portable context: feature directory, `spec.md`, numeric ID и symlink containment.
- Уточнена проверка Legacy Impact; разрешён безопасный комментарий после classification.
- Artifact identities ограничены безопасным форматом; `source-revision` связывается с observed SHA.
- Добавлен bounded Codex skill для progressive disclosure и bounded context.

### Совместимость

- Python 3.9+; CLI и validator API обратно совместимы с `v0.1.7`.
- Откат: immutable `v0.1.7`.

### Проверки

- Self-test, clean sample smoke-test и recursive package-safety/provenance scan — PASS.
- Публичный immutable release создан из exact commit `1d9f5c3ffb242f6480032958000fce40740a10b7`.

### Ограничения

- Product-specific capture, privacy, signing, deployment и data gates остаются adapter-контрактом потребителя.

## [Unreleased]

## [0.1.7] - 2026-08-31

### Исправлено

- Исправлены ссылки на текущий release и rollback в README.
- В публикацию добавлен GitHub Actions self-test workflow с отменой устаревших запусков.
- Синхронизированы generic validators, schemas, templates и source-tree launcher.

### Совместимость

- CLI и validator API обратно совместимы с `v0.1.6`.
- Откат: immutable `v0.1.6`.

### Проверки

- Self-test, clean sample smoke-test, package-safety scan и runtime-version check — PASS.
- Workflow ограничен `contents: read` и не требует секретов.

### Безопасность и контекст

- Package-safety scan теперь проверяет и собственный validator source, не
  оставляя исключений для credential assignments.
- Portable `AGENTS.md` явно описывает официальный порядок наследования
  инструкций Codex и default context limit.

## [0.1.6] - 2026-08-31

### Исправлено

- Усилены package safety, PR metadata, changelog и Legacy Impact validators.
- Добавлены fail-closed ошибки Git/GitHub discovery и безопасные self-check команды.

### Совместимость

- CLI и validator API совместимы с `v0.1.5`.
- Откат: immutable `v0.1.5`.

### Проверки

- Добавлен runnable source-tree self-test для portable package.
- Добавлен GitHub Actions workflow для self-test, sample smoke-test и
  publish-safety scan в матрице Python 3.9 и 3.12.
- Добавлены generic CI evidence и PR metadata validators с positive/negative
  self-tests.
- Добавлены JSON schemas и reusable templates для CI evidence и pull request.

## [0.1.4] - 2026-08-31

### Исправлено

- Синхронизирована версия во всех package metadata и runtime-модулях после
  публикации `v0.1.3`; существующие immutable tags не переписываются.
- Добавлены self-test и recursive package consistency/safety checks.

### Совместимость

- CLI и validator API обратно совместимы с `v0.1.3`.
- Откат: immutable `v0.1.3`.

## [0.1.3] - 2026-08-31

### Документация

- Добавлен стабильный `AGENTS.md` для bounded-контекста и безопасной работы
  reusable harness.

### Совместимость

- CLI и валидаторы не изменились; откат возможен на `v0.1.2`.

## [0.1.2] - 2026-08-31

### Исправлено

- Синхронизированы версия пакета, `VERSION` и публичный immutable ref.

### Совместимость

- API и CLI не изменились; откат на `v0.1.1` возможен по immutable ref.

## [0.1.1] - 2026-08-31

### Исправлено

- Удалены случайно опубликованные Python bytecode-файлы и добавлена защита от их повторного попадания в пакет.

### Совместимость

- API и CLI не изменились; откат на `v0.1.0` возможен по immutable ref.

## [0.1.0] - 2026-08-31

### Добавлено

- Переносимые проверки активного контекста, changelog fragments и Legacy Impact.
- Stdlib-only CLI и безопасная граница project adapter.

### Совместимость

- Python 3.9+; предыдущей версии нет, rollback выполняется возвратом pinned ref.
