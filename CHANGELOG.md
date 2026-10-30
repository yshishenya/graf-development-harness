# Changelog

## [0.1.15] - 2026-10-30

### Исправлено

- Явное пустое значение CDPATH в файле запуска устраняет предупреждение
  ShellCheck SC1007; поведение запуска сохраняется.
- ShellCheck добавлен в существующую матрицу CI до проверки пакета и сборки.
- v0.1.14 опубликована до пропущенной обязательной проверки shellcheck;
  поздняя проверка обнаружила предупреждение. Эта версия и её файлы сохранены,
  результат не выдан за успешную проверку до публикации.

### Совместимость и проверка

- Python 3.9+, интерфейсы и LICENSE не меняются. Новых зависимостей пакета нет.
- До новой публикации обязательны lint, self-test, scan, сборка, чистая
  установка, обновление/возврат и независимое ревью на точных исходниках.
- Возврат: неизменяемая v0.1.14 с известным предупреждением shellcheck.
- Связь: GRAF T062 / https://github.com/yshishenya/graf/issues/7824 .

## [0.1.14] - 2026-10-30

### Исправлено

- Проверка пакета отклоняет присваивания секретов в JSON-полях с кавычками
  и в именах переменных с префиксами; добавлены отдельные синтетические случаи.
- Обозначение лицензии в метаданных исправлено на `LicenseRef-GRAF-Harness`:
  исходный текст `LICENSE` сохранён побайтно, юридические условия не изменены.
- Исправлена устаревшая отметка о неопубликованной v0.1.13.

### Совместимость и возврат

- Python 3.9+; интерфейсы командной строки и Python сохраняются.
- Возврат: неизменяемая `v0.1.13`; в её проверке пакета остаются известные
  пропуски, поэтому после проверки возврата следует снова установить исправление.

### Проверки перед публикацией

- Обязательны независимое ревью происхождения и лицензии, self-test,
  проверка секретов/путей, настоящая сборка, чистая установка и контрольные суммы.
- Проверить обновление с v0.1.13, возврат и повторное обновление.
- Публикация блокируется при отказе любой обязательной проверки.

### Ограничения и связи

- Проверка не обнаруживает любые возможные секреты во всех форматах.
- Продуктовые сборка, подпись и развёртывание остаются у потребителя.
- Исправление исходника: PR #7; GRAF T062 / issue #7824.

## [0.1.13] - 2026-09-01

### Добавлено

- Fail-closed resolver для `pull_request`, `merge_group` и ручного запуска.
- Metadata-only CI receipt contract с exact-SHA и stale/superseded защитой.
- JSON schemas и templates для CI receipt и release train.
- OpenAI-style templates для `GOALS.md`, `PROMPTS.md`, bounded phase/context и
  metadata-only build log.
- Атомарный allocator Feature ID с блокировкой ledger и проверкой локальных
  refs/specs перед резервированием.
- CLI-проверка PR metadata и CI smoke-test для Feature ID, issue/task linkage и
  exact-SHA evidence.
- Проверка 32 KiB bounded agent context, дедупликация стабильных правил,
  канонический `Legacy Impact: Trigger`, `SECURITY.md` и `CODEOWNERS`.
- Сохранено fail-closed обнаружение bearer credentials из публичного `v0.1.12`.
- Контекст feature теперь проверяет `schema_version` и допустимый `risk_lane`.
- CI timestamp принимает RFC3339 precision любой длины, а changelog-фрагменты
  требуют явный `known_limitations`.

### Совместимость

- Python 3.9+; существующий CLI и validator API сохраняются.
- Откат: immutable `v0.1.12`.

### Проверки

- Self-test, clean sample smoke-test и package-safety scan — PASS.
- Сборка wheel/sdist и проверка содержимого артефактов — PASS.
- GitHub Actions self-test для Python 3.9 и 3.12 — PASS.

## [0.1.12] - 2026-09-01

### Исправлено

- Проверка CI evidence теперь fail-closed распознает любой bearer-токен,
  включая короткие значения и форму `Authorization: Bearer ...`.

### Совместимость

- Python 3.9+; CLI и validator API обратно совместимы с `v0.1.11`.
- Откат: immutable `v0.1.11`.

### Проверки

- Self-test, clean sample smoke-test, package-safety scan и runtime-version
  check — PASS.
## [0.1.11] - 2026-08-31

### Исправлено

- Runtime `__version__` синхронизирован с `VERSION` и `pyproject.toml`.

### Совместимость

- Python 3.9+; CLI и validator API обратно совместимы с `v0.1.10`.
- Откат: immutable `v0.1.10`.

### Проверки

- Self-test, clean sample smoke-test, package-safety scan и runtime-version check — PASS.

## [0.1.10] - 2026-08-31

### Добавлено

- Добавлена portable schema для per-worktree Feature context.
- Добавлены copyable templates для короткого `AGENTS.md`, feature workflow,
  Dev adapter, Legacy Impact и release train.

### Совместимость

- Python 3.9+; CLI и validator API обратно совместимы с `v0.1.9`.
- Откат: immutable `v0.1.9`.

### Проверки

- Self-test, clean sample smoke-test и recursive package-safety/provenance scan — PASS.

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
