# padavan-builder-workflow

Автоматическая сборка прошивок [Padavan (nilabsent/padavan-ng)](https://github.com/nilabsent/padavan-ng) для нескольких моделей роутеров.

Форк [shvchk/padavan-builder-workflow](https://github.com/shvchk/padavan-builder-workflow) — функционал расширен: несколько моделей, мониторинг upstream, автоматический changelog с категоризацией коммитов.

> Форк создан для автоматизации собственных сборок. Changelog и прошивки предоставляются as-is.

## Возможности

- **Независимые сборки** — отдельные job (rm-ac2100, mi-3, mi-r3gv2) под каждую модель, со своим `.config` и проверкой partition limit. Возможность запускать сборку выбранной модели или всех разом.
- **Единый Release** — после всех успешных сборок: один GitHub Release со всеми прошивками, конфигами и общим changelog
- **Автоматический changelog** — категоризация upstream-коммитов (Добавлено/Исправлено/Обновлено/Удалено/Прочее)
- **Мониторинг upstream** — ежедневная проверка новых коммитов с фильтрацией meaningful/trivial
- **Еженедельный релиз** — авто-тег в понедельник при наличии meaningful изменений
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

| Событие | Действие | Когда |
|---|---|---|
| `workflow_dispatch` | Ручной запуск | В любой момент |
| `push` на тег `v*` | Полная сборка + Release | Авто — от watch-upstream |
| `schedule` (пн 06:30 UTC) | Еженедельная сборка | Каждый понедельник |

## Как работает changelog

После успешной сборки job `finalize`:
1. Клонирует nilabsent/padavan-ng
2. Читает предыдущий коммит из `.upstream/last-built`
3. `git log` между предыдущим и текущим коммитом
4. Категоризация по префиксам сообщений
5. Обновляет `.upstream/last-built` для следующей сборки

Первый changelog — от коммита `a900068de` (8 июня 2026).

## Мониторинг upstream

`watch-upstream.yml` — ежедневно в 08:05 MSK:
1. Сверяет `.upstream/checked` с HEAD nilabsent
2. **Meaningful** — изменения в libs/user/linux-3.4.x/boards/toolchain
3. **Urgency** — при CVE/security — сборка в тот же день
4. В понедельник: если есть pending — создаёт тег `vYYYY.MM.DD`

## Версионирование

Теги: `vYYYY.MM.DD`. При urgency: `vYYYY.MM.DD-urgency`.

## Структура

```
.github/workflows/
├── build.yml                  — сборка + finalize (Release, changelog)
├── build-one.yml              — reusable: сборка одной модели
├── watch-upstream.yml         — мониторинг nilabsent/padavan-ng
└── close-inappropriate-pr.yml — защита от PR с build.config
.upstream/
├── checked                    — последний проверенный SHA
├── pending                    — накопленные meaningful SHA
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