from django import forms
from .models import Module

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ["title", "inclass", "homework", "terms", "pdf_1", "pdf_2", "pdf_3", "pdf_4"]
        labels = {
            "title": "Titel des Moduls",
            "inclass": "Im Unterricht",
            "homework": "Hausaufgabe",
            "terms": "Begriffe",
            "pdf_1": "Skript",
            "pdf_2": "Lösung",
            "pdf_3": "Hausaufgabe",
            "pdf_4": "Hausaufgabe - Lösung",
        }
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "inclass": forms.Textarea(attrs={"rows": 5}),
            "homework": forms.Textarea(attrs={"rows": 3}),
        }
