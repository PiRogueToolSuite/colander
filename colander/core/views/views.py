from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.contrib import messages
from django.forms.widgets import Textarea
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView
from django.views.decorators.cache import cache_page
from django.views.generic.detail import SingleObjectMixin
from django_serverless_cron.services import RunJobs

from django.views.static import serve
from os import path

from colander.core import datasets
from colander.core.forms import DocumentationForm
from colander.core.models import Entity, Case, colander_models


@login_required
def landing_view(request):
    ctx = dict()
    #ctx['cases'] = Case.get_user_cases(request.user)
    ctx['cases'] = Case.objects.filter(owner=request.user)[:3]
    #ctx['entities'] = Entity.objects.filter(owner=request.user)[:10]
    ctx['entities'] = Entity.filter_by_name_or_value(owner=request.user)[:10]
    return render(request, 'pages/home.html', context=ctx)

class CaseRequiredMixin(AccessMixin):
    """Verify that the current user has an active case."""
    case_required_message_action = "proceed"

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('active_case'):
            messages.add_message(request, messages.WARNING,
                                 f"In order to {self.case_required_message_action}, you must first select a case to work on")
            return redirect('case_create_view')
        return super().dispatch(request, *args, **kwargs)

class OwnershipRequiredMixin(SingleObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        if self.get_object().owner != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

@login_required
def evidences_view(request):
    if not request.session.get('active_case'):
        return redirect('case_create_view')
    return render(request, 'pages/evidences.html')


@login_required
def enable_documentation_editor(request):
    active_case = get_active_case(request)
    if not active_case:
        return redirect('case_create_view')
    request.session['show_documentation_editor'] = True
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def disable_documentation_editor(request):
    active_case = get_active_case(request)
    if not active_case:
        return redirect('case_create_view')
    request.session['show_documentation_editor'] = False
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def save_case_documentation_view(request, pk):
    active_case = get_active_case(request)
    if not active_case:
        return redirect('case_create_view')

    if request.method == 'POST':
        form = DocumentationForm(request.POST)
        if form.is_valid():
            active_case.documentation = form.cleaned_data.get('documentation')
            active_case.save()
    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def case_close(request):
    request.session.pop('active_case')
    return redirect('home')

@login_required
def quick_creation_view(request):
    active_case = get_active_case(request)
    if not active_case:
        return redirect('case_create_view')

    if request.method == 'POST':
        if 'create_entity' in request.POST:
            model_name = request.POST.get('model')
            type_name = request.POST.get('type')
            name = request.POST.get('name')
            model = colander_models.get(model_name)
            type_model = model.type.field.related_model
            type = type_model.objects.get(short_name=type_name)
            entity = model(
                case=active_case,
                owner=request.user,
                type=type,
                name=name
            )
            entity.save()

    models = []
    types = {}
    exclude = ['Artifact', 'Case', 'DetectionRule', 'EntityRelation', 'Event']
    for name, model in colander_models.items():
        if hasattr(model, 'type') and name not in exclude:
            models.append({
                'name': name
            })
            types[name] = [
                {'label': t.name,
                 'id': t.short_name, }
                for t in model.type.get_queryset().all()
            ]

    model_data = {
        'models': models,
        'types': types
    }

    model_data = datasets.creatable_entity_and_types

    ctx = {
        'models': model_data,
        'entities': active_case.get_all_entities(exclude_types=['Case', 'EntityRelation'])
    }

    return render(request, 'pages/quick_creation/base.html', context=ctx)


@login_required
def collect_base_view(request):
    active_case = get_active_case(request)
    if not active_case:
        messages.add_message(request, messages.WARNING,
                             "In order to collect data, you must first select a case to work on")
        return redirect('case_create_view')

    form = DocumentationForm(initial={'documentation': active_case.documentation})

    ctx = {
        'documentation_form': form,
    }
    return render(request, 'pages/collect/base.html', context=ctx)


@login_required
def collaborate_base_view(request):
    return render(request, 'pages/collaborate/base.html')


@login_required
def cases_select_view(request, pk):
    if request.method == 'GET':
        case = get_object_or_404(Case, id=pk)
        if case.can_contribute(request.user):
            request.session['active_case'] = str(case.id)
        else:
            print(f'{request.user} can not contribute to {case}!')
        #return redirect('case_create_view')
        return redirect('case_details_view', case.id)

@login_required
def get_active_case(request):
    if 'active_case' in request.session:
        try:
            case = Case.objects.get(id=request.session['active_case'])
            if case.can_contribute(request.user):
                return case
        except Exception:
            pass
    return None


class CaseCreateView(LoginRequiredMixin, CreateView):
    model = Case
    template_name = 'pages/case/base.html'
    success_url = reverse_lazy('case_create_view')
    fields = [
        'name',
        'description',
        'teams'
    ]

    def get_form(self, form_class=None):
        if self.object and self.request.user != self.object.owner:
            raise Exception("You cannot edit this case")
        form = super(CaseCreateView, self).get_form(form_class)
        form.fields['teams'].queryset = self.request.user.my_teams_as_qset
        form.fields['teams'].widget.attrs['size'] = 10
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        return form

    def form_valid(self, form):
        if form.is_valid():
            case = form.save(commit=False)
            if not hasattr(case, 'owner'):
                case.owner = self.request.user
            case.save()
            form.save_m2m()
            messages.add_message(self.request, messages.SUCCESS,
                                 f"Case {case.name} saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cases'] = Case.get_user_cases(self.request.user)
        ctx['is_editing'] = False

        if 'active_case' not in self.request.session:
            messages.add_message(self.request, messages.INFO,
                                 "Create a new case or select one from the list below.")

        return ctx


class CaseUpdateView(CaseCreateView, OwnershipRequiredMixin, UpdateView):
    def get_object(self, queryset=None):
        edited_case = super().get_object(queryset)
        if 'active_case' in self.request.session:
            ac = Case.objects.get(pk=self.request.session['active_case'])
            if edited_case != ac:
                messages.add_message(self.request, messages.WARNING,
                                     f"The edited case {edited_case.name} is not the current selected case {ac.name}")
        return edited_case

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cases'] = Case.get_user_cases(self.request.user)
        ctx['is_editing'] = True

        return ctx


class CaseDetailsView(LoginRequiredMixin, DetailView):
    model = Case
    context_object_name = 'case'
    template_name = 'pages/case/details.html'

    def get_object(self, queryset=None):
        viewed_case: Case = super().get_object(queryset)
        if viewed_case.can_contribute(self.request.user):
            if 'active_case' in self.request.session:
                ac = Case.objects.get(pk=self.request.session['active_case'])
                if viewed_case != ac:
                    messages.add_message(self.request, messages.WARNING,
                                         f"The viewed case {viewed_case.name} is not the current selected case {ac.name}")
            return viewed_case
        raise Case.DoesNotExist()

@login_required
def download_case_public_key(request, pk):
    case = Case.objects.get(id=pk)
    response = HttpResponse(case.verify_key, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename={case.name}.pem'
    return response


@login_required
def entity_exists(request):
    if request.method == 'GET':
        entity_type = request.GET.get('type', None)
        value = request.GET.get('value', None)
        active_case = get_active_case(request)
        if not active_case or not entity_type or not value:
            return JsonResponse([], safe=False)

        results = active_case.quick_search(value, type=entity_type)
        data = []
        for obj in results:
            data.append({
                'id': str(obj.id),
                'type': entity_type,
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
        results = active_case.quick_search(query, exclude_types=['Case', 'EntityRelation'])
        return render(request, 'pages/quick_search/result_list.html', context={'results': results})
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def report_base_view(request):
    return render(request, 'pages/collect/base.html')


@login_required
def forward_auth(request):
    print(request.headers)
    print(request.path)
    return HttpResponse("OK")
    # return redirect('http://spiderfoot.localhost:88')
    # return HttpResponse(status=200,headers=request.headers)

@login_required
@cache_page(60)
def cron_ish_view(request):
    if request.method == 'GET':
        RunJobs.run_all_jobs()
        return HttpResponse('')

@login_required
def vues_view(request, component_name):
    if request.method != 'GET':
        return HttpResponseNotFound("Not found")
    if "part" in request.GET:
        if request.GET.get("part") == "js":
            return render(request, f'{component_name}/{component_name}.js')
        if request.GET.get("part") == "css":
            return render(request, f'{component_name}/{component_name}.css')
        return HttpResponseNotFound("Not found")
    return render(request, f'{component_name}/{component_name}.html')
