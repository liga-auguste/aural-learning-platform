from django import forms
from django.forms.widgets import ClearableFileInput
from modules.models import Module

class PrettyFileInput(ClearableFileInput):
    template_name = "widgets/pretty_clearable_file_input.html"
    initial_text = "Aktuell"
    input_text = ""
    clear_checkbox_label = "Zurücksetzen"


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ["title", "inclass", "homework", "terms", "pdf_1", "pdf_2", "pdf_3", "pdf_4", 
            "audio_1","audio_1_title",
            "audio_2","audio_2_title",
            "audio_3","audio_3_title",
            "audio_4","audio_4_title",
            ]
        labels = {
            "title": "Titel des Moduls",
            "inclass": "Unterricht",
            "homework": "Hausaufgabe",
            "terms": "Begriffe",
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

            # optional streng: Titel nur erlaubt, wenn auch Datei hochgeladen ist
            # if t and not f:
            #     self.add_error(file_field, "Bitte lade auch eine Audiodatei hoch, wenn du einen Titel angibst.")

        return cleaned

class ModuleFilesForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ("pdf_1", "pdf_2", "pdf_3", "pdf_4")
        widgets = {
            "pdf_1": forms.ClearableFileInput(attrs={"accept": ".pdf"}),
            "pdf_2": forms.ClearableFileInput(attrs={"accept": ".pdf"}),
            "pdf_3": forms.ClearableFileInput(attrs={"accept": ".pdf"}),
            "pdf_4": forms.ClearableFileInput(attrs={"accept": ".pdf"}),
        }
        labels = {
            "pdf_1": "Skript",
            "pdf_2": "Lösung zum Skript",
            "pdf_3": "Hausaufgabe",
            "pdf_4": "Lösung zur Hausaufgabe",
        }
        
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