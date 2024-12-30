import pathlib

import magic
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.forms import ModelForm
from django.shortcuts import render
from django.views.generic import CreateView

from colander.core.models import DroppedFile, Artifact, Case
from colander.core.signals import process_dropped_files_conversion


class ConversionToArtifactForm(ModelForm):
    dropped_files = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=None,
    )
    delete_action = forms.CharField(
        widget=forms.HiddenInput,
        required=False,
    )

    class Meta:
        model = Artifact
        fields = [
            'case',
            'description',
            'extracted_from',
            'source_url',
            'tlp',
            'pap',
            'type',
            'name',
            'description',
            'attributes',
            'dropped_files',
        ]

    @staticmethod
    def get_for_user(user, data=None, for_deletion=False):
        form = ConversionToArtifactForm(data)
        form.fields['case'].queryset = Case.get_user_cases(user)
        form.fields['dropped_files'].queryset = DroppedFile.objects.filter(owner=user)
        form.fields['description'].widget.attrs['rows'] = 2
        if for_deletion:
            form.fields['case'].required = False
            form.fields['type'].required = False
        return form


def __process_drops_deletion(request):
    ctaf = ConversionToArtifactForm.get_for_user(request.user, request.POST, True)
    if ctaf.is_valid():
        deleted_dropped_files = ctaf.cleaned_data['dropped_files']
        is_batch = len(deleted_dropped_files) > 1
        if ctaf.cleaned_data['delete_action'] == 'delete':
            for cdf in deleted_dropped_files:
                cdf.delete()
            messages.add_message(
                request,
                messages.INFO,
                f"Deleted"
                f" {len(deleted_dropped_files)}"
                f" drop{'s' if len(deleted_dropped_files) > 1 else ''}")
    else:
        messages.add_message(
            request,
            messages.ERROR,
            f"Can't perform deletion. Please contact administrator.")


def __process_drops_conversion(request):
    ctaf = ConversionToArtifactForm.get_for_user(request.user, request.POST)
    if ctaf.is_valid():
        converted_dropped_files = ctaf.cleaned_data['dropped_files']
        is_batch = len(converted_dropped_files) > 1

        dropped_files_ids_to_process_later = []

        for cdf in converted_dropped_files:

            new_artifact = Artifact(owner=request.user)
            new_artifact.case = ctaf.cleaned_data['case']
            new_artifact.type = ctaf.cleaned_data['type']
            new_artifact.description = ctaf.cleaned_data['description']
            new_artifact.extracted_form = ctaf.cleaned_data['extracted_from']
            new_artifact.tlp = ctaf.cleaned_data['tlp']
            new_artifact.pap = ctaf.cleaned_data['pap']
            new_artifact.attributes = {}
            # Filters originals attributes without 'source_url'
            for original_attr in cdf.attributes:
                print(f'original_attr:{original_attr}')
                if original_attr == 'source_url':
                    continue
                new_artifact.attributes[original_attr] = cdf.attributes[original_attr]
            # Filters new 'non-empty' attributes
            for new_attr in ctaf.cleaned_data['attributes']:
                print(f'new_attr:{new_attr}')
                if not ctaf.cleaned_data['attributes'][new_attr]:
                    continue
                new_artifact.attributes[new_attr] = ctaf.cleaned_data['attributes'][new_attr]
            new_artifact.extension = pathlib.Path(cdf.filename).suffix
            new_artifact.size_in_bytes = cdf.file.size
            new_artifact.mime_type = cdf.mime_type

            if is_batch:
                new_artifact.name = cdf.filename
                if 'source_url' in cdf.attributes:
                    new_artifact.source_url = cdf.attributes['source_url']
                new_artifact.original_name = new_artifact.name
            else:
                new_artifact.name = ctaf.cleaned_data['name']
                new_artifact.source_url = ctaf.cleaned_data['source_url']
                new_artifact.original_name = cdf.filename

            new_artifact.save()
            cdf.target_artifact_id = str(new_artifact.id)
            cdf.save()
            dropped_files_ids_to_process_later.append(str(cdf.id))

        messages.add_message(
            request,
            messages.INFO,
            f"Convertion started for"
            f" {len(dropped_files_ids_to_process_later)}"
            f" drop{'s' if len(dropped_files_ids_to_process_later) > 1 else ''}")

        transaction.on_commit(
            lambda: process_dropped_files_conversion.send(
                sender=request.__class__,
                dropped_file_ids=dropped_files_ids_to_process_later))
    else:
        messages.add_message(
            request,
            messages.ERROR,
            f"Can't perform conversion. Please contact administrator. {ctaf.errors}")


@login_required
def triage_view(request):
    if request.method == 'POST':
        if 'delete_action' in request.POST and request.POST['delete_action'] == 'delete':
            __process_drops_deletion(request)
        else:
            __process_drops_conversion(request)

    ctx = dict()
    ctx['drops'] = DroppedFile.all_drops_by_user(request.user).order_by('dropped_at')
    ctx['conversion_form'] = ConversionToArtifactForm.get_for_user(request.user)
    return render(request, 'pages/drops_triage/base.html', context=ctx)
