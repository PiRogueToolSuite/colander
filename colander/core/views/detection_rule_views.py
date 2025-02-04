from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.widgets import RadioSelect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, DetailView, UpdateView

from colander.core.forms import CommentForm, DetectionRuleForm
from colander.core.models import DetectionRule, DetectionRuleType
from colander.core.views.views import CaseContextMixin


class DetectionRuleCreateView(LoginRequiredMixin, CaseContextMixin, CreateView):
    form_class = DetectionRuleForm
    template_name = 'pages/collect/detection_rules.html'
    success_url = reverse_lazy('collect_detection_rule_create_view')
    case_required_message_action = 'create detection rules'
    contextual_success_url = 'collect_detection_rule_create_view'

    def get_form(self, form_class=None, edit=False):
        form = super(DetectionRuleCreateView, self).get_form(form_class)
        rule_types = DetectionRuleType.objects.all()
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in rule_types
        ]
        form.fields['content'].widget.attrs.update({'class': 'colander-text-editor'})
        form.fields['type'].widget = RadioSelect(choices=choices)

        if not edit:
            form.initial['tlp'] = self.active_case.tlp
            form.initial['pap'] = self.active_case.pap

        return form


    def form_valid(self, form):
        #active_case = get_active_case(self.request)
        if form.is_valid() and self.active_case:
            rule = form.save(commit=False)
            if not hasattr(rule, 'owner'):
                rule.owner = self.request.user
                rule.case = self.active_case
            rule.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['entity_types'] = {str(t.id): {'type': t.short_name, 'attributes': t.default_attributes} for t in DetectionRuleType.objects.all()}
        ctx['detection_rules'] = DetectionRule.get_user_detection_rules(self.request.user, self.active_case)
        ctx['is_editing'] = False
        return ctx


class DetectionRuleUpdateView(DetectionRuleCreateView, UpdateView):
    model = DetectionRule
    context_object_name = 'detection_rule'
    case_required_message_action = "update detection rule"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['detection_rules'] = DetectionRule.get_user_detection_rules(self.request.user, self.active_case)
        ctx['is_editing'] = True
        return ctx

    def get_form(self, form_class=None):
        return super().get_form(self.form_class, True)


class DetectionRuleDetailsView(LoginRequiredMixin, CaseContextMixin, DetailView):
    model = DetectionRule
    template_name = 'pages/collect/detection_rule_details.html'
    context_object_name = 'detection_rule'
    case_required_message_action = "view detection rule details"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comment_form'] = CommentForm()
        return ctx


@login_required
def delete_detection_rule_view(request, pk):
    obj = DetectionRule.objects.get(id=pk)
    obj.delete()
    return redirect("collect_detection_rule_create_view", case_id=request.contextual_case.id)
