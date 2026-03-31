import base64
import re
from datetime import datetime
from io import BytesIO

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils.encoding import force_str
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import CreateView, DetailView, UpdateView

from colander.core.models import DeviceMonitoring, Device, PiRogueCredentials
from colander.core.pirogue import (
    add_device_monitoring,
    delete_device_monitoring,
    register_device_monitoring_auto_stopper, add_vpn_peer, delete_vpn_peer, get_vpn_peer_config,
)
from colander.core.views.views import CaseContextMixin


class DeviceMonitoringCreateView(LoginRequiredMixin, CaseContextMixin, CreateView):
    model = DeviceMonitoring
    template_name = 'pages/device_monitoring/device_monitorings.html'
    contextual_success_url = 'device_monitoring_create_view'
    fields = [
        'description',
        'device',
        'duration',
        'pirogue',
        'ip_filter',
    ]
    object = None

    def get_form(self, form_class=None, edit=False):
        form = super(DeviceMonitoringCreateView, self).get_form(form_class)
        form.fields['device'].queryset = Device.objects.filter(case=self.request.contextual_case)
        form.fields['pirogue'].queryset = PiRogueCredentials.owned_or_shared_for_user(self.request.user)
        def custom_pirogue_label(obj):
            mode = obj.operating_mode
            if mode:
                return f"{obj} (Mode: {obj.operating_mode.capitalize()})"
            else:
                return f"{obj}"
        form.fields['pirogue'].label_from_instance = custom_pirogue_label
        form.fields['ip_filter'].label = "IP filter"
        return form

    def form_valid(self, form):
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
        ctx['device_monitorings'] = DeviceMonitoring.objects.filter(case=self.request.contextual_case)
        return ctx


class DeviceMonitoringUpdateView(DeviceMonitoringCreateView, UpdateView):
    def get_form(self, form_class=None, edit=False):
        form = super(DeviceMonitoringUpdateView, self).get_form(form_class, True)
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_editing'] = True
        return ctx


class DeviceMonitoringDetailsView(LoginRequiredMixin, CaseContextMixin, DetailView):
    model = DeviceMonitoring
    template_name = 'pages/device_monitoring/device_monitoring_details.html'
    context_object_name = 'device_monitoring'


@login_required
def device_monitoring_delete_view(request, pk):
    device_monitoring = DeviceMonitoring.objects.get(pk=pk)

    if device_monitoring:
        device_monitoring.delete()

    return redirect('device_monitoring_create_view', case_id=request.contextual_case.id)


@login_required
def device_monitoring_start_view(request, pk):
    device_monitoring = DeviceMonitoring.objects.get(pk=pk)

    result = add_device_monitoring(device_monitoring)

    if result['success']:
        device_monitoring.status = 1 # 'In progress'
        device_monitoring.started_at = datetime.now()
        device_monitoring.ended_at = None
        device_monitoring.save()

        register_device_monitoring_auto_stopper()
    else:
        messages.add_message(request, messages.ERROR, "Can't start monitoring: "+result['error'])

    referrer = request.META.get('HTTP_REFERER')
    if referrer and url_has_allowed_host_and_scheme(referrer, allowed_hosts={request.get_host()}):
        return HttpResponseRedirect(referrer)
    return HttpResponseRedirect('/')


@login_required
def device_monitoring_stop_view(request, pk):
    device_monitoring = DeviceMonitoring.objects.get(pk=pk)

    result = delete_device_monitoring(device_monitoring)

    if result['success']:
        device_monitoring.status = 2 # 'Finished'
        device_monitoring.ended_at = datetime.now()
        device_monitoring.save()
    else:
        messages.add_message(request, messages.ERROR, "Can't stop monitoring: "+result['error'])

    referrer = request.META.get('HTTP_REFERER')
    if referrer and url_has_allowed_host_and_scheme(referrer, allowed_hosts={request.get_host()}):
        return HttpResponseRedirect(referrer)
    return HttpResponseRedirect('/')


@login_required
def device_monitoring_create_vpn_peer_view(request, pk):
    device_monitoring = DeviceMonitoring.objects.get(pk=pk)

    result = add_vpn_peer(device_monitoring.pirogue.id)

    if result['success']:
        device_monitoring.peer_id = result['content']['idx']
        details_result = get_vpn_peer_config(device_monitoring.pirogue.id, device_monitoring.peer_id)
        if details_result['success']:
            ip_regex = re.compile(r"^Address = ([^/]+)", flags=re.MULTILINE | re.UNICODE)
            matches = ip_regex.search(details_result['content'])
            if matches:
                device_monitoring.ip_filter = matches.group(1)
        device_monitoring.save()
    else:
        messages.add_message(request, messages.ERROR, "Can't create VPN peer for this monitoring: "+result['error'])

    referrer = request.META.get('HTTP_REFERER')
    if referrer and url_has_allowed_host_and_scheme(referrer, allowed_hosts={request.get_host()}):
        return HttpResponseRedirect(referrer)
    return HttpResponseRedirect('/')


@login_required
def device_monitoring_get_vpn_peer_details_view(request, pk):
    device_monitoring = DeviceMonitoring.objects.get(pk=pk)

    result = get_vpn_peer_config(device_monitoring.pirogue.id, device_monitoring.peer_id)

    img = qrcode.make(result['content'])
    io = BytesIO()
    img.save(io)
    img_bytes = io.getvalue()
    encoded_qr_code = force_str(base64.b64encode(img_bytes))

    return render(request, 'device_monitoring/vpn_peer_details.html', context={
        'details': result['content'],
        'encoded_qr_code': encoded_qr_code,
    })


@login_required
def device_monitoring_release_vpn_peer_view(request, pk):
    device_monitoring = DeviceMonitoring.objects.get(pk=pk)

    result = delete_vpn_peer(device_monitoring.pirogue.id, device_monitoring.peer_id)

    print('device_monitoring_release_vpn_peer_view Result', result)

    if result['success']:
        device_monitoring.peer_id = None
        device_monitoring.ip_filter = None
        device_monitoring.save()
    else:
        messages.add_message(request, messages.ERROR, "Can't delete VPN peer on this monitoring: "+result['error'])

    referrer = request.META.get('HTTP_REFERER')
    if referrer and url_has_allowed_host_and_scheme(referrer, allowed_hosts={request.get_host()}):
        return HttpResponseRedirect(referrer)
    return HttpResponseRedirect('/')
