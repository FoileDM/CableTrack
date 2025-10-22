from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel


class CableModel(TimeStampedModel):
    code = models.CharField(
        verbose_name="Код модели",
        max_length=64,
        unique=True
    )
    name = models.CharField(
        verbose_name="Название",
        max_length=128,
        blank=True,
        default=""
    )
    min_length_m = models.DecimalField(
        verbose_name="Мин. длина, м",
        max_digits=9, decimal_places=2,
        default=Decimal("0.01"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    max_length_m = models.DecimalField(
        verbose_name="Макс. длина, м",
        max_digits=9, decimal_places=2,
        default=Decimal("1000000.00"),
        validators=[
            MinValueValidator(Decimal("0.01")),
            MaxValueValidator(Decimal("1000000.00")),
        ],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(min_length_m__gt=0), name="ck_cablemodel_min_pos"),
            models.CheckConstraint(check=Q(max_length_m__gt=0), name="ck_cablemodel_max_pos"),
            models.CheckConstraint(
                check=Q(max_length_m__gte=models.F("min_length_m")), name="ck_cablemodel_bounds"
            ),
        ]
        verbose_name = "Модель кабеля"
        verbose_name_plural = "Модели кабеля"

    def __str__(self) -> str:
        return self.code


class Drum(TimeStampedModel):
    code = models.CharField(
        verbose_name="Код барабана",
        max_length=64,
        unique=True
    )
    cable_model = models.ForeignKey(
        "CableModel",
        on_delete=models.PROTECT,
        related_name="drums",
        verbose_name="Модель кабеля"
    )
    initial_length_m = models.DecimalField(
        verbose_name="Первичная длина, м",
        max_digits=9, decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
            MaxValueValidator(Decimal("1000000.00")),
        ],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(initial_length_m__gt=0), name="ck_drum_initial_pos"),
        ]
        verbose_name = "Барабан"
        verbose_name_plural = "Барабаны"

    def clean(self):
        super().clean()

        if not self.cable_model_id:
            raise ValidationError({"cable_model": "Не задана модель кабеля."})

        if self.initial_length_m is None:
            raise ValidationError({"initial_length_m": "Не задана первичная длина."})

        cm = self.cable_model
        if not (cm.min_length_m <= self.initial_length_m <= cm.max_length_m):
            raise ValidationError({
                "initial_length_m": (
                    f"Длина {self.initial_length_m} м вне диапазона модели "
                    f"{cm.code}: {cm.min_length_m}–{cm.max_length_m} м."
                )
            })

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.strip().upper()
        self.full_clean(validate_unique=False)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.code
