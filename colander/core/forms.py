from django import forms

from colander.core.models import Case, Comment, ObservableType


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


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = [
            'content',
            'commented_object',
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'cols': 20}),
            'commented_object': forms.TextInput()
        },


    def set_user(self, connected_user):
        if connected_user:
            self.instance.owner = connected_user


class InvestigateSearchForm(forms.Form):
    types = [(t.short_name, t.name) for t in ObservableType.objects.all()]
    type = forms.ChoiceField(choices=types)
    value = forms.CharField(max_length=128)
