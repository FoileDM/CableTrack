from django.contrib import admin

from apps.inventory.models import Batch, BatchItem


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("number", "created_at")
    search_fields = ("number",)


@admin.register(BatchItem)
class BatchItemAdmin(admin.ModelAdmin):
    list_display = ("batch", "number_in_batch", "drum", "storage_location", "length_m", "created_at")
    search_fields = ("batch__number", "drum__code", "storage_location__code")
    list_filter = ("batch", "storage_location")
    list_select_related = ("batch", "drum", "storage_location")
