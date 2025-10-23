import csv
import hashlib
import io
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from django.db import transaction

from apps.audit.models import ImportLog
from apps.catalog.models import Drum
from apps.inventory.models import Batch, BatchItem
from apps.storage.models import Storage


@dataclass(frozen=True)
class ImportResult:
    total: int
    inserted: int
    duplicates_in_file: int
    duplicates_in_db: int
    invalid_rows: int
    errors: list[str]
    batch_id: int | None = None
    file_name: str | None = None
    file_sha256: str | None = None


def _b(value) -> bytes:
    if value is None:
        return b""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if hasattr(value, "read"):
        return value.read()
    return bytes(value)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _norm_code(v: str | None) -> str:
    return (v or "").strip().upper()


def _parse_length(val: str, *, line_no: int, errors: list[str]) -> Decimal | None:
    s = (val or "").strip()
    if not s:
        errors.append(f"Строка {line_no}: не задана длина.")
        return None
    s = s.replace(",", ".")
    try:
        d = Decimal(s)
    except InvalidOperation:
        errors.append(f"Строка {line_no}: некорректная длина '{val}'.")
        return None
    if d <= 0:
        errors.append(f"Строка {line_no}: длина должна быть > 0 (получено {d}).")
        return None
    if d > Decimal("1000000"):
        errors.append(f"Строка {line_no}: длина слишком большая ({d}).")
        return None
    return d.quantize(Decimal("0.01"))


