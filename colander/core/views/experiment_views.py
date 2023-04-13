from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib import messages
from django_q.tasks import async_task

from colander.core.forms import CommentForm
from colander.core.models import PiRogueExperiment, Artifact, PiRogueExperimentAnalysis, DetectionRule
from colander.core.experiment_tasks import save_decrypted_traffic, apply_detection_rules
from colander.core.views.views import get_active_case, CaseRequiredMixin


class PiRogueExperimentCreateView(LoginRequiredMixin, CaseRequiredMixin, CreateView):
    model = PiRogueExperiment
    template_name = 'pages/collect/experiments.html'
    success_url = reverse_lazy('collect_experiment_create_view')
    fields = [
        'name',
        'pcap',
        'socket_trace',
        'aes_trace',
        'sslkeylog',
        'screencast',
        'target_artifact',
        'tlp',
        'pap'
    ]

    def get_form(self, form_class=None):
        active_case = get_active_case(self.request)
        artifacts_qset = Artifact.get_user_artifacts(self.request.user, active_case)
        form = super(PiRogueExperimentCreateView, self).get_form(form_class)
        form.fields['pcap'].queryset = artifacts_qset.filter(type__short_name='PCAP')
        form.fields['socket_trace'].queryset = artifacts_qset.filter(type__short_name='SOCKET_T')
        form.fields['aes_trace'].queryset = artifacts_qset.filter(type__short_name='CRYPTO_T')
        form.fields['sslkeylog'].queryset = artifacts_qset.filter(type__short_name='SSLKEYLOG')
        form.fields['screencast'].queryset = artifacts_qset.filter(type__short_name='VIDEO')
        form.fields['target_artifact'].queryset = artifacts_qset
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
        ctx['experiments'] = PiRogueExperiment.get_user_pirogue_dumps(self.request.user,
                                                                      self.request.session.get('active_case'))
        ctx['is_editing'] = False
        return ctx


class PiRogueExperimentUpdateView(PiRogueExperimentCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['experiments'] = PiRogueExperiment.get_user_pirogue_dumps(self.request.user,
                                                                      self.request.session.get('active_case'))
        ctx['is_editing'] = True
        return ctx


def __compute_detection_summary(analysis, direction):
    items = {}
    rules = {}
    if analysis:
        for record in analysis:
            if 'yara' in record.detections and record.result.direction == direction:
                if direction == 'outbound':
                    host = record.result.dst.host
                    ip = record.result.dst.ip
                else:
                    host = record.result.src.host
                    ip = record.result.src.ip
                process = record.result.full_stack_trace.process
                key = f'{host} - ({ip}) - {process}'
                if direction == 'outbound':
                    geo_data = record.result.dst.geoip
                else:
                    geo_data = record.result.src.geoip
                if key not in items:
                    items[key] = {
                        'host': host,
                        'ip': ip,
                        'process': process,
                        'geoip': geo_data,
                        'rules': {},
                    }
                for y in record.detections.yara:
                    if y.rule not in items[key]['rules']:
                        try:
                            rule_object = DetectionRule.objects.get(id=y.rule_id)  # ToDo: improve this
                        except Exception:
                            # This rules does not exist
                            return {}, {}
                        rules[str(rule_object.id)] = rule_object
                        items[key]['rules'][y.rule] = {
                            'rule_object': rule_object,
                            'tags': y.tags,
                            'hits': 0,
                            'dates': [],
                        }
                    items[key]['rules'][y.rule]['hits'] += 1
                    items[key]['rules'][y.rule]['dates'].append(record.timestamp)
    return items, rules


def get_detection_summary(analysis):
    inbound, r1 = __compute_detection_summary(analysis, 'inbound')
    outbound, r2 = __compute_detection_summary(analysis, 'outbound')
    r1.update(r2)
    return inbound, outbound, r1

class PiRogueExperimentDetailsView(LoginRequiredMixin, CaseRequiredMixin, DetailView):
    model = PiRogueExperiment
    template_name = 'pages/collect/experiment_details.html'
    context_object_name = 'experiment'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comment_form'] = CommentForm()
        inbound, outbound, rules = get_detection_summary(self.object.analysis)
        ctx['inbound_summary'] = inbound
        ctx['outbound_summary'] = outbound
        ctx['rules'] = rules
        return ctx

class PiRogueExperimentAnalysisReportView(LoginRequiredMixin, CaseRequiredMixin, DetailView):
    model = PiRogueExperiment
    template_name = 'experiment/analysis_report.html'
    context_object_name = 'experiment'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        inbound, outbound, rules = get_detection_summary(self.object.analysis)
        ctx['inbound_summary'] = inbound
        ctx['outbound_summary'] = outbound
        ctx['rules'] = rules
        return ctx


@login_required
def delete_experiment_view(request, pk):
    obj = PiRogueExperiment.objects.get(id=pk)
    # ToDo delete ES data too
    obj.delete()
    return redirect("collect_experiment_create_view")


@login_required
def save_decoded_content_view(request, pk):
    from elasticsearch_dsl import connections
    connections.create_connection(hosts=['elasticsearch'], timeout=20)
    if request.method == 'POST':
        try:
            analysis_id = request.POST['analysis_id']
            content = request.POST['content']
            obj = PiRogueExperiment.objects.get(id=pk)
            record = PiRogueExperimentAnalysis.get(index=obj.get_es_index(), id=analysis_id)
            record.decoded_data = content
            record.save()
            messages.success(request, "Decoded content successfully saved")
        except Exception as e:
            print(e)
    return redirect("collect_experiment_details_view", pk=pk)


@login_required
def start_decryption(request, pk):
    if PiRogueExperiment.objects.filter(id=pk).exists():
        experiment = PiRogueExperiment.objects.get(id=pk)
        if experiment.pcap and experiment.sslkeylog:
            messages.success(request, 'Traffic decryption is in progress, refresh this page in a few minutes.')
            save_decrypted_traffic(pk)
            # ToDo switch to async task
            # async_task(save_decrypted_traffic, pk)
        else:
            messages.error(request, 'Cannot decrypt traffic since your experiment does not have both a PCAP file and an SSL keylog file.')
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def start_detection(request, pk):
    if PiRogueExperiment.objects.filter(id=pk).exists():
        experiment = PiRogueExperiment.objects.get(id=pk)
        if experiment.analysis:
            messages.success(request, 'Traffic analysis is in progress, refresh this page in a few minutes.')
            apply_detection_rules(pk)
            # ToDo switch to async task
            # async_task(apply_detection_rules, pk)
        else:
            messages.error(request, 'Cannot analyze traffic since the traffic has not been decrypted yet.')
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def detection_summary(request, pk):
    if PiRogueExperiment.objects.filter(id=pk).exists():
        experiment = PiRogueExperiment.objects.get(id=pk)
        inbound = {}
        outbound = {}
        if experiment.analysis:
            for record in experiment.analysis:
                if 'yara' in record.detections:
                    rules = {}
                    host = record.result.dst.host
                    ip = record.result.dst.ip
                    key = f'{host} - ({ip})'
                    geo_data = record.result.dst.geoip
                    for y in record.detections.yara:
                        print(y)

    return redirect(request.META.get('HTTP_REFERER'))
