# Changelog

## [Unreleased] — планируется `v0.1.5`

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
