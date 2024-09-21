import yara
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from colander.core.models import Case, Comment, DetectionRule
from colander.core.threatr import ThreatrClient


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
    # Corresponds to the entity super type such as observable
    super_type = forms.ChoiceField()
    # Corresponds to the entity type such as ipv4
    type = forms.ChoiceField()
    value = forms.CharField(max_length=128)
    force_update = forms.BooleanField(required=False, label='Update results from vendors.')

    def __init__(self, *args, **kwargs):
        super(InvestigateSearchForm, self).__init__(*args, **kwargs)
        self.threatr_client = ThreatrClient()
        self.threatr_supported_types = self.threatr_client.get_supported_types()
        self.fields['super_type'].choices = [
            (t.get('name').upper(), t.get('name'))
            for t in self.threatr_supported_types.get('super_types')
        ]
        available_types = []
        for _, m in self.threatr_supported_types.get('types').items():
            for t in m:
                available_types.append((t.get('id').upper(), t.get('label')))
        self.fields['type'].choices = available_types

    def clean(self):
        cleaned_data = super().clean()
        selected_model = cleaned_data.get('super_type')
        selected_type = cleaned_data.get('type')
        if selected_model not in self.threatr_supported_types.get('types'):
            raise ValidationError(
                _("Invalid model selected"), code="invalid"
            )
        model_types = self.threatr_supported_types.get('types').get(selected_model, None)
        if selected_type not in [
            t.get('id')
            for t in model_types
        ]:
            raise ValidationError(
                _("Invalid types combination"), code="invalid"
            )



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
