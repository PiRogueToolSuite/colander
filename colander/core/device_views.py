from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.widgets import Textarea, RadioSelect
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, UpdateView, DetailView

from colander.core.forms import CommentForm
from colander.core.models import Device, DeviceType
from colander.core.views import get_active_case, CaseRequiredMixin


class DeviceCreateView(LoginRequiredMixin, CaseRequiredMixin, CreateView):
    model = Device
    template_name = 'pages/collect/devices.html'
    success_url = reverse_lazy('collect_device_create_view')
    fields = [
        'type',
        'name',
        'description',
        'operated_by',
        'source_url',
        'tlp',
        'pap'
    ]

    def get_form(self, form_class=None):
        form = super(DeviceCreateView, self).get_form(form_class)
        device_types = DeviceType.objects.all()
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in device_types
        ]
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        return form

    def form_valid(self, form):
        active_case = get_active_case(self.request)
        if form.is_valid() and active_case:
            device = form.save(commit=False)
            device.owner = self.request.user
            device.case = active_case
            device.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['devices'] = Device.get_user_devices(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = False
        return ctx


class DeviceUpdateView(DeviceCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['devices'] = Device.get_user_devices(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = True
        return ctx


class DeviceDetailsView(LoginRequiredMixin, CaseRequiredMixin, DetailView):
    model = Device
    template_name = 'pages/collect/device_details.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comment_form'] = CommentForm()
        return ctx
