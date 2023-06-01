from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.widgets import RadioSelect, Textarea
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, UpdateView
from django.core.cache import cache

from colander.core.exporters.csv import CsvCaseExporter
from colander.core.exporters.json import JsonCaseExporter
from colander.core.models import DetectionRuleOutgoingFeed, \
    DetectionRuleType, EntityOutgoingFeed
from colander.core.serializers.generic import OutgoingFeedSerializer
from colander.core.views.views import get_active_case, CaseRequiredMixin


class DetectionRuleOutgoingFeedCreateView(LoginRequiredMixin, CaseRequiredMixin, CreateView):
    model = DetectionRuleOutgoingFeed
    template_name = 'pages/collaborate/detection_rule_out_feeds.html'
    success_url = reverse_lazy('collaborate_detection_rule_out_feed_create_view')
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
        active_case = get_active_case(self.request)
        if form.is_valid() and active_case:
            feed = form.save(commit=False)
            if not hasattr(feed, 'owner'):
                feed.owner = self.request.user
                feed.case = active_case
            feed.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['feeds'] = DetectionRuleOutgoingFeed.get_user_detection_rule_out_feeds(self.request.user,
                                                                                   self.request.session.get(
                                                                                       'active_case'))
        ctx['is_editing'] = False
        return ctx


class DetectionRuleOutgoingFeedUpdateView(DetectionRuleOutgoingFeedCreateView, UpdateView):
    case_required_message_action = "update feed"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['feeds'] = DetectionRuleOutgoingFeed.get_user_detection_rule_out_feeds(self.request.user,
                                                                                   self.request.session.get(
                                                                                       'active_case'))
        ctx['is_editing'] = True
        return ctx


@login_required
def delete_detection_rule_out_feed_view(request, pk):
    obj = DetectionRuleOutgoingFeed.objects.get(id=pk)
    obj.delete()
    return redirect("collaborate_detection_rule_out_feed_create_view")


class EntityOutgoingFeedCreateView(LoginRequiredMixin, CaseRequiredMixin, CreateView):
    model = EntityOutgoingFeed
    template_name = 'pages/collaborate/entity_out_feeds.html'
    success_url = reverse_lazy('collaborate_entity_out_feed_create_view')
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
        active_case = get_active_case(self.request)
        if form.is_valid() and active_case:
            feed = form.save(commit=False)
            if not hasattr(feed, 'owner'):
                feed.owner = self.request.user
                feed.case = active_case
            feed.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['feeds'] = EntityOutgoingFeed.get_user_entity_out_feeds(self.request.user,
                                                                    self.request.session.get('active_case'))
        ctx['is_editing'] = False
        return ctx


class EntityOutgoingFeedUpdateView(EntityOutgoingFeedCreateView, UpdateView):
    case_required_message_action = "update feed"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['feeds'] = EntityOutgoingFeed.get_user_entity_out_feeds(self.request.user,
                                                                    self.request.session.get('active_case'))
        ctx['is_editing'] = True
        return ctx


@login_required
def delete_entity_out_feed_view(request, pk):
    obj = EntityOutgoingFeed.objects.get(id=pk)
    obj.delete()
    return redirect("collaborate_entity_out_feed_create_view")


def outgoing_entities_feed_view(request, pk):
    try:
        feed = EntityOutgoingFeed.objects.get(id=pk)
    except EntityOutgoingFeed.DoesNotExist:
        return HttpResponse('', status=503, content_type='text/plain')

    is_authenticated = request.user.is_authenticated
    is_authenticated |= request.GET.get('secret', '') == feed.secret
    is_authenticated |= request.headers.get('X-Colander-Feed', '') == f'Secret {feed.secret}'
    if not is_authenticated:
        return HttpResponse('', status=503, content_type='text/plain')

    if 'info' in request.GET:
        return JsonResponse(OutgoingFeedSerializer(feed).data, json_dumps_params={})

    format = request.GET.get('format', 'json')

    cache_key = f'feed_{feed.id}_{format}_{feed.secret}'
    cached = cache.get(cache_key)
    if cached:
        if format == 'json':
            return JsonResponse(cached, json_dumps_params={})
        elif format == 'csv':
            return HttpResponse(cached, status=200, content_type='text/plain')

    entities = feed.get_entities()
    if format == 'json':
        exporter = JsonCaseExporter(feed.case, entities)
        export = exporter.export()
        cache.set(cache_key, export, 3600)
        return JsonResponse(export, json_dumps_params={})
    elif format == 'csv':
        exporter = CsvCaseExporter(feed.case, entities)
        export = exporter.export()
        cache.set(cache_key, export, 3600)
        return HttpResponse(export, status=200, content_type='text/plain')


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
    if cached:
        return HttpResponse(cached, status=200, content_type='text/plain')

    rules = feed.get_entities()
    export = '\n'.join([r.content for r in rules.all()])
    cache.set(cache_key, export, 3600)
    return HttpResponse(export, status=200, content_type='text/plain')
