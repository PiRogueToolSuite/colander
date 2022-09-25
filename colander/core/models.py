import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ColanderTeam(models.Model):
    contributors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='teams',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING
    )

    @staticmethod
    def get_my_teams_as_contrib(user):
        return ColanderTeam.objects.filter(contributors=user)


def _get_upload_dir(instance, filename):
    owner_id = instance.owner.id
    return f'{owner_id}/files/{instance.id}'


class Evidence(models.Model):
    EMAIL = 'EMAIL'
    SAMPLE = 'SAMPLE'
    FORENSIC = 'FORENSIC'
    PCAP = 'PCAP'
    SOCKET_TRACE = 'SOCKET_TRACE'
    ENCRYPTION_TRACE = 'ENCRYPTION_TRACE'
    DOCUMENT = 'DOCUMENT'
    IMAGE = 'IMAGE'
    VIDEO = 'VIDEO'
    WEB_PAGE = 'WEB_PAGE'
    SM_POST = 'SM_POST'
    REPORT = 'REPORT'
    OTHER = 'OTHER'
    EVIDENCE_TYPE = [
        (EMAIL, _('Email file')),
        (SAMPLE, _('Sample')),
        (FORENSIC, _('Forensic dump')),
        (PCAP, _('PCAP file')),
        (SOCKET_TRACE, _('Socket activity trace')),
        (ENCRYPTION_TRACE, _('Cryptographic activity trace')),
        (DOCUMENT, _('Document')),
        (IMAGE, _('Image')),
        (VIDEO, _('Video')),
        (WEB_PAGE, _('Web page')),
        (SM_POST, _('Social media post')),
        (REPORT, _('Report')),
        (OTHER, _('Other type of file')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier of this file.'),
        editable=False
    )
    type = models.CharField(
        max_length=16,
        choices=EVIDENCE_TYPE,
        default=OTHER,
    )
    extension = models.CharField(max_length=64, blank=True, null=True)
    original_name = models.CharField(max_length=512, blank=True, null=True)
    stored_name = models.CharField(max_length=512, blank=True, null=True)
    storage_name = models.CharField(max_length=64, blank=True, null=True)
    storage_location = models.CharField(max_length=512, blank=True, null=True)
    mime_type = models.CharField(max_length=512, blank=True, null=True)
    detached_signature = models.TextField(blank=True, null=True)
    md5 = models.CharField(max_length=65, blank=True, null=True)
    sha1 = models.CharField(max_length=65, blank=True, null=True)
    sha256 = models.CharField(max_length=65, blank=True, null=True)
    size_in_bytes = models.IntegerField(default=0)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_('Who owns this file.'),
        related_name='my_files',
        editable=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Creation date of your experiment.'),
        editable=False
    )
    updated_at = models.DateTimeField(
        help_text=_('Latest modification of your experiment.'),
        auto_now=True
    )
    file = models.FileField(
        upload_to=_get_upload_dir,
        max_length=512,
        null=True,
        blank=True
    )


class NetworkDump(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier of your experiment.'),
        editable=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Creation date of your experiment.'),
        editable=False
    )
    updated_at = models.DateTimeField(
        help_text=_('Latest modification of your experiment.'),
        auto_now=True
    )
    pcap = models.ForeignKey(
        Evidence,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='pcap_file'
    )
    socket_trace = models.ForeignKey(
        Evidence,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='socket_trace_file'
    )
    sslkeylog = models.ForeignKey(
        Evidence,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    extra_files = models.ManyToManyField(
        Evidence,
        blank=True,
        related_name='extra_files_att'
    )
    traffic_index = models.UUIDField(
        default=uuid.uuid4,
        help_text=_('Elasticsearch index storing the network traffic analysis.'),
        editable=False
    )


class Experiment(models.Model):
    class Meta:
        ordering = ['-updated_at']

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier of your experiment.'),
        editable=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Creation date of your experiment.'),
        editable=False
    )
    updated_at = models.DateTimeField(
        help_text=_('Latest modification of your experiment.'),
        auto_now=True
    )
    name = models.CharField(
        max_length=512,
        verbose_name=_('name'),
        help_text=_('Give a meaningful name to your experiment.'),
        default=''
    )
    description = models.TextField(
        help_text=_('Add more details about the project here.'),
        default=_('No description')
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_('Who owns the current experiment.'),
        related_name='my_experiments',
        editable=False
    )
    team = models.ForeignKey(
        ColanderTeam,
        on_delete=models.CASCADE,
        null=True,
        related_name='experiments'
    )
