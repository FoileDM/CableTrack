from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel


class Batch(TimeStampedModel):
    number = models.CharField(
        verbose_name="Номер партии",
        max_length=64,
        unique=True
    )

    class Meta:
        verbose_name = "Партия"
        verbose_name_plural = "Партии"

    def __str__(self): return self.number


class BatchItem(TimeStampedModel):
    batch = models.ForeignKey(
        "inventory.Batch",
        on_delete=models.CASCADE,
        related_name="items"
    )
    drum = models.ForeignKey(
        "catalog.Drum",
        on_delete=models.PROTECT,
        related_name="batch_items"
    )
    storage_location = models.ForeignKey(
        "storage.Storage",
        on_delete=models.PROTECT,
        related_name="items"
    )
    number_in_batch = models.PositiveIntegerField(
        verbose_name="Номер в партии",
    )
    length_m = models.DecimalField(
        verbose_name="Длина по партии, м",
        max_digits=9, decimal_places=2,

        validators=[
            MinValueValidator(Decimal("0.01")),
            MaxValueValidator(Decimal("1000000.00"))
        ]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["batch", "number_in_batch"],
                name="uq_batch_number_in_batch"
            ),
            models.CheckConstraint(
                check=Q(length_m__gt=0),
                name="ck_batchitem_length_pos"
            ),            models.CheckConstraint(
                check=Q(number_in_batch__gt=0),
                name="ck_batchitem_number_in_batch_pos"
            ),
        ]
        indexes = [
            models.Index(fields=["batch"]),
            models.Index(fields=["drum"]),
            models.Index(fields=["storage_location"]),
        ]
        verbose_name = "Предмет в партии"
        verbose_name_plural = "Предметы в партии"

    def clean(self):
        super().clean()

        if not self.drum_id:
            raise ValidationError({"drum": "Не задан барабан."})
        if self.length_m is None:
            raise ValidationError({"length_m": "Не задана длина."})

        drum_initial = getattr(self.drum, "initial_length_m", None)

        if self.length_m > drum_initial:
            raise ValidationError({
                "length_m": f"Длина {self.length_m} м превышает первичную длину барабана {drum_initial} м."
            })

    def save(self, *args, **kwargs):
        self.full_clean(validate_unique=False)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.batch} / {self.drum}"
