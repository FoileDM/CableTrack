from django.contrib import admin
from apps.catalog.models import CableModel, Drum

@admin.register(CableModel)
class CableModelAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "min_length_m", "max_length_m", "created_at")
    search_fields = ("code", "name")

@admin.register(Drum)
class DrumAdmin(admin.ModelAdmin):
    list_display = ("code", "cable_model", "initial_length_m", "created_at")
    search_fields = ("code",)
