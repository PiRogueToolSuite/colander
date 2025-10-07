from copy import deepcopy

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.forms.widgets import RadioSelect, Textarea
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.views.generic import CreateView, UpdateView

from colander.core.exporters.csv import CsvCaseExporter
from colander.core.exporters.json import JsonCaseExporter
from colander.core.exporters.misp import MISPCaseExporter
from colander.core.exporters.stix2 import Stix2CaseExporter
from colander.core.models import DetectionRuleOutgoingFeed, DetectionRuleType, EntityOutgoingFeed, list_accepted_levels
from colander.core.serializers.generic import OutgoingFeedSerializer
from colander.core.views.views import CaseContextMixin


class DetectionRuleOutgoingFeedCreateView(LoginRequiredMixin, CaseContextMixin, CreateView):
    model = DetectionRuleOutgoingFeed
    template_name = 'pages/feeds/detection_rule_out_feeds.html'
    contextual_success_url = 'feeds_detection_rule_out_feed_create_view'
    fields = [
        'name',
        'description',
        'secret',
        'max_tlp',
        'max_pap',
        'content_type',
    ]
    case_required_message_action = "create detection rule outgoing feed"

    def get_form(self, form_class=None):
        form = super(DetectionRuleOutgoingFeedCreateView, self).get_form(form_class)
        rule_types = DetectionRuleType.objects.all()
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in rule_types
        ]
        form.fields['content_type'].label = 'Type of detection rules to be exported'
        form.fields['content_type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        return form

    def form_valid(self, form):
        if form.is_valid() and self.active_case:
            feed = form.save(commit=False)
            if not hasattr(feed, 'owner'):
                feed.owner = self.request.user
                feed.case = self.active_case
            feed.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['feeds'] = DetectionRuleOutgoingFeed.get_user_detection_rule_out_feeds(self.request.user, self.active_case)
        ctx['is_editing'] = False
        return ctx


class DetectionRuleOutgoingFeedUpdateView(DetectionRuleOutgoingFeedCreateView, UpdateView):
    case_required_message_action = "update feed"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['feeds'] = DetectionRuleOutgoingFeed.get_user_detection_rule_out_feeds(self.request.user, self.active_case)
        ctx['is_editing'] = True
        return ctx


@login_required
def delete_detection_rule_out_feed_view(request, pk):
    obj = DetectionRuleOutgoingFeed.objects.get(id=pk)
    obj.delete()
    return redirect("feeds_detection_rule_out_feed_create_view", case_id=request.contextual_case.id)


class EntityOutgoingFeedCreateView(LoginRequiredMixin, CaseContextMixin, CreateView):
    model = EntityOutgoingFeed
    template_name = 'pages/feeds/entity_out_feeds.html'
    contextual_success_url = 'feeds_entity_out_feed_create_view'
    fields = [
        'name',
        'description',
        'secret',
        'max_tlp',
        'max_pap',
        'misp_org_name',
        'misp_org_id',
        'content_type',
    ]
    case_required_message_action = "create detection rule outgoing feed"

    def get_form(self, form_class=None):
        form = super(EntityOutgoingFeedCreateView, self).get_form(form_class)
        choices = []
        for m, l in form.fields['content_type'].choices:
            label = l.replace('core | ', '')
            label = label.title()
            choices.append((m, label))
        form.fields['content_type'].choices = choices
        form.fields['content_type'].label = 'Type of entities to be exported'
        form.fields['content_type'].widget.attrs = {'size': 10}
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        return form

    def form_valid(self, form):
        if form.is_valid() and self.active_case:
            feed = form.save(commit=False)
            if not hasattr(feed, 'owner'):
                feed.owner = self.request.user
                feed.case = self.active_case
            feed.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['feeds'] = EntityOutgoingFeed.get_user_entity_out_feeds(self.request.user, self.active_case)
        ctx['is_editing'] = False
        return ctx


class EntityOutgoingFeedUpdateView(EntityOutgoingFeedCreateView, UpdateView):
    case_required_message_action = "update feed"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['feeds'] = EntityOutgoingFeed.get_user_entity_out_feeds(self.request.user, self.active_case)
        ctx['is_editing'] = True
        return ctx


@login_required
def delete_entity_out_feed_view(request, pk):
    obj = EntityOutgoingFeed.objects.get(id=pk)
    obj.delete()
    return redirect("feeds_entity_out_feed_create_view", case_id=request.contextual_case.id)


def outgoing_entities_feed_view(request, pk):
    try:
        feed = EntityOutgoingFeed.objects.get(id=pk)
    except EntityOutgoingFeed.DoesNotExist:
        return HttpResponse('', status=404, content_type='text/plain')

    is_authenticated = request.user.is_authenticated
    is_authenticated |= request.GET.get('secret', '') == feed.secret
    is_authenticated |= request.headers.get('X-Colander-Feed', '') == f'Secret {feed.secret}'
    if not is_authenticated:
        return HttpResponse('', status=503, content_type='text/plain')

    if 'info' in request.GET:
        return JsonResponse(OutgoingFeedSerializer(feed).data, json_dumps_params={})

    requested_format = request.GET.get('format', 'json')
    if requested_format not in ['json', 'stix2', 'misp', 'csv']:
        requested_format = 'json'

    cache_key = f'feed_{feed.id}_{requested_format}_{feed.secret}'
    cached = cache.get(cache_key)
    if cached:
        if requested_format in ['json', 'stix2', 'misp']:
            return JsonResponse(cached, json_dumps_params={}, headers={'X-Colander-Feed-Cache': 'hit'})
        elif requested_format == 'csv':
            return HttpResponse(cached, status=200, content_type='text/plain', headers={'X-Colander-Feed-Cache': 'hit'})

    dummy_case = deepcopy(feed.case)
    tlp_levels = list_accepted_levels(feed.max_tlp)
    pap_levels = list_accepted_levels(feed.max_pap)

    if feed.case.tlp not in tlp_levels or feed.case.pap not in pap_levels:
        dummy_case.name = '[REDACTED]'
        dummy_case.description = '[REDACTED]'

    entities = feed.get_entities()
    if requested_format == 'json':
        exporter = JsonCaseExporter(dummy_case, entities)
        export = exporter.export()
        cache.set(cache_key, export, 3600)
        return JsonResponse(export, json_dumps_params={}, headers={'X-Colander-Feed-Cache': 'miss'})
    elif requested_format == 'stix2':
        exporter = Stix2CaseExporter(dummy_case, feed, entities)
        export = exporter.export()
        cache.set(cache_key, export, 3600)
        return JsonResponse(export, json_dumps_params={}, headers={'X-Colander-Feed-Cache': 'miss'})
    elif requested_format == 'misp':
        if not feed.misp_org_id or not feed.misp_org_name:
            return HttpResponse('Unavailable', status=404, content_type='text/plain')
        else:
            exporter = MISPCaseExporter(dummy_case, feed, entities)
            export = exporter.export()
            cache.set(cache_key, export, 3600)
            return JsonResponse(export, json_dumps_params={}, headers={'X-Colander-Feed-Cache': 'miss'})
    elif requested_format == 'csv':
        exporter = CsvCaseExporter(dummy_case, entities)
        export = exporter.export()
        cache.set(cache_key, export, 3600)
        return HttpResponse(export, status=200, content_type='text/plain', headers={'X-Colander-Feed-Cache': 'miss'})
    return HttpResponse('', status=404, content_type='text/plain')


def outgoing_detection_rules_feed_view(request, pk):
    try:
        feed = DetectionRuleOutgoingFeed.objects.get(id=pk)
    except DetectionRuleOutgoingFeed.DoesNotExist:
        return HttpResponse('', status=503, content_type='text/plain')

    is_authenticated = request.user.is_authenticated
    is_authenticated |= request.GET.get('secret', '') == feed.secret
    is_authenticated |= request.headers.get('X-Colander-Feed', '') == f'Secret {feed.secret}'
    if not is_authenticated:
        return HttpResponse('', status=503, content_type='text/plain')

    if 'info' in request.GET:
        return JsonResponse(OutgoingFeedSerializer(feed).data, json_dumps_params={})

    cache_key = f'feed_{feed.id}_{feed.secret}'
    cached = cache.get(cache_key)

    filename = f'Colander_{slugify(feed.name)}_{feed.id}_{feed.content_type.short_name.lower()}.rules'
    if cached:
        response = HttpResponse(cached, content_type='application/octet-stream')
        response['X-Colander-Feed-Cache'] = 'hit'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    rules = feed.get_entities()
    export = '\n'.join([r.content for r in rules.all()])
    cache.set(cache_key, export, 3600)
    response = HttpResponse(export, content_type='application/octet-stream')
    response['X-Colander-Feed-Cache'] = 'miss'
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response
