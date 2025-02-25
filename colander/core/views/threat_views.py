from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.widgets import RadioSelect, Textarea
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, DetailView, UpdateView

from colander.core.forms import CommentForm
from colander.core.forms.widgets import ThumbnailFileInput
from colander.core.models import Threat, ThreatType
from colander.core.views.views import CaseContextMixin


class ThreatCreateView(LoginRequiredMixin, CaseContextMixin, CreateView):
    model = Threat
    template_name = 'pages/collect/threats.html'
    contextual_success_url = 'collect_threat_create_view'
    #success_url = reverse_lazy('collect_threat_create_view')
    fields = [
        'type',
        'name',
        'description',
        'source_url',
        'tlp',
        'pap',
        'thumbnail',
    ]
    case_required_message_action = "create threats"

    def get_form(self, form_class=None, edit=False):
        #active_case = get_active_case(self.request)
        form = super(ThreatCreateView, self).get_form(form_class)
        threat_types = ThreatType.objects.all()
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in threat_types
        ]
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
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
            threat = form.save(commit=False)
            if not hasattr(threat, 'owner'):
                threat.owner = self.request.user
                threat.case = self.active_case
            threat.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['entity_types'] = {str(t.id): {'type': t.short_name, 'attributes': t.default_attributes} for t in ThreatType.objects.all()}
        ctx['threats'] = Threat.get_user_threats(self.request.user, self.active_case)
        ctx['is_editing'] = False
        return ctx


class ThreatUpdateView(ThreatCreateView, UpdateView):
    case_required_message_action = "update threat"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['threats'] = Threat.get_user_threats(self.request.user, self.active_case)
        ctx['is_editing'] = True
        return ctx

    def get_form(self, form_class=None):
        return super().get_form(form_class, True)


class ThreatDetailsView(LoginRequiredMixin, CaseContextMixin, DetailView):
    model = Threat
    template_name = 'pages/collect/threat_details.html'
    case_required_message_action = "view threat details"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comment_form'] = CommentForm()
        return ctx


@login_required
def delete_threat_view(request, pk):
    obj = Threat.objects.get(id=pk)
    obj.delete()
    return redirect("collect_threat_create_view", case_id=request.contextual_case.id)
