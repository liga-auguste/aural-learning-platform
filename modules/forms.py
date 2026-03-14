from django import forms
from django.forms.widgets import ClearableFileInput
from modules.models import Module
from .models import Aufgabentyp, GlossaryEntry
from django.db.models import Count
from .widgets import GlossaryCheckboxWidget


class PrettyFileInput(ClearableFileInput):
    template_name = "widgets/pretty_clearable_file_input.html"
    initial_text = "Aktuell"
    input_text = ""
    clear_checkbox_label = "Zurücksetzen"


class ModuleForm(forms.ModelForm):
    tasktype = forms.ModelMultipleChoiceField(
        queryset=Aufgabentyp.objects.all().order_by("name"),
        required=False,
        label="Aufgabentypen",
        widget=forms.CheckboxSelectMultiple(),
    )

    glossary_entries = forms.ModelMultipleChoiceField(
        queryset=GlossaryEntry.objects.all().order_by("title"),
        required=False,
        label="Lernbegriffe:",
        help_text="Begriffe, die in diesem Modul erklärt und angezeigt werden",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["glossary_entries"].widget = GlossaryCheckboxWidget()
        self.fields["glossary_entries"].queryset = (
            GlossaryEntry.objects
            .annotate(modules_count=Count("modules", distinct=True))
            .order_by("title")
        )
        self.fields["glossary_entries"].label_from_instance = lambda obj: (
            f"{obj.title} ({getattr(obj, 'modules_count', 0)})"
        )

        if self.instance and self.instance.pk:
            self.fields["glossary_entries"].initial = self.instance.glossary_terms.all()

    def save(self, commit=True):
        module = super().save(commit=commit)
        if commit:
            module.glossary_terms.set(self.cleaned_data.get("glossary_entries") or [])
        return module
    
    class Meta:
        model = Module
        fields = ["title", "inclass", "homework",
            "tasktype",
            "glossary_entries",
            "pdf_1", "pdf_2", "pdf_3", "pdf_4", 
            "audio_1","audio_1_title",
            "audio_2","audio_2_title",
            "audio_3","audio_3_title",
            "audio_4","audio_4_title",
            ]
        labels = {
            "title": "Titel des Moduls",
            "inclass": "Unterricht",
            "homework": "Hausaufgabe",
            "tasktype": "Aufgabentypen",
            "pdf_1": "Skript",
            "pdf_2": "Lösung zum Skript",
            "pdf_3": "Hausaufgabe",
            "pdf_4": "Lösung zur Hausaufgabe",
        }
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "inclass": forms.Textarea(attrs={"rows": 5}),
            "homework": forms.Textarea(attrs={"rows": 3}),
            "pdf_1": PrettyFileInput(attrs={"accept": ".pdf"}),
            "pdf_2": PrettyFileInput(attrs={"accept": ".pdf"}),
            "pdf_3": PrettyFileInput(attrs={"accept": ".pdf"}),
            "pdf_4": PrettyFileInput(attrs={"accept": ".pdf"}),
        }
    
    def clean(self):
        cleaned = super().clean()

        pairs = [
            ("audio_1", "audio_1_title"),
            ("audio_2", "audio_2_title"),
            ("audio_3", "audio_3_title"),
            ("audio_4", "audio_4_title"),
        ]

        for file_field, title_field in pairs:
            f = cleaned.get(file_field)
            t = (cleaned.get(title_field) or "").strip()

            if f and not t:
                self.add_error(title_field, "Bitte gib einen Titel an, wenn du eine Audiodatei hochlädst.")

        return cleaned

class ContactForm(forms.Form):
    name = forms.CharField(label="Name", max_length=100)
    email = forms.EmailField(label="E-Mail")
    subject = forms.CharField(label="Betreff", max_length=150, required=False)
    message = forms.CharField(label="Nachricht", widget=forms.Textarea(attrs={"rows": 6}))
    consent = forms.BooleanField(
        label="Ich stimme der Verarbeitung meiner Angaben zu (Datenschutz)."
    )
    # Honeypot (soll leer bleiben)
    hp_field = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_hp_field(self):
        if self.cleaned_data.get("hp_field"):
            raise forms.ValidationError("Spam erkannt.")
        return ""
    
