from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, reverse

from apps.inventory.models import Batch, BatchItem
from apps.inventory.views import BatchImportAdminView


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("number", "created_at")
    search_fields = ("number",)
    ordering = ("-created_at",)

    def add_view(self, request, form_url="", extra_context=None):
        return redirect(reverse("admin:inventory_batch_import"))

    def get_urls(self):
        urls = super().get_urls()
        view = BatchImportAdminView.as_view(admin_site=self.admin_site)
        my_urls = [
            path(
                "import/",
                self.admin_site.admin_view(view),
                name="inventory_batch_import",
            ),
        ]
        return my_urls + urls


@admin.register(BatchItem)
class BatchItemAdmin(admin.ModelAdmin):
    list_display = ("batch", "number_in_batch", "drum", "storage_location", "length_m", "created_at")
    search_fields = ("batch__number", "drum__code", "storage_location__code")
    list_filter = ("batch", "storage_location")
    list_select_related = ("batch", "drum", "storage_location")
