import pathlib
from tempfile import NamedTemporaryFile

import magic
from django.forms.widgets import Textarea, RadioSelect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, UpdateView

from colander.core.models import Case, Artifact, Observable, ArtifactType, Actor, \
    ActorType, Device, DeviceType, Event, EventType
from colander.core.utils import hash_file


def evidences_view(request):
    return render(request, 'pages/evidences.html')


def collect_base_view(request):
    ctx = {
        'cases': Case.get_user_cases(request.user)[:20],
        'artifacts': Artifact.get_user_artifacts(request.user, request.session.get('active_case'))[:20],
        'observables': Observable.get_user_observables(request.user, request.session.get('active_case'))[:20],
    }
    return render(request, 'pages/collect/base.html', context=ctx)


def collect_cases_select_view(request, pk):
    if request.method == 'GET':
        case = get_object_or_404(Case, id=pk)
        request.session['active_case'] = str(case.id)
        return redirect(request.META.get('HTTP_REFERER'))


def get_active_case(request):
    if 'active_case' in request.session:
        try:
            return Case.objects.get(id=request.session['active_case'])
        except Exception:
            pass
    return None


class CaseCreateView(CreateView):
    model = Case
    template_name = 'pages/collect/cases.html'
    success_url = reverse_lazy('collect_case_create_view')
    fields = [
        'name',
        'description',
    ]

    def get_form(self, form_class=None):
        form = super(CaseCreateView, self).get_form(form_class)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        return form

    def form_valid(self, form):
        active_case = get_active_case(self.request)
        if form.is_valid() and active_case:
            case = form.save(commit=False)
            case.owner = self.request.user
            case.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cases'] = Case.get_user_cases(self.request.user)
        ctx['is_editing'] = False
        return ctx


class CaseUpdateView(CaseCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cases'] = Case.get_user_cases(self.request.user)
        ctx['is_editing'] = True
        return ctx


class ActorCreateView(CreateView):
    model = Actor
    template_name = 'pages/collect/actors.html'
    success_url = reverse_lazy('collect_actor_create_view')
    fields = [
        'type',
        'name',
        'description',
        'source_url',
        'tlp',
        'pap'
    ]

    def get_form(self, form_class=None):
        form = super(ActorCreateView, self).get_form(form_class)
        actor_types = ActorType.objects.all()
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in actor_types
        ]
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        return form

    def form_valid(self, form):
        if form.is_valid():
            actor = form.save(commit=False)
            actor.owner = self.request.user
            actor.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['actors'] = Actor.get_user_actors(self.request.user)
        ctx['is_editing'] = False
        return ctx


class ActorUpdateView(ActorCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['actors'] = Actor.get_user_actors(self.request.user)
        ctx['is_editing'] = True
        return ctx


class DeviceCreateView(CreateView):
    model = Device
    template_name = 'pages/collect/devices.html'
    success_url = reverse_lazy('collect_device_create_view')
    fields = [
        'type',
        'name',
        'description',
        'operated_by',
        'source_url',
        'tlp',
        'pap'
    ]

    def get_form(self, form_class=None):
        form = super(DeviceCreateView, self).get_form(form_class)
        device_types = DeviceType.objects.all()
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in device_types
        ]
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
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
        ctx['devices'] = Device.get_user_devices(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = False
        return ctx


class DeviceUpdateView(DeviceCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['devices'] = Device.get_user_devices(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = True
        return ctx


class EventCreateView(CreateView):
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

    def get_form(self, form_class=None):
        form = super(EventCreateView, self).get_form(form_class)
        event_types = EventType.objects.all()
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in event_types
        ]
        form.fields['involved_observables'].widget.attrs = {'size': 30}
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        return form

    def form_valid(self, form):
        active_case = get_active_case(self.request)
        if form.is_valid() and active_case:
            event = form.save(commit=False)
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
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['events'] = Event.get_user_events(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = True
        return ctx


class ArtifactCreateView(CreateView):
    model = Artifact
    template_name = 'pages/collect/artifacts.html'
    success_url = reverse_lazy('collect_artifact_create_view')
    fields = [
        'file',
        'type',
        'description',
        'extracted_from',
        'source_url',
        'tlp',
        'pap',
    ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['artifacts'] = Artifact.get_user_artifacts(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = False
        return ctx

    def form_valid(self, form):
        active_case = get_active_case(self.request)
        if form.is_valid() and active_case:
            evidence = form.save(commit=False)
            evidence.owner = self.request.user
            file_name = str(self.request.FILES['file'])
            uploaded_file = self.request.FILES['file']
            with NamedTemporaryFile(suffix=file_name) as tmp:
                for chunk in uploaded_file.chunks():
                    tmp.write(chunk)
                tmp.seek(0)
                sha256, sha1, md5, size = hash_file(tmp)
                mime_type = magic.from_file(tmp.name, mime=True)
            extension = pathlib.Path(file_name).suffix
            evidence.sha256 = sha256
            evidence.sha1 = sha1
            evidence.md5 = md5
            evidence.size_in_bytes = size
            evidence.extension = extension
            evidence.mime_type = mime_type
            evidence.original_name = file_name
            evidence.case = active_case
            evidence.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super(ArtifactCreateView, self).get_form(form_class)
        artifact_types = ArtifactType.objects.all()
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in artifact_types
        ]
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        return form


class ArtifactUpdateView(UpdateView):
    model = Artifact
    template_name = 'pages/collect/artifacts.html'
    success_url = reverse_lazy('collect_artifact_create_view')
    fields = [
        'type',
        'description',
        'extracted_from',
        'source_url',
        'tlp',
        'pap',
    ]

    def get_form(self, form_class=None):
        form = super(ArtifactUpdateView, self).get_form(form_class)
        artifact_types = ArtifactType.objects.all()
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in artifact_types
        ]
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['artifacts'] = Artifact.get_user_artifacts(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = True
        return ctx


def analyze_base_view(request):
    return render(request, 'pages/collect/base.html')


def investigate_base_view(request):
    return render(request, 'pages/collect/base.html')


def report_base_view(request):
    return render(request, 'pages/collect/base.html')
