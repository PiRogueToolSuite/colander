import json

from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.forms.widgets import Textarea
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView

from colander.core.models import Case, Artifact, Observable


class CaseRequiredMixin(AccessMixin):
    """Verify that the current user has an active case."""
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('active_case'):
            return redirect('collect_case_create_view')
        return super().dispatch(request, *args, **kwargs)


@login_required
def evidences_view(request):
    if not request.session.get('active_case'):
        return redirect('collect_case_create_view')
    return render(request, 'pages/evidences.html')


@login_required
def collect_base_view(request):
    if not request.session.get('active_case'):
        return redirect('collect_case_create_view')

    ctx = {
        'cases': Case.get_user_cases(request.user)[:20],
        'artifacts': Artifact.get_user_artifacts(request.user, request.session.get('active_case'))[:20],
        'observables': Observable.get_user_observables(request.user, request.session.get('active_case'))[:20],
    }
    return render(request, 'pages/collect/base.html', context=ctx)


@login_required
def collect_cases_select_view(request, pk):
    if request.method == 'GET':
        case = get_object_or_404(Case, id=pk)
        request.session['active_case'] = str(case.id)
        return redirect('collect_base_view')


@login_required
def get_active_case(request):
    if 'active_case' in request.session:
        try:
            return Case.objects.get(id=request.session['active_case'])
        except Exception:
            pass
    return None


class CaseCreateView(LoginRequiredMixin, CreateView):
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


class CaseDetailsView(LoginRequiredMixin, DetailView):
    model = Case
    context_object_name = 'case'
    template_name = 'pages/collect/case_details.html'


@login_required
def download_case_public_key(request, pk):
    case = Case.objects.get(id=pk)
    response = HttpResponse(case.verify_key, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename={case.name}.pem'
    return response


@login_required
def entity_exists(request, type, value):
    if request.method == 'GET':
        active_case = get_active_case(request)
        if not active_case:
            return JsonResponse([], safe=False)

        results = active_case.quick_search(value, type=type)
        data = []
        for obj in results:
            data.append({
                'id': str(obj.id),
                'type': type,
                'value': obj.value,
                'text': str(obj),
                'url': obj.get_absolute_url()
            })
            return JsonResponse(data, safe=False)
        return JsonResponse([], safe=False)


@login_required
def quick_search(request):
    active_case = get_active_case(request)
    if not active_case:
        return redirect(request.META.get('HTTP_REFERER'))
    if request.method == 'POST':
        query = request.POST['q']
        results = active_case.quick_search(query)
        return render(request, 'pages/quick_search/result_list.html', context={'results': results})

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def investigate_base_view(request):
    return render(request, 'pages/collect/base.html')


@login_required
def report_base_view(request):
    return render(request, 'pages/collect/base.html')
