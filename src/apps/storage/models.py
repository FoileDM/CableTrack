from django.db import models

from apps.core.models import TimeStampedModel


class Storage(TimeStampedModel):
    code = models.CharField("Код места хранения", max_length=64, unique=True)
    name = models.CharField("Название", max_length=128, blank=True, default="")

    class Meta:
        verbose_name = "Склад"
        verbose_name_plural = "Склады"

    def save(self, *args, **kwargs):
        if self.code: self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self): return self.code
