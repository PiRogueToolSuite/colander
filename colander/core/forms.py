import yara
from django import forms
from django.core.exceptions import ValidationError

from colander.core.models import Case, Comment, ObservableType, DetectionRule
from django.utils.translation import gettext_lazy as _


class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = [
            'name',
            'description',
            'parent_case',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'cols': 20, 'placeholder': _("No case description yet.")}),
        }

    def set_user(self, connected_user):
        if connected_user:
            self.instance.owner = connected_user


class DetectionRuleForm(forms.ModelForm):
    class Meta:
        model = DetectionRule
        fields = [
            'type',
            'name',
            'description',
            'source_url',
            'tlp',
            'pap',
            'content'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'cols': 20}),
        }

    def clean_content(self):
        content = self.cleaned_data.get('content')
        _type = self.cleaned_data.get('type')
        if _type.short_name == 'YARA':
            try:
                yara.compile(source=content)
            except Exception as e:
                raise ValidationError(
                    f'The Yara rule does not compile: {e}'
                )
        return content


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
    type = forms.ChoiceField(choices=[(t.short_name, t.name) for t in ObservableType.objects.all()])
    value = forms.CharField(max_length=128)
    force_update = forms.BooleanField(required=False, label='Update results from vendors.')


class DocumentationForm(forms.Form):
    documentation = forms.CharField(widget=forms.Textarea(), label=False)

class EntityRelationForm(forms.Form):
    name = forms.CharField(
        label='Relation name',
        max_length=128,
        required=True
    )
    obj_from = forms.ChoiceField(
        label='Source entity',
        required=True
    )
    obj_to = forms.ChoiceField(
        label='Target entity',
        required=True
    )


class AddRemoveTeamContributorForm(forms.Form):
    contributor_id = forms.UUIDField(
        label='ID of the contributor to add',
        required=True
    )
