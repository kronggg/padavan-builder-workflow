# FAQ — Добавление новой модели

## Как добавить новый роутер в сборку?

1. Найди шаблон конфига для своей модели:
   - В upstream: `trunk/configs/templates/VENDOR/MODEL.config`
   - Скопируй содержимое в `configs/` в форке с уникальным именем

2. Добавь файл конфига в `configs/`:
   ```
   configs/my-model.config
   ```

3. Убедись, что в `variables` указан правильный upstream:
   ```
   PADAVAN_REPO="https://github.com/nilabsent/padavan-ng.git"
   ```

4. Обнови матрицу в `.github/workflows/build.yml`:
   ```yaml
   strategy:
     matrix:
       model: [rm-ac2100, mi-3, mi-r3gv2, my-model]
   ```

5. **Важно: проверь размер firmware partition.** Найди файл `trunk/configs/boards/VENDOR/PRODUCT_ID/partitions.config` в upstream и убедись, что прошивка влезет.

6. Запусти сборку через `workflow_dispatch` для проверки.

## Как работает матрица?

Каждый job в матрице запускает независимую сборку со своим `.config` файлом. Все модели собираются параллельно.

## Выбор модели при ручном запуске

При `workflow_dispatch` можно выбрать:
- `all` — собрать все модели из матрицы
- конкретное имя (например `rm-ac2100`) — собрать только одну

## Ограничения

- Имя файла конфига должно совпадать с именем в матрице
- Максимальный размер прошивки определяется в `partitions.config` для каждой платы
- Не добавляй модели, которые не поддерживаются upstream (nilabsent/padavan-ng)
