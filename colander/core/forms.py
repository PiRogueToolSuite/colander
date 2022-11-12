from django import forms

from colander.core.models import Case


class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = [
            'name',
            'description',
            'parent_case',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'cols': 20}),
        }

    def set_user(self, connected_user):
        if connected_user:
            self.instance.owner = connected_user

