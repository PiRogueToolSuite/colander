from functools import partial

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.forms.widgets import Textarea
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, UpdateView

from colander.core.models import PiRogueCredentials, PiRogueStatus
from colander.core.pirogue import unschedule_pirogue_status_retrieval, \
    register_pirogue_status_retrieval_schedule, _proceed_pirogue_status_retrieval


class PiRogueCredentialsCreateView(LoginRequiredMixin, CreateView):
    model = PiRogueCredentials
    template_name = 'pages/pirogue/credentials.html'
    success_url = reverse_lazy('pirogue_credentials_base_view')
    fields = [
        'host',
        'port',
        'token',
        'has_public_visibility',
        'friendly_name',
        'certificate',
    ]

    def get_form(self, form_class=None):
        form = super(PiRogueCredentialsCreateView, self).get_form(form_class)
        form.fields['certificate'].widget = Textarea(
            attrs={'rows': 18,
                   'placeholder': "-----BEGIN CERTIFICATE-----\n" +
                                  _("Paste certificate here.") +
                                  "\n-----END CERTIFICATE-----"
                   },

        )
        if self.object:
            form.fields['certificate'].disabled = self.object.has_public_visibility
        return form

    def form_valid(self, form):
        if form.is_valid():
            pirogue_credential = form.save(commit=False)
            if not hasattr(pirogue_credential, 'owner'):
                pirogue_credential.owner = self.request.user
            pirogue_credential.save()
            form.save_m2m()
            messages.add_message(self.request, messages.SUCCESS,
                                 f"PiRogue Credentials {pirogue_credential.host}:{pirogue_credential.port} saved.")

            transaction.on_commit(partial(register_pirogue_status_retrieval_schedule, pirogue_credential))

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['credentials'] = PiRogueCredentials.owned_or_shared_for_user(self.request.user)
        ctx['is_editing'] = False
        return ctx


class PiRogueCredentialsDetailsView(LoginRequiredMixin, DetailView):
    model = PiRogueCredentials
    template_name = 'pages/pirogue/credentials_details.html'
    context_object_name = 'pirogue_credentials'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status'] = PiRogueStatus.objects.filter(pirogue_credentials=self.object).order_by('-reported_at').all()
        return ctx


class PiRogueCredentialsUpdateView(PiRogueCredentialsCreateView, UpdateView):

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_editing'] = True
        return ctx


@login_required
def pirogue_credentials_delete_view(request, pk):
    obj = PiRogueCredentials.objects.get(id=pk)

    if obj.owner != request.user:
        return HttpResponseForbidden()

    transaction.on_commit(partial(unschedule_pirogue_status_retrieval, pk))

    obj.delete()

    return redirect("pirogue_credentials_base_view")


@login_required
def pirogue_credentials_check_status_view(request, pk):
    obj = PiRogueCredentials.objects.get(id=pk)

    if obj.owner != request.user:
        return HttpResponseForbidden()

    _proceed_pirogue_status_retrieval(pk)

    referrer = request.META.get('HTTP_REFERER')
    if referrer and url_has_allowed_host_and_scheme(referrer, allowed_hosts={request.get_host()}):
        return HttpResponseRedirect(referrer)
    return HttpResponseRedirect('/')
