from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.widgets import Textarea, RadioSelect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, UpdateView, DetailView

from colander.core.forms import CommentForm
from colander.core.models import DataFragment, DataFragmentType, Artifact
from colander.core.views.views import get_active_case, CaseRequiredMixin


class DataFragmentCreateView(LoginRequiredMixin, CaseRequiredMixin, CreateView):
    model = DataFragment
    template_name = 'pages/collect/data_fragments.html'
    success_url = reverse_lazy('collect_data_fragment_create_view')
    fields = [
        'type',
        'name',
        'description',
        'source_url',
        'tlp',
        'pap',
        'extracted_from',
        'content'
    ]
    case_required_message_action = "create data fragments"

    def get_form(self, form_class=None, edit=False):
        form = super(DataFragmentCreateView, self).get_form(form_class)
        rule_types = DataFragmentType.objects.all()
        #active_case = self.request.session.get('active_case')
        active_case = get_active_case(self.request)
        artifact_qset = Artifact.get_user_artifacts(self.request.user, active_case)
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in rule_types
        ]
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        form.fields['extracted_from'].queryset = artifact_qset
        form.fields['extracted_from'].queryset = artifact_qset

        if not edit:
            form.initial['tlp'] = active_case.tlp
            form.initial['pap'] = active_case.pap

        return form

    def form_valid(self, form):
        active_case = get_active_case(self.request)
        if form.is_valid() and active_case:
            rule = form.save(commit=False)
            if not hasattr(rule, 'owner'):
                rule.owner = self.request.user
                rule.case = active_case
            rule.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['data_fragments'] = DataFragment.get_user_data_fragments(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = False
        return ctx


class DataFragmentUpdateView(DataFragmentCreateView, UpdateView):
    context_object_name = 'data_fragment'
    case_required_message_action = "update data fragment"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['data_fragments'] = DataFragment.get_user_data_fragments(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = True
        return ctx

    def get_form(self, form_class=None):
        return super().get_form(form_class, True)

class DataFragmentDetailsView(LoginRequiredMixin, CaseRequiredMixin, DetailView):
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
    return redirect("collect_data_fragment_create_view")
