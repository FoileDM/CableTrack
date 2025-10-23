# CableTrack — учёт барабанов кабеля

> Прототип для учёта барабанов по местам хранения: импорт партий из CSV, исключение дублей, валидация длины и просмотр
> загруженных данных через Django Admin.

## Docker Compose

```bash
# 1) Распакуйте архив и перейдите в корень проекта
cp .env.example .env

# 2) Запустите сервисы
docker compose up -d --build

# 3) (Опционально) загрузите демо-справочники: склады, модели кабеля, барабаны
docker compose exec web python manage.py basic_data

# 4) Зайдите в админку
#   http://localhost:8000/admin
#   Пользователь берётся из .env:
#   DJANGO_SUPERUSER_USERNAME=admin
#   DJANGO_SUPERUSER_PASSWORD=admin
```

## Как проверить импорт из CSV

1. Войдите в **Django Admin** → *Inventory / Batches* → **Add** — вы попадёте на форму «Импорт CSV в партию».
2. Укажите:
    - **Номер партии** (например, `PO-2025-001`).
    - **Склад** (например, `S-1`).
    - **CSV-файл** (пример: `batch_valid.csv` сгенерированный скриптом `data/generate_csv.py`).
3. Нажмите **Импортировать** — по завершении вы увидите сообщение с итогами. Будет создана запись партии и **BatchItem**
   ’ы; подробности попадут в **Audit / Imports**.
4. Повторный импорт того же файла в ту же партию не создаёт дублей позиций: строки, которые уже существуют (см. правила
   ниже), будут пропущены и посчитаны как дубликаты.

### Формат CSV

CSV **с заголовком** в кодировке UTF‑8, разделитель — запятая:

```csv
position,drum_code,length
1,DRUM-001,250
2,DRUM-002,300
3,DRUM-003,150.5
```

- `position` — целое ≥ 1 (номер позиции в партии, `number_in_batch`).
- `drum_code` — код барабана (регистр не важен, пробелы обрезаются).
- `length` — десятичное число в метрах (точка как разделитель), > 0 и ≤ первичной длины барабана.

### Правила дедупликации и валидации при импорте

- **Дубликаты в файле**: строки с повторяющимся `position` считаются дублями и **не вставляются** (метрика
  `duplicates_in_file`).
- **Дубликаты в БД**: если в выбранной партии уже существует элемент с тем же барабаном (`batch + drum`) или той же
  позицией (`batch + number_in_batch`), строка **не вставляется** (метрика `duplicates_in_db`).
- **Валидация длины**: `0 < length ≤ drum.initial_length_m`. Также на уровне схемы заданы `CheckConstraint` и
  `Min/MaxValueValidator`.
- Все итоги импорта (total, inserted, dups, invalid, duration, список ошибок, sha256 файла) записываются в **Audit →
  Imports**.

## Предустановленные пути и endpoints

- **Admin**: `http://localhost:8000/admin`
- **OpenAPI/Swagger**: `http://localhost:8000/api/docs` (генерируется `drf-spectacular`).

## Локальный запуск (без Docker)

Требования: Python 3.12, Poetry 2.2.x, PostgreSQL 16.

```bash
# Установите зависимости
poetry install

# Переменные окружения
cp .env.example .env

# Миграции и запуск
poetry run python src/manage.py migrate
poetry run python src/manage.py collectstatic --noinput
poetry run python src/manage.py runserver 0.0.0.0:8000

# Демо-справочники
poetry run python src/manage.py basic_data
```

## Архитектура проекта (вкратце)

- **Django 5.2**, **DRF 3.16**, **PostgreSQL 16**, **docker-compose**, **Poetry**.
- Приложения:
    - `apps.storage` — склады (Storage).
    - `apps.catalog` — справочник кабельных моделей (CableModel) и барабанов (Drum).
    - `apps.inventory` — партии (Batch) и позиции в партиях (BatchItem), импорт CSV.
    - `apps.audit` — логирование импортов (ImportLog).
    - `apps.core` — базовые абстракции
