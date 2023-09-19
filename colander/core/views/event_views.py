from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.widgets import Textarea, RadioSelect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, UpdateView, DetailView

from colander.core.forms import CommentForm
from colander.core.models import Event, EventType, Observable, Artifact, Device, DetectionRule
from colander.core.views.views import get_active_case, CaseRequiredMixin


class EventCreateView(LoginRequiredMixin, CaseRequiredMixin, CreateView):
    model = Event
    template_name = 'pages/collect/events.html'
    success_url = reverse_lazy('collect_event_create_view')
    fields = [
        'type',
        'name',
        'description',
        'first_seen',
        'last_seen',
        'count',
        'extracted_from',
        'observed_on',
        'detected_by',
        'involved_observables',
        'source_url',
        'tlp',
        'pap'
    ]
    case_required_message_action = "create events"

    def get_form(self, form_class=None, edit=False):
        active_case = get_active_case(self.request)
        observable_qset = Observable.get_user_observables(self.request.user, active_case)
        artifact_qset = Artifact.get_user_artifacts(self.request.user, active_case)
        devices_qset = Device.get_user_devices(self.request.user, active_case)
        rules_qset = DetectionRule.get_user_detection_rules(self.request.user, active_case)
        form = super(EventCreateView, self).get_form(form_class)
        event_types = EventType.objects.all()
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in event_types
        ]
        form.fields['involved_observables'].widget.attrs = {'size': 30}
        form.fields['involved_observables'].queryset = observable_qset
        form.fields['extracted_from'].queryset = artifact_qset
        form.fields['observed_on'].queryset = devices_qset
        form.fields['detected_by'].queryset = rules_qset
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})

        if not edit:
            form.initial['tlp'] = active_case.tlp
            form.initial['pap'] = active_case.pap

        return form

    def form_valid(self, form):
        active_case = get_active_case(self.request)
        if form.is_valid() and active_case:
            event = form.save(commit=False)
            if not hasattr(event, 'owner'):
                event.owner = self.request.user
                event.case = active_case
            event.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['events'] = Event.get_user_events(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = False
        return ctx


class EventUpdateView(EventCreateView, UpdateView):
    case_required_message_action = "update event"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['events'] = Event.get_user_events(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = True
        return ctx

    def get_form(self, form_class=None):
        return super().get_form(form_class, True)


class EventDetailsView(LoginRequiredMixin, CaseRequiredMixin, DetailView):
    model = Event
    template_name = 'pages/collect/event_details.html'
    case_required_message_action = "view event details"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comment_form'] = CommentForm()
        return ctx


@login_required
def delete_event_view(request, pk):
    obj = Event.objects.get(id=pk)
    obj.delete()
    return redirect("collect_event_create_view")
