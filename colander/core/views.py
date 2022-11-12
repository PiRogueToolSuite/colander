import pathlib
from tempfile import NamedTemporaryFile
import magic
from django.contrib import messages
from django.forms.widgets import Textarea, RadioSelect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.views.generic import CreateView, UpdateView

from colander.core.forms import CaseForm
from colander.core.models import Case, Artifact, Observable, ObservableRelation, ObservableType, ArtifactType
from colander.core.utils import hash_file

def evidences_view(request):
    return render(request, 'pages/evidences.html')


def collect_base_view(request):
    ctx = {
        'cases': Case.get_user_cases(request.user)[:20],
        'artifacts': Artifact.get_user_artifacts(request.user)[:20],
        'observables': Observable.get_user_observables(request.user)[:20],
    }
    return render(request, 'pages/collect/base.html', context=ctx)


def collect_cases_view(request):
    case_edit_form = CaseForm()
    case_edit_form.set_user(request.user)

    if request.method == 'POST':
        if 'save_case' in request.POST:
            f = CaseForm(request.POST)
            if f.is_valid():
                case = f.save(commit=False)
                f.set_user(request.user)
                case.save()
                f.save_m2m()
                messages.success(request, _(f'Your case {case.name} have been created.'))
                return redirect(request.META.get('HTTP_REFERER'))
    ctx = {
        'cases': Case.get_user_cases(request.user),
        'case_edit_form': case_edit_form
    }
    return render(request, 'pages/collect/cases.html', context=ctx)


def analyze_base_view(request):
    return render(request, 'pages/collect/base.html')


def investigate_base_view(request):
    return render(request, 'pages/collect/base.html')


def report_base_view(request):
    return render(request, 'pages/collect/base.html')


class ArtifactCreateView(CreateView):
    model = Artifact
    template_name = 'pages/collect/artifacts.html'
    success_url = reverse_lazy('collect_artifact_create_view')
    fields = [
        'file',
        'type',
        'case',
        'description',
        'source_url',
        'tlp',
        'pap',
    ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['artifacts'] = Artifact.get_user_artifacts(self.request.user)[:30]
        ctx['is_editing'] = False
        return ctx

    def form_valid(self, form):
        if form.is_valid():
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

class ArtifactUpdateView(ArtifactCreateView, UpdateView):

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['artifacts'] = Artifact.get_user_artifacts(self.request.user)[:30]
        ctx['is_editing'] = True
        return ctx


class ObservableCreateView(CreateView):
    model = Observable
    template_name = 'pages/collect/observables.html'
    success_url = reverse_lazy('collect_observable_create_view')
    fields = [
        'type',
        'case',
        'extracted_from',
        'associated_threat',
        'operated_by',
        'value',
        'description',
        'tlp',
        'pap',
        'source_url',
    ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['observables'] = Observable.get_user_observables(self.request.user)[:30]
        ctx['is_editing'] = False
        return ctx

    def get_form(self, form_class=None):
        observable_types = ObservableType.objects.all()
        form = super(ObservableCreateView, self).get_form(form_class)
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in observable_types
        ]
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        return form

    def form_valid(self, form):
        if form.is_valid():
            observable = form.save(commit=False)
            observable.owner = self.request.user
            evidence = form.cleaned_data['extracted_from']
            if evidence:
                observable.case = evidence.case
            observable.save()
            form.save_m2m()
        return super().form_valid(form)

class ObservableUpdateView(ObservableCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['observables'] = Observable.get_user_observables(self.request.user)[:30]
        ctx['observable_types'] = ObservableType.objects.all()
        ctx['is_editing'] = True
        return ctx

class ObservableRelationCreateView(CreateView):
    model = ObservableRelation
    template_name = 'pages/collect/relations.html'
    success_url = reverse_lazy('collect_relation_create_view')
    fields = [
        'case',
        'name',
        'observable_from',
        'observable_to',
        'description',
    ]

    def get_form(self, form_class=None):
        form = super(ObservableRelationCreateView, self).get_form(form_class)
        form.fields['name'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['relations'] = ObservableRelation.get_user_relations(self.request.user)[:30]
        return ctx