def import_batch_from_csv(*, file, batch_number: str, storage) -> ImportResult:
    """
    Импорт CSV формата: position, drum_code, length

    Изменения по требованиям:
    - position ОБЯЗАТЕЛЕН, положительное целое; если пустой/битый — строка помечается как невалидная и пропускается.
    - Если >50% строк файла с ошибками (валидация/дубли в файле) — создаём ImportLog (с ошибкой) и бросаем исключение.
    - Всегда создаём новый ImportLog. Если (batch+sha256) уже встречались — пишем новый лог с ошибкой «файл уже обработан» и бросаем исключение.
    - drum_code должен существовать в каталоге; иначе строка — ошибка и пропуск.
    - Длина > 0 и ≤ стандартной длины барабана (initial_length_m, если задана).
    - Позиции не должны повторяться (ни в файле, ни в БД).
    """
    t0 = time.perf_counter()
    content = _b(file)
    file_name = getattr(file, "name", "uploaded.csv")
    file_sha = _sha256(content)

    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))
    headers = {h.strip().lower() for h in (reader.fieldnames or [])}
    required = {"drum_code", "length", "position"}

    # Партия и склад
    batch, _ = Batch.objects.get_or_create(number=(batch_number or "").strip())
    storage_obj = storage
    if isinstance(storage_obj, str):
        storage_obj, _ = Storage.objects.get_or_create(code=_norm_code(storage_obj))

    rows = list(reader)
    total = len(rows)

    # Нет нужных колонок в файле
    if not required.issubset(headers):
        missing = ", ".join(sorted(required - headers))
        _ = ImportLog.objects.create(
            batch=batch_number,
            file_name=file_name or "",
            file_sha256=file_sha,
            total=0,
            inserted=0,
            duplicates_in_file=0,
            duplicates_in_db=0,
            invalid_rows=0,
            duration_sec=Decimal("0.000"),
            errors=[f"Отсутствуют обязательные колонки: {missing}"],
        )
        raise ValueError(f"Отсутствуют обязательные колонки: {missing}")

    # Нет данных в файле
    if total == 0:
        _ = ImportLog.objects.create(
            batch=batch,
            file_name=file_name or "",
            file_sha256=file_sha,
            total=0,
            inserted=0,
            duplicates_in_file=0,
            duplicates_in_db=0,
            invalid_rows=0,
            duration_sec=Decimal("0.000"),
            errors=["Файл не содержит данных."],
        )
        raise ValueError("Файл не содержит данных.")

    # Повторная обработка файла с тем же sha для этой партии
    if ImportLog.objects.filter(batch=batch, file_sha256=file_sha).exists():
        _ = ImportLog.objects.create(
            batch=batch,
            file_name=file_name or "",
            file_sha256=file_sha,
            total=total,
            inserted=0,
            duplicates_in_file=0,
            duplicates_in_db=total,
            invalid_rows=0,
            duration_sec=Decimal("0.000"),
            errors=["Файл с такой контрольной суммой уже был обработан для этой партии."],
        )
        raise ValueError("Файл уже был обработан для этой партии.")

    errors: list[str] = []
    duplicates_in_file = 0
    duplicates_in_db = 0
    invalid_rows = 0

    # Текущее состояние БД по партии
    existing_items = BatchItem.objects.filter(batch=batch).select_related("drum")
    existing_positions = set(existing_items.values_list("number_in_batch", flat=True))

    used_positions_in_file: set[int] = set()
    used_drums_in_file: set[str] = set()

    drum_codes = []
    norm_rows = []
    for idx, r in enumerate(rows, start=2):
        drum_code = _norm_code(r.get("drum_code"))
        if not drum_code:
            invalid_rows += 1
            errors.append(f"Строка {idx}: пустой drum_code.")
            continue
        length = _parse_length(r.get("length"), line_no=idx, errors=errors)
        if length is None:
            invalid_rows += 1
            continue

        pos_val = (r.get("position") or "").strip()
        if not pos_val:
            invalid_rows += 1
            errors.append(f"Строка {idx}: пустая position — строка пропущена.")
            continue
        try:
            pos = int(pos_val)
            if pos <= 0:
                raise ValueError
        except Exception:
            invalid_rows += 1
            errors.append(f"Строка {idx}: некорректная position '{pos_val}' (ожидается положительное целое).")
            continue

        norm_rows.append((idx, drum_code, length, pos))
        drum_codes.append(drum_code)

    drums_by_code = {d.code: d for d in Drum.objects.filter(code__in=set(drum_codes))}

    # Вторая фаза нормализации
    to_create: list[BatchItem] = []
    for (idx, drum_code, length, pos) in norm_rows:
        drum = drums_by_code.get(drum_code)
        if not drum:
            invalid_rows += 1
            errors.append(f"Строка {idx}: барабан '{drum_code}' не найден в каталоге.")
            continue

        # Длина > первичной длины барабана
        init_len = getattr(drum, "initial_length_m", None)
        if init_len is not None and length > init_len:
            invalid_rows += 1
            errors.append(
                f"Строка {idx}: длина {length} м превышает первичную длину барабана {init_len} м."
            )
            continue

        # Дубли позиций в файле/БД
        if pos in used_positions_in_file:
            duplicates_in_file += 1
            errors.append(f"Строка {idx}: дублирование position {pos} в файле.")
            continue
        if pos in existing_positions:
            duplicates_in_db += 1
            continue

        used_drums_in_file.add(drum_code)
        used_positions_in_file.add(pos)

        to_create.append(
            BatchItem(
                batch=batch,
                drum=drum,
                storage_location=storage_obj,
                number_in_batch=pos,
                length_m=length,
            )
        )

    # Порог 50% ошибок
    file_quality_errors = invalid_rows + duplicates_in_file
    error_ratio = (file_quality_errors / total) if total > 0 else 1.0
    duration = Decimal(str(round(time.perf_counter() - t0, 3)))

    if error_ratio > 0.5:
        ImportLog.objects.create(
            batch=batch,
            file_name=file_name or "",
            file_sha256=file_sha,
            total=total,
            inserted=0,
            duplicates_in_file=duplicates_in_file,
            duplicates_in_db=duplicates_in_db,
            invalid_rows=invalid_rows,
            duration_sec=duration,
            errors=(errors[:100] + [f"Порог >50% ошибок ({file_quality_errors}/{total}) — загрузка отменена."])[:120],
        )
        raise ValueError("В файле более 50% ошибок. Загрузка отменена.")

    with transaction.atomic():
        created = BatchItem.objects.bulk_create(to_create, ignore_conflicts=True)
        inserted = len(created)

    ImportLog.objects.create(
        batch=batch,
        file_name=file_name or "",
        file_sha256=file_sha,
        total=total,
        inserted=inserted,
        duplicates_in_file=duplicates_in_file,
        duplicates_in_db=duplicates_in_db,
        invalid_rows=invalid_rows,
        duration_sec=duration,
        errors=errors[:100],
    )

    return ImportResult(
        total=total,
        inserted=inserted,
        duplicates_in_file=duplicates_in_file,
        duplicates_in_db=duplicates_in_db,
        invalid_rows=invalid_rows,
        errors=errors,
        batch_id=batch.id,
        file_name=file_name,
        file_sha256=file_sha,
    )
