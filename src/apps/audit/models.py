from decimal import Decimal

from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel


class ImportLog(TimeStampedModel):
    batch = models.ForeignKey(
        "inventory.Batch",
        on_delete=models.CASCADE,
        related_name="imports",
        verbose_name = "Партия"
    )
    file_name = models.CharField(
        verbose_name="Имя файла",
        max_length=255,
        blank=True,
        default=""
    )
    file_sha256 = models.CharField(
        verbose_name="SHA256",
        max_length=64
    )
    total = models.PositiveIntegerField(
        verbose_name="Всего строк",
        default=0
    )
    inserted = models.PositiveIntegerField(
        verbose_name="Вставлено",
        default=0
    )
    duplicates_in_file = models.PositiveIntegerField(
        verbose_name="Дубли в файле",
        default=0
    )
    duplicates_in_db = models.PositiveIntegerField(
        verbose_name="Дубли в БД",
        default=0
    )
    invalid_rows = models.PositiveIntegerField(
        verbose_name="Некорректных строк",
        default=0
    )
    duration_sec = models.DecimalField(
        verbose_name="Длительность, с",
        max_digits=8,
        decimal_places=3,
        default=Decimal("0.000")
    )
    errors = models.JSONField(
        verbose_name="Ошибки",
        default=list,
        blank=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["batch"]),
            models.Index(fields=["file_sha256"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(duration_sec__gte=0), name="ck_importlog_duration_nonneg"
            ),
        ]
        verbose_name = "Импорт"
        verbose_name_plural = "Импорты"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.file_sha256:
            self.file_sha256 = self.file_sha256.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Import[{self.batch} | {self.file_name}]"
