from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic.edit import FormView

from apps.inventory.forms import BatchImportForm
from apps.inventory.models import Batch
from apps.inventory.services.import_from_csv import import_batch_from_csv


@method_decorator(csrf_protect, name="dispatch")
class BatchImportAdminView(FormView):
    template_name = "admin/inventory/batch/import.html"
    form_class = BatchImportForm

    admin_site = None
    permission_codename = "inventory.add_batchitem"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm(self.permission_codename):
            return HttpResponseForbidden("Недостаточно прав для импорта партии.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.admin_site:
            ctx.update(self.admin_site.each_context(self.request))
        ctx["opts"] = Batch._meta
        ctx["title"] = "Импорт CSV в партию"
        return ctx

    def form_valid(self, form):
        batch_number = form.cleaned_data["batch_number"]
        storage = form.cleaned_data["storage"]
        file = form.cleaned_data["file"]

        res = import_batch_from_csv(file=file, batch_number=batch_number, storage=storage)

        msg = (
            f"Импорт '{res.file_name}' в партию '{batch_number}' завершён: "
            f"всего={res.total}, вставлено={res.inserted}, "
            f"дубли_в_файле={res.duplicates_in_file}, дубли_в_БД={res.duplicates_in_db}, "
            f"некорректных={res.invalid_rows}"
        )
        level = messages.SUCCESS if res.inserted and not res.invalid_rows else messages.WARNING
        messages.add_message(self.request, level, msg)

        try:
            batch = Batch.objects.get(id=res.batch_id)
            url = reverse("admin:inventory_batch_change", args=[batch.id])
            return redirect(url)
        except Batch.DoesNotExist:
            return redirect("admin:inventory_batch_changelist")
