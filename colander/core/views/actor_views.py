from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.widgets import Textarea, RadioSelect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, UpdateView, DetailView

from colander.core.forms import CommentForm
from colander.core.models import Actor, ActorType
from colander.core.views.views import get_active_case, CaseRequiredMixin


class ActorCreateView(LoginRequiredMixin, CaseRequiredMixin, CreateView):
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
        active_case = get_active_case(self.request)
        if form.is_valid() and active_case:
            actor = form.save(commit=False)
            if not hasattr(actor, 'owner'):
                actor.owner = self.request.user
                actor.case = active_case
            actor.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['actors'] = Actor.get_user_actors(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = False
        return ctx


class ActorUpdateView(ActorCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['actors'] = Actor.get_user_actors(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = True
        return ctx


class ActorDetailsView(LoginRequiredMixin, CaseRequiredMixin, DetailView):
    model = Actor
    template_name = 'pages/collect/actor_details.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comment_form'] = CommentForm()
        return ctx


@login_required
def delete_actor_view(request, pk):
    obj = Actor.objects.get(id=pk)
    obj.delete()
    return redirect("collect_actor_create_view")
