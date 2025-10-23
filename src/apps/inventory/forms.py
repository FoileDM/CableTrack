from django import forms

from apps.storage.models import Storage


class BatchImportForm(forms.Form):
    batch_number = forms.CharField(label="Номер партии", max_length=64)
    storage = forms.ModelChoiceField(label="Склад", queryset=Storage.objects.all())
    file = forms.FileField(label="CSV-файл")

    def clean_file(self):
        f = self.cleaned_data["file"]
        if f.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Слишком большой файл (>5MB).")
        return f
