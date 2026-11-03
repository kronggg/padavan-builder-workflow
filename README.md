# padavan-builder-workflow

Автоматическая сборка прошивок [Padavan (nilabsent/padavan-ng)](https://github.com/nilabsent/padavan-ng) для нескольких моделей роутеров.

Форк [shvchk/padavan-builder-workflow](https://github.com/shvchk/padavan-builder-workflow) — функционал расширен: несколько моделей, мониторинг upstream, автоматический changelog с категоризацией коммитов.

> Форк создан для автоматизации собственных сборок. Changelog и прошивки предоставляются as-is.

## Возможности

- **Независимые сборки** — отдельные job (rm-ac2100, mi-3, mi-r3gv2) под каждую модель, со своим `.config` и проверкой partition limit. Возможность запускать сборку выбранной модели или всех разом.
- **Единый Release** — после всех успешных сборок: один GitHub Release со всеми прошивками, конфигами и общим changelog
- **Автоматический changelog** — категоризация upstream-коммитов (Добавлено/Исправлено/Обновлено/Удалено/Прочее)
- **Мониторинг upstream** — ежедневная проверка новых коммитов с фильтрацией meaningful/trivial
- **Еженедельная автосборка** — в понедельник при наличии meaningful изменений watch-upstream запускает сборку (dispatch), без ручного тега
- **Urgency-сборка** — экстренный запуск при CVE/security-фиксах
- **Ручной запуск** — workflow_dispatch с выбором модели или all
- **Валидация размера** — проверка лимита firmware partition из upstream
- **GitHub Watch → Releases** — уведомления о новых сборках через нативный механизм GitHub

## Модели

| Модель | Конфиг | SoC | Flash | Firmware |
|---|---|---|---|---|
| Xiaomi RM-AC2100 | `configs/rm-ac2100.config` | MT7621 | 128 MB NAND | 20 MB |
| Xiaomi Mi Router 3 | `configs/mi-3.config` | MT7620 | 128 MB NAND | 16 MB |
| Xiaomi Mi Router 4A Gigabit (R4A/R3Gv2) | `configs/mi-r3gv2.config` | MT7621 | 16 MB SPI | 15.4 MB |

## Триггеры сборки

| Событие | Ветка | Действие | Когда |
|---|---|---|---|
| `dispatch-watch` (cron 08:05 MSK) | `main` | Запускает `watch-upstream.yml` на `beta` | Ежедневно |
| `watch-upstream` (cron 08:05 MSK) | `beta` | Мониторинг upstream → dispatch сборки | В понедельник или при urgency |
| `workflow_dispatch` (model=all) | `beta` | Полная сборка + Release + finalize | Ручной запуск / авто — от watch-upstream |
| `push` на тег `v*` | — | Полная сборка + Release | Ручной релиз |

> **Почему два файла.** GitHub запускает `schedule` только если файл воркфлоу есть
> на **default branch** (`main`). Вся логика автосборки живёт в `beta`. Поэтому на
> `main` лежит тонкий `dispatch-watch.yml`, который ничего не собирает — он только
> вызывает `watch-upstream.yml` на `beta`. Когда `beta` смержится в `main`, файл
> станет лишним и его нужно удалить.

Автосборка запускается из `watch-upstream.yml` через `gh workflow run build.yml --ref beta` — без тегов. `build.yml`, `configs/` и `.upstream/` живут только в ветке `beta`.

## Как работает changelog

После успешной сборки job `finalize`:
1. Клонирует nilabsent/padavan-ng
2. Читает предыдущий коммит из `.upstream/last-built`
3. `git log` между предыдущим и текущим коммитом
4. Категоризация по префиксам сообщений
5. Обновляет `.upstream/last-built` для следующей сборки

Первый changelog — от коммита `a900068de` (8 июня 2026).

## Мониторинг upstream

`watch-upstream.yml` — ежедневно в 08:05 MSK (запускается dispatcher'ом с `main`):
1. Берёт baseline из `.upstream/last-built` (реально собранное), `.upstream/checked` — верхняя граница осмотренного
2. **Meaningful** — изменения в libs/user/linux-3.4.x/boards/toolchain
3. **Urgency** — при CVE/security — сборка в тот же день
4. В понедельник (или при urgency): если есть pending и сборка уже не идёт — диспатчит `build.yml` на `beta`

### `pending` — производное состояние

`.upstream/pending` пересчитывается от `last-built` **каждый запуск**, а не дописывается
накопительно. Это исключает «фантомные» SHA: записи, которых уже нет в диапазоне
`last-built..upstream`, но которые остались от прежних прогонов.

### Защита от тихого пропуска

Базовая точка обязана присутствовать в локальной истории. Если её там нет (мелкий
`fetch`), история углубляется; если и это не помогло — шаг падает с явной ошибкой,
вместо того чтобы молча решить «изменений нет».

### Защита от двойного диспатча

Перед запуском сборки проверяется, нет ли уже `in_progress`/`queued` запусков
`build.yml`. Сборка идёт дольше интервала между проверками, а `last-built`
сдвигается только по её завершении — без этой проверки возможны дубли.

### Ручная проверка авторежима

Запустить проверку вне понедельника, не дожидаясь cron:

```bash
gh workflow run watch-upstream.yml --repo <owner>/<repo> --ref beta -f force=true
```

`force=true` игнорирует правило понедельника. `model=<name>` — собрать одну модель
вместо всех.

## Версионирование

Теги: `vYYYY.MM.DD`. При urgency: `vYYYY.MM.DD-urgency`.

## Структура

```
.github/workflows/
├── build.yml                  — сборка + finalize (Release, changelog)
├── build-one.yml              — reusable: сборка одной модели
├── build-image.yml            — self-hosted образ сборки (GHCR)
├── watch-upstream.yml         — мониторинг nilabsent/padavan-ng
└── close-inappropriate-pr.yml — защита от PR с build.config

main/.github/workflows/
└── dispatch-watch.yml         — cron-шим: запускает watch-upstream на beta
                                 (нужен, пока default branch = main)

.upstream/
├── checked                    — последний проверенный SHA
├── pending                    — meaningful SHA от last-built (пересчёт каждый запуск)
└── last-built                 — предыдущий коммит для changelog
configs/
├── rm-ac2100.config
├── mi-3.config
└── mi-r3gv2.config
docs/
├── FAQ.md                     — добавление моделей
├── README.md / ru/README.md  — оригинальные README (en/ru)
└── misc/                      — скриншоты
variables                      — репозиторий, тулчейн, темы
```

## Добавление новой модели

См. [docs/FAQ.md](docs/FAQ.md).

## Темы

Дефолтные темы Padavan. Персонализация — через WebUI.