from django.contrib import admin

from apps.storage.models import Storage


@admin.register(Storage)
class StorageAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "created_at")
    search_fields = ("code",)
