import csv
from pathlib import Path
from typing import Iterable, List, Dict, Set, Union

Number = Union[int, float]
Row = Dict[str, object]

DRUMS = ["DRUM-001", "DRUM-002", "DRUM-003", "DRUM-004", "DRUM-005"]
CSV_HEADER = ["position", "drum_code", "length"]
TARGET_ROWS = 50


def write_csv(path: Path, rows: Iterable[Row]) -> None:
    if path.exists():
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in CSV_HEADER})


def _numeric_positions(rows: Iterable[Row]) -> Set[int]:
    used: Set[int] = set()
    for r in rows:
        pos = r.get("position")
        if isinstance(pos, (int, float)):
            try:
                used.add(int(pos))
            except (TypeError, ValueError):
                pass
    return used


def _next_drum_code(index: int) -> str:
    return DRUMS[index % len(DRUMS)]


def _build_valid_rows(
        current_rows: List[Row],
        target_total: int = TARGET_ROWS,
        start_pos: int = 1,
) -> List[Row]:
    rows: List[Row] = []
    used_positions = _numeric_positions(current_rows)
    pos = max(start_pos, 1)

    # Смещение по drum_code, чтобы распределение было стабильным относительно уже имеющихся строк
    seed_count = sum(1 for r in current_rows if r.get("drum_code") in DRUMS)

    while len(current_rows) + len(rows) < target_total:
        while pos in used_positions:
            pos += 1

        code = _next_drum_code(seed_count + len(rows))
        # Детерминированная, "разумная" длина
        base = 100 + ((pos - 1) % 10) * 50  # 100..550
        length: Number = float(base) + 0.5 if pos % 3 == 0 else base  # часть значений float

        rows.append({"position": pos, "drum_code": code, "length": length})
        used_positions.add(pos)
        pos += 1

    return rows


def generate_csvs() -> None:
    out_dir = Path(__file__).resolve().parent

    # 1) Валидный набор
    valid_rows: List[Row] = _build_valid_rows(current_rows=[], target_total=TARGET_ROWS)
    write_csv(out_dir / "batch_valid.csv", valid_rows)

    # 2) Дубли позиций
    dup_pos_seed: List[Row] = [
        {"position": 1, "drum_code": DRUMS[0], "length": 200},
        {"position": 1, "drum_code": DRUMS[1], "length": 200},  # дубль позиции
        {"position": 2, "drum_code": DRUMS[2], "length": 100},
        {"position": 3, "drum_code": DRUMS[3], "length": 120},
    ]
    dup_pos_rows = dup_pos_seed + _build_valid_rows(dup_pos_seed, target_total=TARGET_ROWS, start_pos=1)
    write_csv(out_dir / "batch_dup_positions.csv", dup_pos_rows)

    # 3) Отсутствующие позиции
    missing_pos_seed: List[Row] = [
        {"position": "", "drum_code": DRUMS[0], "length": 200},  # отсутствует
        {"position": "   ", "drum_code": DRUMS[1], "length": 180},  # пробелы
        {"position": None, "drum_code": DRUMS[2], "length": 150},  # пустая ячейка
        {"position": 3, "drum_code": DRUMS[3], "length": 120},
    ]
    missing_pos_rows = missing_pos_seed + _build_valid_rows(missing_pos_seed, target_total=TARGET_ROWS, start_pos=1)
    write_csv(out_dir / "batch_missing_positions.csv", missing_pos_rows)

    # 4) Некорректные длины
    invalid_len_seed: List[Row] = [
        {"position": 1, "drum_code": DRUMS[0], "length": 0},  # ноль
        {"position": 2, "drum_code": DRUMS[1], "length": -5},  # отрицательное
        {"position": 3, "drum_code": DRUMS[2], "length": "text"},  # не число
        {"position": 4, "drum_code": DRUMS[3], "length": 5000000},  # слишком большое
        {"position": 5, "drum_code": DRUMS[4], "length": "12,5"},  # запятая как разделитель
    ]
    invalid_len_rows = invalid_len_seed + _build_valid_rows(invalid_len_seed, target_total=TARGET_ROWS, start_pos=1)
    write_csv(out_dir / "batch_invalid_lengths.csv", invalid_len_rows)

    # 5) Смешанные ошибки
    mixed_seed: List[Row] = [
        {"position": 1, "drum_code": DRUMS[0], "length": 100},
        {"position": 1, "drum_code": DRUMS[0], "length": 90},  # дубль позиции
        {"position": 2, "drum_code": "", "length": 120},  # пустой drum_code
        {"position": 3, "drum_code": DRUMS[2], "length": ""},  # пустая длина
        {"position": 4, "drum_code": DRUMS[3], "length": -1},  # отрицательная длина
        {"position": 5, "drum_code": DRUMS[3], "length": 50},
    ]
    mixed_rows = mixed_seed + _build_valid_rows(mixed_seed, target_total=TARGET_ROWS, start_pos=1)
    write_csv(out_dir / "batch_mixed.csv", mixed_rows)

    for name in [
        "batch_valid.csv",
        "batch_dup_positions.csv",
        "batch_missing_positions.csv",
        "batch_invalid_lengths.csv",
        "batch_mixed.csv",
    ]:
        print(f"generated {name} at {out_dir / name}")


if __name__ == "__main__":
    generate_csvs()
