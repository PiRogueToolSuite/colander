import pathlib
from tempfile import NamedTemporaryFile

import magic
from django.forms.widgets import Textarea, RadioSelect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, UpdateView

from colander.core.models import Case, Artifact, Observable, ArtifactType, Actor, \
    ActorType, Device, DeviceType
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











def analyze_base_view(request):
    return render(request, 'pages/collect/base.html')


def investigate_base_view(request):
    return render(request, 'pages/collect/base.html')


def report_base_view(request):
    return render(request, 'pages/collect/base.html')
