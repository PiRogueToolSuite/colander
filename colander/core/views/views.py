import json
from urllib.parse import urlparse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.core.files.base import ContentFile
from django.forms.widgets import Textarea
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import resolve, reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_page, cache_control
from django.views.generic import CreateView, DetailView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django_serverless_cron.services import RunJobs

from colander.core import datasets
from colander.core.forms import DocumentationForm
from colander.core.models import (
    Case,
    DetectionRuleOutgoingFeed,
    Entity,
    EntityOutgoingFeed,
    colander_models,
    color_scheme,
    icons,
)
from colander.core.templatetags.colander_tags import model_name


@login_required
def landing_view(request):
    ctx = dict()
    #ctx['cases'] = Case.get_user_cases(request.user)
    ctx['cases'] = Case.objects.filter(owner=request.user)[:3]
    #ctx['entities'] = Entity.objects.filter(owner=request.user)[:10]
    ctx['entities'] = Entity.filter_by_name_or_value(owner=request.user)[:10]
    ctx['search_results'] = False
    if request.method == 'POST':
        query = request.POST.get('q', '')
        ctx['entities'] = do_search(query, Case.get_user_cases(request.user))
        ctx['search_results'] = True
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


class CaseContextMixin(AccessMixin):
    """Verify that the current user has an active case."""
    case_required_message_action = "proceed"
    contextual_success_url = ''
    active_case = None

    def dispatch(self, request, *args, **kwargs):
        # print("CaseContextMixin", "dispatch", request, hasattr(request, 'contextual_case') )
        if hasattr(request, 'contextual_case') and request.contextual_case.can_contribute(request.user):
            self.active_case = request.contextual_case
            return super().dispatch(request, *args, **kwargs)
        else:
            return self.handle_no_permission()

    def get_success_url(self):
        #print("get_success_url", self.active_case)
        return reverse(self.contextual_success_url, kwargs={'case_id': self.active_case.id})


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
def save_case_documentation_view(request):
    #active_case = get_active_case(request)
    active_case = request.contextual_case
    if not active_case:
        return redirect('case_create_view')

    if request.method == 'POST':
        form = DocumentationForm(request.POST)
        if form.is_valid():
            active_case.documentation = form.cleaned_data.get('documentation')
            active_case.save()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def export_case_documentation_as_markdown_view(request):
    #case = Case.objects.get(pk=pk)
    case = request.contextual_case
    if not case:
        return redirect('document_case_write_doc_view')
    if not case.can_contribute(request.user):
        return HttpResponseForbidden("Not allowed")

    content = ""
    if case.documentation is not None:
        content = case.documentation

    file_to_send = ContentFile(content.encode(encoding="UTF-8"))
    response = HttpResponse(file_to_send, 'text/markdown')
    response['Content-Length'] = file_to_send.size
    response['Content-Disposition'] = f'attachment; filename="{case.name}.md"'
    return response


@login_required
def case_close(request):
    request.session.pop('active_case')
    return redirect('home')


