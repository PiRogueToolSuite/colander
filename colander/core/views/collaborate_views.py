from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView

from colander.core.models import ColanderTeam
from colander.core.views.views import CaseRequiredMixin


class ColanderTeamCreateView(LoginRequiredMixin, CaseRequiredMixin, CreateView):
    model = ColanderTeam
    template_name = 'pages/collaborate/teams.html'
    success_url = reverse_lazy('collaborate_team_create_view')
    fields = [
        'name',
        'contributors',
    ]

    def get_form(self, form_class=None):
        form = super(ColanderTeamCreateView, self).get_form(form_class)
        return form

    def form_valid(self, form):
        if form.is_valid():
            team = form.save(commit=False)
            team.owner = self.request.user
            team.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['teams'] = ColanderTeam.get_user_teams(self.request.user)
        ctx['is_editing'] = False
        return ctx


class ColanderTeamUpdateView(ColanderTeamCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['teams'] = ColanderTeam.get_user_teams(self.request.user)
        ctx['is_editing'] = True
        return ctx


class ColanderTeamDetailsView(LoginRequiredMixin, CaseRequiredMixin, DetailView):
    model = ColanderTeam
    template_name = 'pages/collaborate/team_details.html'
    context_object_name = 'team'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx


@login_required
def delete_team_view(request, pk):
    obj = ColanderTeam.objects.get(id=pk)
    obj.delete()
    return redirect("collaborate_team_create_view")
