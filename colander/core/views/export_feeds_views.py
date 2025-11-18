from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.forms.widgets import RadioSelect, Textarea
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.views.generic import CreateView, UpdateView

from colander.core.feed.exporters.csv import CsvFeedExporter
from colander.core.feed.exporters.dot import DotFeedExporter
from colander.core.feed.exporters.json import JsonFeedExporter
from colander.core.feed.exporters.mermaid import MermaidFeedExporter
from colander.core.feed.exporters.misp import MISPFeedExporter
from colander.core.feed.exporters.stix2 import Stix2FeedExporter
from colander.core.feed.serializers import OutgoingFeedInfoSerializer
from colander.core.models import DetectionRuleExportFeed, DetectionRuleType, EntityExportFeed, FeedTemplate, \
    CustomExportFeed
from colander.core.views.views import CaseContextMixin


class DetectionRuleExportFeedCreateView(LoginRequiredMixin, CaseContextMixin, CreateView):
    model = DetectionRuleExportFeed
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
        form = super(DetectionRuleExportFeedCreateView, self).get_form(form_class)
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
        ctx['feeds'] = DetectionRuleExportFeed.get_user_detection_rule_out_feeds(self.request.user, self.active_case)
        ctx['is_editing'] = False
        return ctx


class DetectionRuleExportFeedUpdateView(DetectionRuleExportFeedCreateView, UpdateView):
    case_required_message_action = "update feed"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['feeds'] = DetectionRuleExportFeed.get_user_detection_rule_out_feeds(self.request.user, self.active_case)
        ctx['is_editing'] = True
        return ctx


@login_required
def delete_detection_rule_export_feed_view(request, pk):
    obj = DetectionRuleExportFeed.objects.get(id=pk)
    obj.delete()
    return redirect("feeds_detection_rule_out_feed_create_view", case_id=request.contextual_case.id)


class CustomExportFeedCreateView(LoginRequiredMixin, CaseContextMixin, CreateView):
    model = CustomExportFeed
    template_name = 'pages/feeds/custom_out_feeds.html'
    contextual_success_url = 'feeds_custom_out_feed_create_view'
    fields = [
        'name',
        'description',
        'template',
        'secret',
    ]
    case_required_message_action = "create detection rule outgoing feed"

    def get_form(self, form_class=None):
        form = super(CustomExportFeedCreateView, self).get_form(form_class)
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
        ctx['feeds'] = CustomExportFeed.get_user_custom_out_feeds(self.request.user, self.active_case)
        ctx['is_editing'] = False
        return ctx


class CustomExportFeedUpdateView(CustomExportFeedCreateView, UpdateView):
    case_required_message_action = "update feed"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['feeds'] = CustomExportFeed.get_user_custom_out_feeds(self.request.user, self.active_case)
        ctx['is_editing'] = True
        return ctx


@login_required
def delete_custom_export_feed_view(request, pk):
    obj = CustomExportFeed.objects.get(id=pk)
    obj.delete()
    return redirect("feeds_custom_out_feed_create_view", case_id=request.contextual_case.id)


class FeedTemplateCreateView(LoginRequiredMixin, CaseContextMixin, CreateView):
    model = FeedTemplate
    template_name = 'pages/feeds/template.html'
    contextual_success_url = 'feeds_template_create_view'
    fields = [
        'name',
        'description',
        'visibility',
        'teams',
        'content',
    ]
    case_required_message_action = "create templates"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['templates'] = self.request.user.available_templates
        ctx['active_case'] = self.active_case
        ctx['is_editing'] = False
        return ctx

    def form_valid(self, form):
        if form.is_valid() and self.active_case:
            template = form.save(commit=False)
            if not hasattr(template, 'owner'):
                template.owner = self.request.user
                template.case = self.active_case
            template.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super(FeedTemplateCreateView, self).get_form(form_class)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        return form


class FeedTemplateUpdateView(FeedTemplateCreateView, UpdateView):
    case_required_message_action = "update template"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['templates'] = self.request.user.available_templates
        ctx['active_case'] = self.active_case
        ctx['is_editing'] = True
        return ctx


@login_required
def feed_template_live_editor_view(request, pk):
    obj = FeedTemplate.objects.get(id=pk)
    if obj not in request.user.available_templates:
        return redirect("feeds_template_create_view", case_id=request.contextual_case.id)
    else:
        return render(request, 'feed/template_live_editor.html', {
            "case_id": request.contextual_case.id,
            "template_id": str(obj.id),
            "read_only": bool(request.user != obj.owner),
        })


@login_required
def delete_feed_template_view(request, pk):
    obj = FeedTemplate.objects.get(id=pk)
    if obj in request.user.available_templates:
        obj.delete()
    return redirect("feeds_template_create_view", case_id=request.contextual_case.id)


class EntityExportFeedCreateView(LoginRequiredMixin, CaseContextMixin, CreateView):
    model = EntityExportFeed
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
        form = super(EntityExportFeedCreateView, self).get_form(form_class)
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
        ctx['feeds'] = EntityExportFeed.get_user_entity_out_feeds(self.request.user, self.active_case)
        ctx['is_editing'] = False
        return ctx


class EntityExportFeedUpdateView(EntityExportFeedCreateView, UpdateView):
    case_required_message_action = "update feed"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['feeds'] = EntityExportFeed.get_user_entity_out_feeds(self.request.user, self.active_case)
        ctx['is_editing'] = True
        return ctx


