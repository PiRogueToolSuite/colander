from django.forms.widgets import Textarea, RadioSelect
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, UpdateView, DetailView

from colander.core.models import PiRogueExperiment, Artifact
from colander.core.views import get_active_case


class PiRogueExperimentCreateView(CreateView):
    model = PiRogueExperiment
    template_name = 'pages/collect/experiments.html'
    success_url = reverse_lazy('collect_experiment_create_view')
    fields = [
        'name',
        'pcap',
        'socket_trace',
        'sslkeylog',
        'tlp',
        'pap'
    ]

    def get_form(self, form_class=None):
        active_case = get_active_case(self.request)
        artifacts_qset = Artifact.get_user_artifacts(self.request.user, active_case)
        form = super(PiRogueExperimentCreateView, self).get_form(form_class)
        form.fields['pcap'].queryset = artifacts_qset
        form.fields['socket_trace'].queryset = artifacts_qset
        form.fields['sslkeylog'].queryset = artifacts_qset
        return form

    def form_valid(self, form):
        active_case = get_active_case(self.request)
        if form.is_valid() and active_case:
            device = form.save(commit=False)
            device.owner = self.request.user
            device.case = active_case
            device.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['experiments'] = PiRogueExperiment.get_user_pirogue_dumps(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = False
        return ctx


class PiRogueExperimentUpdateView(PiRogueExperimentCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['experiments'] = PiRogueExperiment.get_user_pirogue_dumps(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = True
        return ctx


class PiRogueExperimentDetailsView(DetailView):
    model = PiRogueExperiment
    template_name = 'pages/collect/experiment_details.html'
    context_object_name = 'experiment'
