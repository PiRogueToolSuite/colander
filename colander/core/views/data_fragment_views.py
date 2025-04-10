from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.widgets import RadioSelect, Textarea
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, DetailView, UpdateView

from colander.core.forms import CommentForm
from colander.core.forms.widgets import ThumbnailFileInput
from colander.core.models import Artifact, DataFragment, DataFragmentType
from colander.core.views.views import CaseContextMixin


class DataFragmentCreateView(LoginRequiredMixin, CaseContextMixin, CreateView):
    model = DataFragment
    template_name = 'pages/collect/data_fragments.html'
    contextual_success_url = 'collect_data_fragment_create_view'
    #success_url = reverse_lazy('collect_data_fragment_create_view')
    fields = [
        'type',
        'name',
        'description',
        'source_url',
        'tlp',
        'pap',
        'extracted_from',
        'content',
        'thumbnail',
    ]
    case_required_message_action = "create data fragments"

    def get_form(self, form_class=None, edit=False):
        form = super(DataFragmentCreateView, self).get_form(form_class)
        rule_types = DataFragmentType.objects.all()
        #active_case = self.request.session.get('active_case')
        #active_case = get_active_case(self.request)
        artifact_qset = Artifact.get_user_artifacts(self.request.user, self.active_case)
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in rule_types
        ]
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        form.fields['extracted_from'].queryset = artifact_qset
        form.fields['extracted_from'].queryset = artifact_qset
        form.fields['content'].widget.attrs.update({'class': 'colander-text-editor'})
        form.fields['thumbnail'].widget = ThumbnailFileInput()
        if self.object and self.object.thumbnail:
            form.fields['thumbnail'].widget.thumbnail_url = self.object.thumbnail_url

        if not edit:
            form.initial['tlp'] = self.active_case.tlp
            form.initial['pap'] = self.active_case.pap

        return form

    def form_valid(self, form):
        #active_case = get_active_case(self.request)
        if form.is_valid() and self.active_case:
            rule = form.save(commit=False)
            if not hasattr(rule, 'owner'):
                rule.owner = self.request.user
                rule.case = self.active_case
            rule.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['entity_types'] = {str(t.id): {'type': t.short_name, 'attributes': t.default_attributes} for t in DataFragmentType.objects.all()}
        ctx['data_fragments'] = DataFragment.get_user_data_fragments(self.request.user, self.active_case)
        ctx['is_editing'] = False
        return ctx


class DataFragmentUpdateView(DataFragmentCreateView, UpdateView):
    context_object_name = 'data_fragment'
    case_required_message_action = "update data fragment"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['data_fragments'] = DataFragment.get_user_data_fragments(self.request.user, self.active_case)
        ctx['is_editing'] = True
        return ctx

    def get_form(self, form_class=None):
        return super().get_form(form_class, True)


class DataFragmentDetailsView(LoginRequiredMixin, CaseContextMixin, DetailView):
    model = DataFragment
    template_name = 'pages/collect/data_fragment_details.html'
    context_object_name = 'data_fragment'
    case_required_message_action = "view data fragment details"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comment_form'] = CommentForm()
        return ctx


@login_required
def delete_data_fragment_view(request, pk):
    obj = DataFragment.objects.get(id=pk)
    obj.delete()
    return redirect("collect_data_fragment_create_view", case_id=request.contextual_case.id)
