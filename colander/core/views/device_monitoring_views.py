from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views.generic import CreateView, DetailView

from colander.core.models import DeviceMonitoring, Device, PiRogueCredentials
from colander.core.views.views import CaseContextMixin


class DeviceMonitoringCreateView(LoginRequiredMixin, CaseContextMixin, CreateView):
    model = DeviceMonitoring
    template_name = 'device_monitoring/create_update.html'
    contextual_success_url = 'device_monitoring_view'
    fields = [
        'description',
        'device',
        'duration',
        'pirogue',
    ]
    object = None

    def get_form(self, form_class=None, edit=False):
        form = super(DeviceMonitoringCreateView, self).get_form(form_class)
        form.fields['device'].queryset = Device.objects.filter(case=self.request.contextual_case)
        form.fields['pirogue'].queryset = PiRogueCredentials.owned_or_shared_for_user(self.request.user)

        # Work-Around QuerySet.get(...) can't be called with filters after union()
        if 'pirogue' in self.request.POST:
            form.fields['pirogue'].queryset = PiRogueCredentials.owned_or_shared_for_user(self.request.user)
        return form

    def form_valid(self, form):
        print("DeviceMonitoringCreateView form_valid")
        if form.is_valid():
            device_monitoring = form.save(commit=False)
            print("DeviceMonitoringCreateView is_valid", device_monitoring)
            if not hasattr(device_monitoring, 'owner'):
                device_monitoring.owner = self.request.user
            if not hasattr(device_monitoring, 'case'):
                device_monitoring.case = self.active_case

            device_monitoring.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_editing'] = False
        return ctx


class DeviceMonitoringUpdateView(DeviceMonitoringCreateView):
    def get_form(self, form_class=None, edit=False):
        form = super(DeviceMonitoringUpdateView, self).get_form(form_class, True)
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_editing'] = True
        return ctx

class DeviceMonitoringDetailsView(LoginRequiredMixin, CaseContextMixin, DetailView):
    model = DeviceMonitoring
    template_name = 'device_monitoring/details.html'


@login_required
def landing_view(request):
    view = DeviceMonitoringCreateView(request=request)
    return render(request,
                  'pages/device_monitoring/landing.html',
                  context=view.get_context_data(
                    device_monitorings=DeviceMonitoring.objects.all(),
                  ))


@login_required
def device_monitoring_delete_view(request, pk):
    return redirect('device_monitoring_view', case_id=request.contextual_case.id)
