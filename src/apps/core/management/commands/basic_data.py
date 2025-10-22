from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import CableModel, Drum
from apps.storage.models import Storage

STORAGES = [
    {"code": "S-1", "name": "Склад 1"},
    {"code": "S-2", "name": "Склад 2"},
    {"code": "S-3", "name": "Склад 3"},
]

CABLE_MODELS = [
    {"code": "CM-OPT-01", "name": "Оптика 24F", "min_length_m": Decimal("10"), "max_length_m": Decimal("1200")},
    {"code": "CM-OPT-02", "name": "Оптика 12F", "min_length_m": Decimal("10"), "max_length_m": Decimal("900")},
    {"code": "CM-OPT-03", "name": "Оптика 8F", "min_length_m": Decimal("10"), "max_length_m": Decimal("700")},
    {"code": "CM-OPT-04", "name": "Оптика 4F", "min_length_m": Decimal("10"), "max_length_m": Decimal("300")},
]

DRUMS = [
    {"code": "DRUM-001", "cable_model_code": "CM-OPT-01", "initial_length_m": Decimal("1000")},
    {"code": "DRUM-002", "cable_model_code": "CM-OPT-02", "initial_length_m": Decimal("800")},
    {"code": "DRUM-003", "cable_model_code": "CM-OPT-03", "initial_length_m": Decimal("600")},
    {"code": "DRUM-004", "cable_model_code": "CM-OPT-03", "initial_length_m": Decimal("400")},
    {"code": "DRUM-005", "cable_model_code": "CM-OPT-04", "initial_length_m": Decimal("200")},
]


class Command(BaseCommand):
    help = "Создаёт базовые записи Storage, CableModel и Drum. Повторный запуск ничего не меняет."

    @transaction.atomic
    def handle(self, *args, **options):
        created, existed = {"storage": 0, "cablemodel": 0, "drum": 0}, {"storage": 0, "cablemodel": 0, "drum": 0}

        # 1) Storage
        self.stdout.write("→ Storage:")
        for s in STORAGES:
            obj, is_created = Storage.objects.get_or_create(code=s["code"], defaults={"name": s["name"]})
            if is_created:
                created["storage"] += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ создан {obj.code} ({obj.name})"))
            else:
                existed["storage"] += 1
                if obj.name != s["name"]:
                    self.stdout.write(self.style.WARNING(f"  • уже существует {obj.code} (текущее имя: '{obj.name}')"))
                else:
                    self.stdout.write(f"  • уже существует {obj.code}")

        # 2) CableModel
        self.stdout.write("→ CableModel:")
        cm_by_code = {}
        for cm in CABLE_MODELS:
            obj, is_created = CableModel.objects.get_or_create(
                code=cm["code"],
                defaults={"name": cm["name"], "min_length_m": cm["min_length_m"], "max_length_m": cm["max_length_m"]},
            )
            cm_by_code[obj.code] = obj
            if is_created:
                created["cablemodel"] += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ создан {obj.code} [{obj.min_length_m}..{obj.max_length_m}]"))
            else:
                existed["cablemodel"] += 1
                self.stdout.write(f"  • уже существует {obj.code}")

        # 3) Drum
        self.stdout.write("→ Drum:")
        for d in DRUMS:
            cm = cm_by_code.get(d["cable_model_code"]) or CableModel.objects.get(code=d["cable_model_code"])
            obj, is_created = Drum.objects.get_or_create(
                code=d["code"],
                defaults={"cable_model": cm, "initial_length_m": d["initial_length_m"]},
            )
            if is_created:
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ создан {obj.code} → {cm.code} ({obj.initial_length_m} м)"
                ))
                created["drum"] += 1
            else:
                self.stdout.write(f"  • уже существует {obj.code}")
                existed["drum"] += 1

        self.stdout.write(self.style.SUCCESS(
            "Готово.\n"
            f"Storage: создано {created['storage']}, уже было {existed['storage']}\n"
            f"CableModel: создано {created['cablemodel']}, уже было {existed['cablemodel']}\n"
            f"Drum: создано {created['drum']}, уже было {existed['drum']}"
        ))
