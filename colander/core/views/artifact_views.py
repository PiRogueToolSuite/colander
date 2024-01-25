import pathlib

import magic
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.forms.widgets import Textarea, RadioSelect
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, UpdateView, DetailView
from nacl.encoding import Base64Encoder

from colander.core.forms import CommentForm
from colander.core.models import Artifact, ArtifactType, Device, UploadRequest
from colander.core.views.views import CaseContextMixin
from colander.core.signals import process_hash_and_signing

class ArtifactCreateView(LoginRequiredMixin, CaseContextMixin, CreateView):
    model = Artifact
    template_name = 'pages/collect/artifacts.html'
    #success_url = reverse_lazy('collect_artifact_create_view')
    contextual_success_url = 'collect_artifact_create_view'
    fields = [
        #'file',
        'type',
        'description',
        'extracted_from',
        'source_url',
        'attributes',
        'tlp',
        'pap',
    ]
    case_required_message_action = "create artifacts"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['artifacts'] = Artifact.get_user_artifacts(self.request.user, self.active_case)
        ctx['is_editing'] = False
        return ctx

    def clean(self):
        clean_data = super(ArtifactCreateView, self).clean()
        print('!!! Clean !!!')
        return clean_data

    def form_invalid(self, form):
        if 'upload_request_ref' in form.cleaned_data:
            upr = UploadRequest.objects.get(pk=form.cleaned_data['upload_request_ref'])
            form.fields['filename'] = forms.CharField(initial=upr.name, required=False, disabled=True)
            form.fields.pop( 'file' )
        return super().form_invalid(form)

    def form_valid(self, form):

        if form.is_valid() and self.active_case:
            artifact = form.save(commit=False)
            if not hasattr(artifact, 'owner'):
                artifact.owner = self.request.user
                artifact.case = self.active_case

            upr = UploadRequest.objects.get(pk=form.cleaned_data['upload_request_ref'])

            file_name = upr.name

            mime_type = magic.from_file(upr.path, mime=True)

            #TODO: To clean
            # delegate to an 'async'ish task
            # with open(upr.path, 'rb') as f:
            #   sha256, sha1, md5, size = hash_file(f)

            extension = pathlib.Path(file_name).suffix

            #TODO: To clean
            # delegate to an 'async'ish task
            # artifact.file = File(file=open(upr.path, 'rb'), name=file_name)
            # artifact.sha256 = sha256
            # artifact.sha1 = sha1
            # artifact.md5 = md5
            artifact.size_in_bytes = upr.size

            artifact.extension = extension
            artifact.mime_type = mime_type
            artifact.name = file_name
            artifact.original_name = file_name
            artifact.save()
            form.save_m2m()

            upr.target_artifact_id = str(artifact.id)
            upr.save()

            transaction.on_commit(lambda: process_hash_and_signing.send(sender=self.__class__, upload_request_id=str(upr.id)))

        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super(ArtifactCreateView, self).get_form(form_class)
        devices_qset = Device.get_user_devices(self.request.user, self.active_case)
        artifact_types = ArtifactType.objects.all()
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in artifact_types
        ]
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        form.fields['extracted_from'].queryset = devices_qset
        form.fields['upload_request_ref'] = forms.CharField(widget = forms.HiddenInput(), required = True)
        form.fields['file'] = forms.FileField(required=False)
        form.initial['tlp'] = self.active_case.tlp
        form.initial['pap'] = self.active_case.pap

        return form


class ArtifactUpdateView(LoginRequiredMixin, CaseContextMixin, UpdateView):
    model = Artifact
    template_name = 'pages/collect/artifacts.html'
    #success_url = reverse_lazy('collect_artifact_create_view')
    contextual_success_url = 'collect_artifact_create_view'
    fields = [
        'original_name',
        'type',
        'description',
        'extracted_from',
        'attributes',
        'source_url',
        'tlp',
        'pap',
    ]
    case_required_message_action = "edit artifact"

    def get_form(self, form_class=None):
        form = super(ArtifactUpdateView, self).get_form(form_class)
        devices_qset = Device.get_user_devices(self.request.user, self.active_case)
        artifact_types = ArtifactType.objects.all()
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in artifact_types
        ]
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['original_name'] = forms.CharField(disabled=True)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        form.fields['extracted_from'].queryset = devices_qset
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['artifacts'] = Artifact.get_user_artifacts(self.request.user, self.active_case)
        ctx['is_editing'] = True
        return ctx


class ArtifactDetailsView(LoginRequiredMixin, CaseContextMixin, DetailView):
    model = Artifact
    template_name = 'pages/collect/artifact_details.html'
    case_required_message_action = "view artifact details"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comment_form'] = CommentForm()
        return ctx

@login_required
def download_artifact(request, pk):
    content = Artifact.objects.get(id=pk)
    response = StreamingHttpResponse(content.file, content_type=content.mime_type)
    response['Content-Disposition'] = 'attachment; filename=' + content.name
    return response

@login_required
def view_artifact(request, pk):
    content = Artifact.objects.get(id=pk)
    response = StreamingHttpResponse(content.file, content_type=content.mime_type)
    response['Content-Disposition'] = 'inline; filename=' + content.name
    return response

@login_required
def download_artifact_signature(request, pk):
    content = Artifact.objects.get(id=pk)
    raw = Base64Encoder.decode(content.detached_signature)
    response = HttpResponse(raw, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename={content.name}.sig'
    return response

@login_required
def delete_artifact_view(request, pk):
    obj = Artifact.objects.get(id=pk)
    obj.delete()
    return redirect("collect_artifact_create_view", case_id=request.contextual_case.id)
