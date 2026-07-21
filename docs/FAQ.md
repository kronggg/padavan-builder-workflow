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

4. Добавь job в `.github/workflows/build.yml`:
   ```yaml
     my-model:
       if: ${{ github.event_name != 'workflow_dispatch' || github.event.inputs.model == 'all' || github.event.inputs.model == 'my-model' }}
       uses: ./.github/workflows/build-one.yml
       with:
         model: my-model
   ```

5. **Автоматическая проверка размера.** В build.yml есть шаг, который сверяет размер прошивки с `trunk/configs/boards/VENDOR/PRODUCT_ID/partitions.config` в upstream. Если конфиг превышает лимит — сборка упадёт с ошибкой. Тебе не нужно помнить точные цифры — workflow сам проверит.

6. Запусти сборку через `workflow_dispatch` для проверки.

## Как работает автоматическая проверка partitions.config?

При сборке workflow выполняет следующие шаги:
1. Определяет VENDOR и PRODUCT_ID из твоего `.config` файла
2. Ищет файл `trunk/configs/boards/VENDOR/PRODUCT_ID/partitions.config` в upstream
3. Извлекает значение `mtd_firmware_size` (или `mtd_firmware_start` + `mtd_firmware_end`)
4. Сравнивает размер готовой прошивки с лимитом
5. Если прошивка превышает лимит — сборка падает с понятной ошибкой

Это значит, что при добавлении новой модели:
- Ты не обязан вручную искать partitions.config — workflow сделает это сам
- Если твой конфиг слишком большой, сборка упадёт, и ты увидишь точную цифру превышения
- Можешь итеративно отключать опции в конфиге, пока сборка не пройдёт

## Как работает сборка?

Каждый job запускает независимую сборку со своим `.config` файлом.

## Выбор модели при ручном запуске

При `workflow_dispatch` можно выбрать:
- `all` — собрать все модели
- конкретное имя (например `rm-ac2100`) — собрать только одну

## Ограничения

- Имя файла конфига должно совпадать с именем модели в build.yml
- Максимальный размер прошивки определяется в `partitions.config` для каждой платы (проверяется автоматически)
- Не добавляй модели, которые не поддерживаются upstream (nilabsent/padavan-ng)
