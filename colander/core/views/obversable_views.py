from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.widgets import Textarea, RadioSelect
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, UpdateView, DetailView
from django_q.tasks import async_task

from colander.core.forms import CommentForm
from colander.core.models import Observable, ObservableRelation, ObservableType, Artifact, Threat, Actor
from colander.core.observable_tasks import capture_url
from colander.core.views.views import CaseContextMixin


class ObservableCreateView(LoginRequiredMixin, CaseContextMixin, CreateView):
    model = Observable
    template_name = 'pages/collect/observables.html'
    contextual_success_url = 'collect_observable_create_view'
    #success_url = reverse_lazy('collect_observable_create_view')
    fields = [
        'type',
        'extracted_from',
        'associated_threat',
        'operated_by',
        'name',
        'description',
        'tlp',
        'pap',
        'source_url',
    ]
    case_required_message_action = "create observables"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['observables'] = Observable.get_user_observables(self.request.user, self.active_case)
        ctx['is_editing'] = False
        return ctx

    def get_form(self, form_class=None, edit=False):
        observable_types = ObservableType.objects.all()
        #active_case = self.request.session.get('active_case')
        #active_case = get_active_case(self.request)
        artifact_qset = Artifact.get_user_artifacts(self.request.user, self.active_case)
        threat_qset = Threat.get_user_threats(self.request.user, self.active_case)
        actor_qset = Actor.get_user_actors(self.request.user, self.active_case)
        form = super(ObservableCreateView, self).get_form(form_class)
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in observable_types
        ]
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        form.fields['extracted_from'].queryset = artifact_qset
        form.fields['associated_threat'].queryset = threat_qset
        form.fields['operated_by'].queryset = actor_qset

        if not edit:
            form.initial['tlp'] = self.active_case.tlp
            form.initial['pap'] = self.active_case.pap

        return form

    def form_valid(self, form):
        #active_case = get_active_case(self.request)
        if form.is_valid() and self.active_case:
            observable = form.save(commit=False)
            if not hasattr(observable, 'owner'):
                observable.owner = self.request.user
                observable.case = self.active_case
            observable.save()
            form.save_m2m()
        return super().form_valid(form)


class ObservableUpdateView(ObservableCreateView, UpdateView):
    case_required_message_action = "update observable"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['observables'] = Observable.get_user_observables(self.request.user, self.active_case)
        ctx['is_editing'] = True
        return ctx

    def get_form(self, form_class=None):
        return super().get_form(form_class, True)


class ObservableDetailsView(LoginRequiredMixin, CaseContextMixin, DetailView):
    model = Observable
    template_name = 'pages/collect/observable_details.html'
    case_required_message_action = "view observable details"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comment_form'] = CommentForm()
        return ctx


class ObservableRelationCreateView(LoginRequiredMixin, CaseContextMixin, CreateView):
    model = ObservableRelation
    template_name = 'pages/collect/relations.html'
    contextual_success_url = 'collect_relation_create_view'
    #success_url = reverse_lazy('collect_relation_create_view')
    fields = [
        'name',
        'observable_from',
        'observable_to',
        'tlp',
        'pap',
        'description',
    ]
    case_required_message_action = "create observable relations"

    def get_form(self, form_class=None):
        observable_qset = Observable.get_user_observables(self.request.user, self.active_case)
        form = super(ObservableRelationCreateView, self).get_form(form_class)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        form.fields['observable_from'].queryset = observable_qset
        form.fields['observable_to'].queryset = observable_qset
        return form

    def form_valid(self, form):
        #active_case = get_active_case(self.request)
        if form.is_valid() and self.active_case:
            relation = form.save(commit=False)
            relation.owner = self.request.user
            relation.case = self.active_case
            relation.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['relations'] = ObservableRelation.get_user_relations(self.request.user,
                                                                 self.active_case)
        ctx['is_editing'] = False
        return ctx


class ObservableRelationUpdateView(ObservableRelationCreateView, UpdateView):
    case_required_message_action = "update observable relation"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['relations'] = ObservableRelation.get_user_relations(self.request.user,
                                                                 self.active_case)
        ctx['is_editing'] = True
        return ctx


class ObservableRelationDetailsView(LoginRequiredMixin, CaseContextMixin, DetailView):
    model = ObservableRelation
    context_object_name = 'relation'
    template_name = 'pages/collect/relation_details.html'
    case_required_message_action = "view observable relation details"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comment_form'] = CommentForm()
        return ctx


@login_required
def delete_observable_view(request, pk):
    obj = Observable.objects.get(id=pk)
    obj.delete()
    return redirect("collect_observable_create_view", case_id=request.contextual_case.id)


@login_required()
def capture_observable_view(request, pk):
    obj = Observable.objects.get(id=pk)
    if obj.type.short_name == 'URL':
        async_task(capture_url, obj.id)
        messages.success(request, 'The capture of this URL has started, refresh this page in a few minutes.')
    return redirect(request.META.get('HTTP_REFERER'))
