from django.contrib import admin
from django.db.models import F, Q
from django.utils.html import format_html, format_html_join

from apps.audit.models import ImportLog


class ImportStatusFilter(admin.SimpleListFilter):
    title = "Статус"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return [
            ("ok", "OK"),
            ("partial", "PARTIAL"),
            ("fail", "FAIL"),
        ]

    def queryset(self, request, qs):
        value = self.value()
        if value == "ok":
            return qs.filter(
                inserted=F("total"),
                invalid_rows=0,
                duplicates_in_file=0,
                duplicates_in_db=0,
            )
        if value == "partial":
            return qs.filter(
                inserted__gt=0
            ).filter(
                Q(inserted__lt=F("total")) |
                Q(invalid_rows__gt=0) |
                Q(duplicates_in_file__gt=0) |
                Q(duplicates_in_db__gt=0)
            )
        if value == "fail":
            return qs.filter(inserted=0)
        return qs


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "batch", "file_name", "status_badge",)
    list_display_links = ("batch", "file_name")
    list_filter = (ImportStatusFilter, "batch")
    search_fields = ("batch__number", "file_name", "file_sha256")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    readonly_fields = (
        "batch",
        "file_name",
        "file_sha256",
        "status_badge",
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
                "status_badge",
                "status_summary",
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

    def status_code(self, obj: ImportLog) -> str:
        if (obj.inserted or 0) == 0:
            return "fail"
        if (
            obj.inserted == obj.total
            and obj.invalid_rows == 0
            and obj.duplicates_in_file == 0
            and obj.duplicates_in_db == 0
        ):
            return "ok"
        return "partial"

    @admin.display(description="Статус")
    def status_badge(self, obj: ImportLog) -> str:
        code = self.status_code(obj)
        if code == "ok":
            text, bg = "OK", "#10b981"
        elif code == "partial":
            text, bg = "PARTIAL", "#f59e0b"
        else:
            text, bg = "FAIL", "#ef4444"
        return format_html(
            '<span style="display:inline-block;padding:2px 8px;border-radius:9999px;'
            'font-weight:600;color:#fff;background:{};">{}</span>',
            bg, text
        )

    @admin.display(description="Прогресс", ordering="inserted")
    def progress(self, obj: ImportLog) -> str:
        total = obj.total or 0
        ins = obj.inserted or 0
        pct = int(round((ins / total) * 100)) if total > 0 else 0
        return f"{pct}% ({ins}/{total})"

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
        return format_html('<ul style="margin:0;padding-left:1.1rem;">{}</ul>',
                           format_html_join("", "<li>{}</li>", items))
