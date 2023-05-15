from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.widgets import Textarea, RadioSelect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, UpdateView, DetailView

from colander.core.forms import CommentForm
from colander.core.models import DetectionRule, DetectionRuleType
from colander.core.views.views import get_active_case, CaseRequiredMixin


class DetectionRuleCreateView(LoginRequiredMixin, CaseRequiredMixin, CreateView):
    model = DetectionRule
    template_name = 'pages/collect/detection_rules.html'
    success_url = reverse_lazy('collect_detection_rule_create_view')
    fields = [
        'type',
        'name',
        'description',
        'source_url',
        'tlp',
        'pap',
        'content'
    ]

    def get_form(self, form_class=None):
        form = super(DetectionRuleCreateView, self).get_form(form_class)
        rule_types = DetectionRuleType.objects.all()
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in rule_types
        ]
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        return form

    def form_valid(self, form):
        active_case = get_active_case(self.request)
        if form.is_valid() and active_case:
            rule = form.save(commit=False)
            if not hasattr(rule, 'owner'):
                rule.owner = self.request.user
                rule.case = active_case
            rule.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['detection_rules'] = DetectionRule.get_user_detection_rules(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = False
        return ctx


class DetectionRuleUpdateView(DetectionRuleCreateView, UpdateView):
    context_object_name = 'detection_rule'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['detection_rules'] = DetectionRule.get_user_detection_rules(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = True
        return ctx


class DetectionRuleDetailsView(LoginRequiredMixin, CaseRequiredMixin, DetailView):
    model = DetectionRule
    template_name = 'pages/collect/detection_rule_details.html'
    context_object_name = 'detection_rule'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comment_form'] = CommentForm()
        return ctx


@login_required
def delete_detection_rule_view(request, pk):
    obj = DetectionRule.objects.get(id=pk)
    obj.delete()
    return redirect("collect_detection_rule_create_view")
