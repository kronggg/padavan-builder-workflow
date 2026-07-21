# padavan-builder-workflow

Автоматическая сборка прошивок [Padavan (nilabsent/padavan-ng)](https://github.com/nilabsent/padavan-ng) для нескольких моделей роутеров с мониторингом изменений upstream.

Форк от [shvchk/padavan-builder-workflow](https://github.com/shvchk/padavan-builder-workflow). Оригинальный функционал расширен: добавлена матричная сборка, мониторинг upstream, автоматические релизы и фильтрация изменений.

## Возможности

- **Матричная сборка** — параллельная сборка всех моделей в одном запуске
- **Мониторинг upstream** — ежедневная проверка новых коммитов в nilabsent/padavan-ng с фильтрацией meaningful/trivial
- **Еженедельный релиз** — автоматическая сборка в понедельник при наличии meaningful изменений за неделю
- **Urgency-сборка** — экстренный запуск при CVE/security-фиксах в upstream
- **Ручной запуск** — workflow_dispatch с выбором конкретной модели или всех сразу
- **GitHub Releases** — архив на каждую модель (прошивка + .config + changelog)
- **Умный фильтр** — сборка только при изменениях, влияющих на функционал (libs/user/boards/toolchain)
- **Автоматическая проверка размера** — каждая модель проверяется на лимит firmware partition
- **Валидация partitions.config** — при добавлении модели конфиг сверяется с upstream

## Модели

| Модель | Конфиг | SoC | Flash | Firmware |
|---|---|---|---|---|
| Xiaomi RM-AC2100 | `configs/rm-ac2100.config` | MT7621 | 128 MB NAND | 20 MB |
| Xiaomi Mi Router 3 | `configs/mi-3.config` | MT7620 | 128 MB NAND | 16 MB |
| Xiaomi Mi Router 4A Gigabit (R4A/R3Gv2) | `configs/mi-r3gv2.config` | MT7621 | 16 MB SPI | 15.4 MB |

## Триггеры сборки

| Событие | Действие |
|---|---|
| `workflow_dispatch` | Ручной запуск (выбор модели или all) |
| `push` на тег `v*` | Релизная сборка + GitHub Release |
| watch-upstream (ежедневно, пн) | Мониторинг изменений nilabsent; авто-тег при meaningful |
| urgency (CVE/security) | Экстренная сборка вне недельного графика |

## Мониторинг upstream

watch-upstream ежедневно проверяет новые коммиты в nilabsent/padavan-ng.
Сборка запускается **только при meaningful изменениях** (обновление openssl, curl, драйверов, ядра, тулчейна).
Изменения документации, переводов и косметики — игнорируются.

## Версионирование

Теги: `vYYYY.MM.DD`. Одна сборка в неделю (понедельник). При urgency — отдельный тег в тот же день.

## Релизный механизм

GitHub Release с архивами на каждую модель:
- Прошивка (`.trx`)
- Конфиг сборки (`.config`)
- Changelog изменений (`CHANGELOG.md`)

Уведомление — через GitHub Watch → Releases.

## Структура репозитория

```
.github/workflows/
├── build.yml              — матричная сборка + релиз
└── watch-upstream.yml     — ежедневный мониторинг upstream
.upstream/
├── checked                — последний проверенный SHA
└── pending                — накопленные meaningful SHA
configs/
├── rm-ac2100.config
├── mi-3.config
└── mi-r3gv2.config
variables                  — переменные сборки (репозиторий, тулчейн, темы)
docs/
└── FAQ.md                 — инструкция по добавлению моделей
```

## Добавление новой модели

См. [docs/FAQ.md](docs/FAQ.md).

## Оригинальный репозиторий

Оригинальный форк: [shvchk/padavan-builder-workflow](https://github.com/shvchk/padavan-builder-workflow).  
README на английском и русском: [docs/README.md](docs/README.md) и [docs/ru/README.md](docs/ru/README.md).

## Темы

Используются дефолтные темы Padavan. Персонализация доступна в WebUI прошивки.
