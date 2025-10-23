import csv
from pathlib import Path
from typing import Iterable

DRUMS = ["DRUM-001", "DRUM-002", "DRUM-003", "DRUM-004", "DRUM-005"]
CSV_HEADER = ["position", "drum_code", "length"]


def write_csv(path: Path, rows: Iterable[dict]) -> None:
    if path.exists():
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in CSV_HEADER})


def generate_csvs():
    out_dir = Path.cwd().parent / "data"

    # 1) Валидный набор
    valid_rows = [
        {"position": 1, "drum_code": DRUMS[0], "length": 250},
        {"position": 2, "drum_code": DRUMS[1], "length": 300},
        {"position": 3, "drum_code": DRUMS[2], "length": 150.5},
        {"position": 4, "drum_code": DRUMS[3], "length": 100},
        {"position": 5, "drum_code": DRUMS[4], "length": 50},
    ]
    write_csv(out_dir / "batch_valid.csv", valid_rows)

    # 2) Дубли позиций
    dup_pos_rows = [
        {"position": 1, "drum_code": DRUMS[0], "length": 200},
        {"position": 1, "drum_code": DRUMS[1], "length": 200},  # дубль позиции
        {"position": 2, "drum_code": DRUMS[2], "length": 100},
        {"position": 3, "drum_code": DRUMS[3], "length": 120},
    ]
    write_csv(out_dir / "batch_dup_positions.csv", dup_pos_rows)

    # 3) Отсутствующие позиции
    missing_pos_rows = [
        {"position": "", "drum_code": DRUMS[0], "length": 200},  # отсутствует
        {"position": "   ", "drum_code": DRUMS[1], "length": 180},  # пробелы
        {"position": None, "drum_code": DRUMS[2], "length": 150},  # пустая ячейка
        {"position": 3, "drum_code": DRUMS[3], "length": 120},
    ]
    write_csv(out_dir / "batch_missing_positions.csv", missing_pos_rows)

    # 4) Некорректные длины
    invalid_len_rows = [
        {"position": 1, "drum_code": DRUMS[0], "length": 0},  # ноль
        {"position": 2, "drum_code": DRUMS[1], "length": -5},  # отрицательное
        {"position": 3, "drum_code": DRUMS[2], "length": "text"},  # не число
        {"position": 4, "drum_code": DRUMS[3], "length": 5000000},  # слишком большое
        {"position": 5, "drum_code": DRUMS[4], "length": "12,5"},  # запятая как разделитель
    ]
    write_csv(out_dir / "batch_invalid_lengths.csv", invalid_len_rows)

    # 5) Смешанные ошибки
    mixed_rows = [
        {"position": 1, "drum_code": DRUMS[0], "length": 100},
        {"position": 1, "drum_code": DRUMS[0], "length": 90},  # дубль позиции
        {"position": 2, "drum_code": "", "length": 120},  # пустой барабан
        {"position": 3, "drum_code": DRUMS[2], "length": ""},  # пустая длина
        {"position": 4, "drum_code": DRUMS[3], "length": -1},  # отрицательная длина
        {"position": 5, "drum_code": DRUMS[3], "length": 50},
    ]
    write_csv(out_dir / "batch_mixed.csv", mixed_rows)

    for name in [
        "batch_valid.csv",
        "batch_dup_positions.csv",
        "batch_missing_positions.csv",
        "batch_invalid_lengths.csv",
        "batch_mixed.csv",
    ]:
        print(f"generating {name}")


if __name__ == "__main__":
    generate_csvs()