@login_required
def quick_creation_view(request):
    active_case = request.contextual_case
    if not active_case:
        return redirect('case_create_view')

    search_results = False
    entities_list = []
    model_data = datasets.creatable_entity_and_types

    if request.method == 'POST':
        if 'create_entity' in request.POST:
            model_name = request.POST.get('super_type')  # OBSERVABLE
            type_name = request.POST.get('type')  # DOMAIN
            names = request.POST.get('name')
            model = {t.upper(): m for t, m in colander_models.items()}.get(model_name.upper())
            type_model = model.type.field.related_model
            type = type_model.objects.get(short_name=type_name)
            for name in names.splitlines():
                name = name.strip()
                if name and model.objects.filter(case=active_case, type=type, name=name).count() == 0:
                    entity = model(
                        case=active_case,
                        owner=request.user,
                        type=type,
                        name=name,
                        tlp=active_case.tlp,
                        pap=active_case.pap
                    )
                    entity.save()
                    messages.add_message(request, messages.SUCCESS, f"The {model_name.title()} named {name} of type {type} successfully created.")
                else:
                    messages.add_message(request, messages.WARNING, f"The {model_name.title()} named {name} of type {type} already exists.")
        else:
            query = request.POST.get('q', '')
            entities_list = do_search(query, [active_case])
            search_results = True

    if not search_results:
        entities_list = active_case.get_all_entities(exclude_types=['Case', 'EntityRelation'])

    ctx = {
        'active_case': active_case,
        'models': model_data,
        'entities': entities_list,
        'search_results': search_results
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
def get_active_case(request, case_id=None):
    print("Case id:", case_id)
    if case_id:
        try:
            case = Case.objects.get(id=case_id)
            if case.can_contribute(request.user):
                return case
        except Exception:
            pass
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
        'teams',
        'tlp',
        'pap',
    ]

    def get_form(self, form_class=None):
        if self.object and self.request.user != self.object.owner:
            raise Exception("You cannot edit this case")
        form = super(CaseCreateView, self).get_form(form_class)
        form.fields['teams'].queryset = self.request.user.my_teams_as_qset
        form.fields['teams'].widget.attrs['size'] = 10
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20, 'placeholder': _("No case description yet.")})
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
    if request.method == 'POST':
        case_id = request.POST.get('case_id', None)
        entity_type = request.POST.get('type', None)
        value = request.POST.get('value', None)

        if not case_id:
            return JsonResponse([], safe=False)

        active_case = Case.objects.get(pk=case_id)

        if not active_case:
            return JsonResponse([], safe=False)

        if not entity_type or not value:
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

    # Inject contextual case (if any) into requested vues parts
    referer = request.META.get("HTTP_REFERER", None) or "/"
    parsed = urlparse(referer)
    func, args, kwargs = resolve(parsed[2])
    ctx = {}
    if 'case_id' in kwargs:
        case = Case.objects.get(pk=kwargs['case_id'])
        if case and case.can_contribute(request.user):
            ctx['contextual_case'] = case

    if "part" in request.GET:
        if request.GET.get("part") == "js":
            return render(request, f'{component_name}/{component_name}.js',
                          content_type='text/javascript', context=ctx)
        if request.GET.get("part") == "css":
            return render(request, f'{component_name}/{component_name}.css',
                          content_type='text/css', context=ctx)
        return HttpResponseNotFound("Not found")

    return render(request, f'{component_name}/{component_name}.html', context=ctx)


@login_required
def case_workspace_view(request):
    active_case = request.contextual_case
    ctx = {
      'active_case': active_case,
    }
    return render(request, 'pages/workspace/base.html', context=ctx)


@login_required
def feeds_view(request):
    feeds = []
    feeds.extend( DetectionRuleOutgoingFeed.get_user_detection_rule_out_feeds(request.user, request.contextual_case) )
    feeds.extend( EntityOutgoingFeed.get_user_entity_out_feeds(request.user, request.contextual_case) )
    ctx = {
        'feeds': feeds
    }
    return render(request, 'pages/feeds/base.html', context=ctx)


def do_search(query, cases):
    overall_results = []
    for c in cases:
        results = c.quick_search(query, exclude_types=['Case', 'EntityRelation'])
        overall_results.extend(results)
    return overall_results


@login_required
def quick_search(request):
    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER'))

    case_id = request.POST.get('case_id', None)
    query = request.POST.get('q', '')

    cases = []
    if case_id:
        case = Case.objects.get(pk=case_id)
        if case and case.can_contribute(request.user):
            cases.append(case)
    else:
        cases = Case.get_user_cases(request.user)

    results = do_search(query, cases)
    return render(request, 'pages/quick_search/result_list.html', context={'results': results})

    #return redirect(request.META.get('HTTP_REFERER'))


@login_required
def overall_search(request):
    if request.method != 'POST':
        return JsonResponse([], safe=False)

    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    query = body.get('query', '')
    case_id_ctx = body.get('case_id', None)

    if not query:
        return JsonResponse([], safe=False)

    cases = []
    if case_id_ctx:
        case_ctx = Case.objects.get(pk=case_id_ctx)
        if case_ctx.can_contribute(request.user):
            cases.append(case_ctx)
    else:
        cases = Case.get_user_cases(request.user)

    overall_results = []
    for c in cases:
        results = c.quick_search(query, exclude_types=['Case', 'EntityRelation'])
        overall_results.extend(results)

    serializable_results = []
    for r in overall_results:
        rr = {
            'case': r.case.name,
            'name': r.name,
            'color': color_scheme[type(r)],
            'icon': icons[type(r)],
            'model_name': model_name(r).capitalize(),
            'type': r.type.name if hasattr(r, 'type') else None,
            'type_icon': r.type.nf_icon if hasattr(r, 'type') else None,
            'url': r.absolute_url,
            'tlp': r.tlp,
            'pap': r.pap,
            'is_malicious': False,
        }
        if hasattr(r, 'associated_threat'):
             rr['is_malicious'] = bool(r.associated_threat)
        if hasattr(r, 'attributes'):
            if r.attributes:
                if 'is_malicious' in r.attributes:
                    rr['is_malicious'] = r.attributes['is_malicious'] == "1" or r.attributes['is_malicious'] == "True"
        serializable_results.append(rr)

    return JsonResponse(serializable_results, safe=False)
