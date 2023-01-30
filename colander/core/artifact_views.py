import pathlib
from tempfile import NamedTemporaryFile

import magic
from django.contrib.auth.decorators import login_required
from django.forms.widgets import Textarea, RadioSelect
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, UpdateView, DetailView
from nacl.encoding import Base64Encoder

from colander.core.models import Artifact, ArtifactType
from colander.core.utils import hash_file
from colander.core.views import get_active_case


class ArtifactCreateView(CreateView):
    model = Artifact
    template_name = 'pages/collect/artifacts.html'
    success_url = reverse_lazy('collect_artifact_create_view')
    fields = [
        'file',
        'type',
        'description',
        'extracted_from',
        'source_url',
        'tlp',
        'pap',
    ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['artifacts'] = Artifact.get_user_artifacts(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = False
        return ctx

    def form_valid(self, form):
        active_case = get_active_case(self.request)
        if form.is_valid() and active_case:
            evidence = form.save(commit=False)
            evidence.owner = self.request.user
            file_name = str(self.request.FILES['file'])
            uploaded_file = self.request.FILES['file']
            with NamedTemporaryFile(suffix=file_name) as tmp:
                for chunk in uploaded_file.chunks():
                    tmp.write(chunk)
                tmp.seek(0)
                sha256, sha1, md5, size = hash_file(tmp)
                mime_type = magic.from_file(tmp.name, mime=True)
            extension = pathlib.Path(file_name).suffix
            evidence.sha256 = sha256
            evidence.sha1 = sha1
            evidence.md5 = md5
            evidence.size_in_bytes = size
            evidence.extension = extension
            evidence.mime_type = mime_type
            evidence.name = file_name
            evidence.original_name = file_name
            evidence.case = active_case
            evidence.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super(ArtifactCreateView, self).get_form(form_class)
        artifact_types = ArtifactType.objects.all()
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in artifact_types
        ]
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        return form


class ArtifactUpdateView(UpdateView):
    model = Artifact
    template_name = 'pages/collect/artifacts.html'
    success_url = reverse_lazy('collect_artifact_create_view')
    fields = [
        'type',
        'description',
        'extracted_from',
        'source_url',
        'tlp',
        'pap',
    ]

    def get_form(self, form_class=None):
        form = super(ArtifactUpdateView, self).get_form(form_class)
        artifact_types = ArtifactType.objects.all()
        choices = [
            (t.id, mark_safe(f'<i class="nf {t.nf_icon} text-primary"></i> {t.name}'))
            for t in artifact_types
        ]
        form.fields['type'].widget = RadioSelect(choices=choices)
        form.fields['description'].widget = Textarea(attrs={'rows': 2, 'cols': 20})
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['artifacts'] = Artifact.get_user_artifacts(self.request.user, self.request.session.get('active_case'))
        ctx['is_editing'] = True
        return ctx


class ArtifactDetailsView(DetailView):
    model = Artifact
    template_name = 'pages/collect/artifact_details.html'

@login_required
def download_artifact(request, pk):
    content = Artifact.objects.get(id=pk)
    response = HttpResponse(content.file, content_type=content.mime_type)
    response['Content-Disposition'] = 'attachment; filename=' + content.name
    return response

@login_required
def download_artifact_signature(request, pk):
    content = Artifact.objects.get(id=pk)
    raw = Base64Encoder.decode(content.detached_signature)
    response = HttpResponse(raw, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename={content.name}.sig'
    return response
