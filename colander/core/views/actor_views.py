from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.widgets import RadioSelect, Textarea
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, DetailView, UpdateView

from colander.core.forms import CommentForm
from colander.core.forms.widgets import ThumbnailFileInput
from colander.core.models import Actor, ActorType
from colander.core.views.views import CaseContextMixin


class ActorCreateView(LoginRequiredMixin, CaseContextMixin, CreateView):
    model = Actor
    template_name = 'pages/collect/actors.html'
    contextual_success_url = 'collect_actor_create_view'
    fields = [
        'type',
        'name',
        'description',
        'source_url',
        'tlp',
        'pap',
        'thumbnail',
    ]
    case_required_message_action = "create actors"

    def get_form(self, form_class=None, edit=False):
        form = super(ActorCreateView, self).get_form(form_class)
        actor_types = ActorType.objects.all()
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in actor_types
        ]
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        form.fields['thumbnail'].widget = ThumbnailFileInput()
        if self.object and self.object.thumbnail:
            form.fields['thumbnail'].widget.thumbnail_url = self.object.thumbnail_url

        if not edit:
            form.initial['tlp'] = self.active_case.tlp
            form.initial['pap'] = self.active_case.pap

        return form

    def form_valid(self, form):
        if form.is_valid() and self.active_case:
            actor = form.save(commit=False)
            if not hasattr(actor, 'owner'):
                actor.owner = self.request.user
                actor.case = self.active_case
            actor.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['entity_types'] = {str(t.id): {'type': t.short_name, 'attributes': t.default_attributes} for t in ActorType.objects.all()}
        ctx['actors'] = Actor.get_user_actors(self.request.user, self.active_case)
        ctx['is_editing'] = False
        return ctx


class ActorUpdateView(ActorCreateView, UpdateView):
    case_required_message_action = "update actor"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_editing'] = True
        return ctx

    def get_form(self, form_class=None):
        return super().get_form(form_class, True)


class ActorDetailsView(LoginRequiredMixin, CaseContextMixin, DetailView):
    model = Actor
    template_name = 'pages/collect/actor_details.html'
    case_required_message_action = "view actor details"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comment_form'] = CommentForm()
        return ctx


@login_required
def delete_actor_view(request, pk):
    obj = Actor.objects.get(id=pk)
    obj.delete()
    return redirect("collect_actor_create_view", case_id=request.contextual_case.id)