@login_required
def delete_entity_export_feed_view(request, pk):
    obj = EntityExportFeed.objects.get(id=pk)
    obj.delete()
    return redirect("feeds_entity_out_feed_create_view", case_id=request.contextual_case.id)


def entity_export_feed_view(request, pk):
    try:
        feed = EntityExportFeed.objects.get(id=pk)
    except EntityExportFeed.DoesNotExist:
        return HttpResponse('', status=404, content_type='text/plain')

    is_authenticated = request.user.is_authenticated
    is_authenticated |= request.GET.get('secret', '') == feed.secret
    is_authenticated |= request.headers.get('X-Colander-Feed', '') == f'Secret {feed.secret}'
    if not is_authenticated:
        return HttpResponse('', status=503, content_type='text/plain')

    if 'info' in request.GET:
        return JsonResponse(OutgoingFeedInfoSerializer(feed).data, json_dumps_params={})

    requested_format = request.GET.get('format', 'json')
    if requested_format not in ['json', 'stix2', 'misp', 'csv', 'mermaid', 'dot']:
        requested_format = 'json'

    cache_key = f'feed_{feed.id}_{requested_format}_{feed.secret}'

    cached = cache.get(cache_key)
    if cached:
        if requested_format in ['json', 'stix2', 'misp']:
            return JsonResponse(cached, json_dumps_params={}, headers={'X-Colander-Feed-Cache': 'hit'})
        elif requested_format in ['csv', 'mermaid', 'dot']:
            return HttpResponse(cached, status=200, content_type='text/plain', headers={'X-Colander-Feed-Cache': 'hit'})

    if requested_format == 'json':
        exporter = JsonFeedExporter(feed)
        export = exporter.export()
        cache.set(cache_key, export, 3600)
        return JsonResponse(export, json_dumps_params={}, headers={'X-Colander-Feed-Cache': 'miss'})
    elif requested_format == 'stix2':
        exporter = Stix2FeedExporter(feed)
        export = exporter.export()
        cache.set(cache_key, export, 3600)
        return JsonResponse(export, json_dumps_params={}, headers={'X-Colander-Feed-Cache': 'miss'})
    elif requested_format == 'misp':
        if not feed.misp_org_id or not feed.misp_org_name:
            return HttpResponse('Unavailable', status=404, content_type='text/plain')
        else:
            exporter = MISPFeedExporter(feed)
            export = exporter.export()
            cache.set(cache_key, export, 3600)
            return JsonResponse(export, json_dumps_params={}, headers={'X-Colander-Feed-Cache': 'miss'})
    elif requested_format == 'csv':
        exporter = CsvFeedExporter(feed)
        export = exporter.export()
        cache.set(cache_key, export, 3600)
        return HttpResponse(export, status=200, content_type='text/plain', headers={'X-Colander-Feed-Cache': 'miss'})
    elif requested_format == 'mermaid':
        exporter = MermaidFeedExporter(feed)
        export = exporter.export()
        cache.set(cache_key, export, 3600)
        return HttpResponse(export, status=200, content_type='text/plain', headers={'X-Colander-Feed-Cache': 'miss'})
    elif requested_format == 'dot':
        exporter = DotFeedExporter(feed)
        export = exporter.export()
        cache.set(cache_key, export, 3600)
        return HttpResponse(export, status=200, content_type='text/plain', headers={'X-Colander-Feed-Cache': 'miss'})
    return HttpResponse('', status=404, content_type='text/plain')


def custom_export_feed_view(request, pk):
    try:
        feed = CustomExportFeed.objects.get(id=pk)
    except CustomExportFeed.DoesNotExist:
        return HttpResponse('', status=503, content_type='text/plain')

    is_authenticated = request.user.is_authenticated
    is_authenticated |= request.GET.get('secret', '') == feed.secret
    is_authenticated |= request.headers.get('X-Colander-Feed', '') == f'Secret {feed.secret}'
    if not is_authenticated:
        return HttpResponse('', status=503, content_type='text/plain')

    if 'info' in request.GET:
        return JsonResponse(OutgoingFeedInfoSerializer(feed).data, json_dumps_params={})

    cache_key = f'feed_{feed.id}_{feed.secret}'
    cached = cache.get(cache_key)
    if cached:
        return HttpResponse(cached, status=200, content_type='text/plain', headers={'X-Colander-Feed-Cache': 'hit'})
    content = feed.get_content()
    cache.set(cache_key, content, 3600)
    return HttpResponse(content, status=200, content_type='text/plain', headers={'X-Colander-Feed-Cache': 'miss'})


def detection_rule_export_feed_view(request, pk):
    try:
        feed = DetectionRuleExportFeed.objects.get(id=pk)
    except DetectionRuleExportFeed.DoesNotExist:
        return HttpResponse('', status=503, content_type='text/plain')

    is_authenticated = request.user.is_authenticated
    is_authenticated |= request.GET.get('secret', '') == feed.secret
    is_authenticated |= request.headers.get('X-Colander-Feed', '') == f'Secret {feed.secret}'
    if not is_authenticated:
        return HttpResponse('', status=503, content_type='text/plain')

    if 'info' in request.GET:
        return JsonResponse(OutgoingFeedInfoSerializer(feed).data, json_dumps_params={})

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
