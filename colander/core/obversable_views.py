from django.forms.widgets import Textarea, RadioSelect
from django.forms.widgets import Textarea, RadioSelect
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, UpdateView, DetailView

from colander.core.models import Observable, ObservableRelation, ObservableType, Artifact
from colander.core.views import get_active_case


class ObservableCreateView(CreateView):
    model = Observable
    template_name = 'pages/collect/observables.html'
    success_url = reverse_lazy('collect_observable_create_view')
    fields = [
        'type',
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
        ctx['observables'] = Observable.get_user_observables(self.request.user, self.request.session.get('active_case'))
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
        form.fields['extracted_from'].queryset = Artifact.get_user_artifacts(self.request.user, self.request.session.get('active_case'))
        return form

    def form_valid(self, form):
        active_case = get_active_case(self.request)
        if form.is_valid() and active_case:
            observable = form.save(commit=False)
            observable.owner = self.request.user
            observable.case = active_case
            artifact = form.cleaned_data['extracted_from']
            if artifact:
                observable.case = artifact.case
            observable.save()
            form.save_m2m()
        return super().form_valid(form)


class ObservableUpdateView(ObservableCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['observables'] = Observable.get_user_observables(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = True
        return ctx


class ObservableDetailsView(DetailView):
    model = Observable
    template_name = 'pages/collect/observable_details.html'


class ObservableRelationCreateView(CreateView):
    model = ObservableRelation
    template_name = 'pages/collect/relations.html'
    success_url = reverse_lazy('collect_relation_create_view')
    fields = [
        'name',
        'observable_from',
        'observable_to',
        'tlp',
        'pap',
        'description',
    ]

    def get_form(self, form_class=None):
        observable_qset = Observable.get_user_observables(self.request.user, self.request.session.get('active_case'))
        form = super(ObservableRelationCreateView, self).get_form(form_class)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        form.fields['observable_from'].queryset = observable_qset
        form.fields['observable_to'].queryset = observable_qset
        return form

    def form_valid(self, form):
        active_case = get_active_case(self.request)
        if form.is_valid() and active_case:
            relation = form.save(commit=False)
            relation.owner = self.request.user
            relation.case = active_case
            relation.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['relations'] = ObservableRelation.get_user_relations(self.request.user,
                                                                 self.request.session.get('active_case'))
        ctx['is_editing'] = False
        return ctx


class ObservableRelationUpdateView(ObservableRelationCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['relations'] = ObservableRelation.get_user_relations(self.request.user,
                                                                 self.request.session.get('active_case'))
        ctx['is_editing'] = True
        return ctx


class ObservableRelationDetailsView(DetailView):
    model = ObservableRelation
    context_object_name = 'relation'
    template_name = 'pages/collect/relation_details.html'
