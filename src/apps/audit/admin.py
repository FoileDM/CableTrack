from django.contrib import admin
from django.utils.html import format_html_join

from apps.audit.models import ImportLog


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ("batch", "file_name", "status_ok")
    list_display_links = ("batch", "file_name")
    search_fields = ("batch__number", "file_name", "file_sha256")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    readonly_fields = (
        "batch",
        "file_name",
        "file_sha256",
        "status_ok",
        "status_summary",
        "total",
        "inserted",
        "duplicates_in_file",
        "duplicates_in_db",
        "invalid_rows",
        "duration_sec",
        "errors_pretty",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Файл и партия", {"fields": ("batch", "file_name", "file_sha256")}),
        ("Статус", {
            "fields": (
                "status_ok",
                "total",
                "inserted",
                "duplicates_in_file",
                "duplicates_in_db",
                "invalid_rows",
                "duration_sec",
            )
        }),
        ("Ошибки", {"fields": ("errors_pretty",)}),
        ("Метаданные", {"fields": ("created_at", "updated_at")}),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(boolean=True, description="OK")
    def status_ok(self, obj: ImportLog) -> bool:
        return (obj.invalid_rows == 0
                and obj.duplicates_in_file == 0
                and obj.duplicates_in_db == 0)

    @admin.display(description="Итоги")
    def status_summary(self, obj: ImportLog) -> str:
        return (
            f"total={obj.total}; inserted={obj.inserted}; "
            f"dup_file={obj.duplicates_in_file}; dup_db={obj.duplicates_in_db}; "
            f"invalid={obj.invalid_rows}; duration={obj.duration_sec}s"
        )

    @admin.display(description="Ошибки")
    def errors_pretty(self, obj: ImportLog):
        if not obj.errors:
            return "—"
        items = tuple((str(e),) for e in obj.errors[:50])
        return format_html_join("", "<li>{}</li>", items)
