from django.forms.widgets import CheckboxSelectMultiple

class GlossaryCheckboxWidget(CheckboxSelectMultiple):
    def label_from_instance(self, obj):
        count = getattr(obj, "modules_count", None)
        if count is None:
            return obj.title
        return f"{obj.title} ({count})"