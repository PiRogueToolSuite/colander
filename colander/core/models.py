import uuid

from django.conf import settings
from django.contrib.postgres.fields import HStoreField
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


def _get_evidence_upload_dir(instance, filename):
    # owner_id = instance.owner.id
    case_id = instance.case.id
    return f'cases/{case_id}/evidences/{instance.id}'


class CommonModelType(models.Model):
    class Meta:
        abstract = True
        ordering = ['name']

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    short_name = models.CharField(
        max_length=32,
        editable=False
    )
    name = models.CharField(
        max_length=512,
        verbose_name=_('name'),
        help_text=_('Give a meaningful name to this type of artifact.'),
        default=''
    )
    description = models.TextField(
        help_text=_('Add more details about it.'),
        blank=True,
        null=True
    )
    svg_icon = models.TextField(
        blank=True,
        null=True
    )
    nf_icon = models.CharField(
        max_length=256,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name


class ArtifactType(CommonModelType):
    pass


class ObservableType(CommonModelType):
    pass


class ThreatType(CommonModelType):
    pass


class ActorType(CommonModelType):
    pass


class DeviceType(CommonModelType):
    pass


class EventType(CommonModelType):
    pass


class DetectionRuleType(CommonModelType):
    pass


class CommonModel(models.Model):
    RED = 'RED'
    AMBER = 'AMBER'
    GREEN = 'GREEN'
    WHITE = 'WHITE'
    TLP_PAP_CHOICES = [
        (RED, 'RED'),
        (AMBER, 'AMBER'),
        (GREEN, 'GREEN'),
        (WHITE, 'WHITE'),
    ]

    class Meta:
        abstract: True

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier.'),
        editable=False
    )
    description = models.TextField(
        help_text=_('Add more details about this object.'),
        null=True,
        blank=True
    )
    source_url = models.URLField(
        help_text=_('Specify the source of this object.'),
        verbose_name='Source URL',
        null=True,
        blank=True
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_('Who owns this object.'),
        related_name="%(app_label)s_%(class)s_related",
        related_query_name="%(app_label)s_%(class)ss",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Creation date of this object.'),
        editable=False
    )
    updated_at = models.DateTimeField(
        help_text=_('Latest modification of this object.'),
        auto_now=True
    )
    tlp = models.CharField(
        max_length=6,
        choices=TLP_PAP_CHOICES,
        help_text=_('Traffic Light Protocol, designed to indicate the sharing boundaries to be applied.'),
        verbose_name='TLP',
        default=WHITE
    )
    pap = models.CharField(
        max_length=6,
        choices=TLP_PAP_CHOICES,
        help_text=_('Permissible Actions Protocol, designed to indicate how the received information can be used.'),
        verbose_name='PAP',
        default=WHITE
    )


class Comment(models.Model):
    class Meta:
        ordering = ['-updated_at']

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier of the case.'),
        editable=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Creation date of the case.'),
        editable=False
    )
    updated_at = models.DateTimeField(
        help_text=_('Latest modification of the case.'),
        auto_now=True
    )
    content = models.TextField(
        help_text=_('Add more details about the case here.'),
        default=_('No description')
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_('Who owns the current case.'),
        related_name='comments',
        editable=False
    )
    commented_object = models.ForeignKey(
        CommonModel,
        on_delete=models.CASCADE,
        related_name='comments',
    )


class Case(models.Model):
    class Meta:
        ordering = ['-updated_at']

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier of the case.'),
        editable=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Creation date of the case.'),
        editable=False
    )
    updated_at = models.DateTimeField(
        help_text=_('Latest modification of the case.'),
        auto_now=True
    )
    name = models.CharField(
        max_length=512,
        verbose_name=_('name'),
        help_text=_('Give a meaningful name to the case.'),
        default=''
    )
    description = models.TextField(
        help_text=_('Add more details about the case here.'),
        default=_('No description')
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_('Who owns the current case.'),
        related_name='cases',
        editable=True
    )
    team = models.ForeignKey(
        ColanderTeam,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='cases'
    )
    parent_case = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='sub_cases'
    )

    def __str__(self):
        return self.name

    @staticmethod
    def get_user_cases(user):
        return Case.objects.all()


class CaseRelated(models.Model):
    class Meta:
        abstract = True

    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_related",
        related_query_name="%(app_label)s_%(class)ss",
    )


class Actor(CommonModel):
    type = models.ForeignKey(
        ActorType,
        on_delete=models.CASCADE,
        help_text=_('Type of this actor.')
    )
    name = models.CharField(
        max_length=512,
    )

    def __str__(self):
        return self.name


class Artifact(CommonModel, CaseRelated):
    type = models.ForeignKey(
        ArtifactType,
        on_delete=models.CASCADE,
        help_text=_('Type of this artifact.')
    )
    name = models.CharField(max_length=512, blank=True, null=True)
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
    size_in_bytes = models.BigIntegerField(default=0)
    file = models.FileField(
        upload_to=_get_evidence_upload_dir,
        max_length=512,
    )
    analysis_index = models.UUIDField(
        default=uuid.uuid4,
        help_text=_('Elasticsearch index storing the analysis.'),
        editable=False
    )
    attributes = HStoreField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f'{self.original_name} - {self.type}'

    @staticmethod
    def get_user_artifacts(user):
        return Artifact.objects.all()


class Threat(CommonModel):
    class Meta:
        ordering = ['-updated_at']

    type = models.ForeignKey(
        ThreatType,
        on_delete=models.CASCADE,
        help_text=_('Type of this threat.')
    )
    name = models.CharField(
        max_length=1024,
    )
    documentation = models.TextField(
        help_text=_('Add documentation about this threat.'),
        default=_('No documentation')
    )

    def __str__(self):
        return f'{self.name} - {self.type}'

    @staticmethod
    def get_user_threats(user):
        return Threat.objects.all()


class Observable(CommonModel, CaseRelated):
    class Meta:
        ordering = ['-updated_at']

    type = models.ForeignKey(
        ObservableType,
        on_delete=models.CASCADE,
        help_text=_('Type of this observable.')
    )
    value = models.CharField(
        max_length=512,
    )
    extracted_from = models.ForeignKey(
        Artifact,
        on_delete=models.CASCADE,
        related_name='observables',
        null=True,
        blank=True,
    )
    associated_threat = models.ForeignKey(
        Threat,
        on_delete=models.CASCADE,
        related_name='observables',
        null=True,
        blank=True,
    )
    analysis_index = models.UUIDField(
        default=uuid.uuid4,
        help_text=_('Elasticsearch index storing the analysis.'),
        editable=False
    )
    operated_by = models.ForeignKey(
        Actor,
        on_delete=models.CASCADE,
        related_name='observables',
        null=True,
        blank=True,
    )
    attributes = HStoreField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f'{self.type} - {self.value}'

    @property
    def event_count(self):
        return self.events.count()

    @staticmethod
    def get_user_observables(user):
        return Observable.objects.all()


class ObservableRelation(CommonModel, CaseRelated):
    class Meta:
        ordering = ['-updated_at']

    name = models.TextField(
        help_text=_('Name of this relation between two observables.'),
    )
    observable_from = models.ForeignKey(
        Observable,
        on_delete=models.CASCADE,
        related_name='relation_origins',
        null=True,
        blank=True,
    )
    observable_to = models.ForeignKey(
        Observable,
        on_delete=models.CASCADE,
        related_name='relation_targets',
        null=True,
        blank=True,
    )

    @staticmethod
    def get_user_relations(user):
        return ObservableRelation.objects.all()


class Device(CommonModel, CaseRelated):
    type = models.ForeignKey(
        DeviceType,
        on_delete=models.CASCADE,
        help_text=_('Type of this device.')
    )
    name = models.CharField(
        max_length=512,
    )
    operated_by = models.ForeignKey(
        Actor,
        on_delete=models.CASCADE,
        related_name='devices',
        null=True,
        blank=True,
    )
    attributes = HStoreField(
        blank=True,
        null=True
    )


class DetectionRule(CommonModel):
    type = models.ForeignKey(
        DetectionRuleType,
        on_delete=models.CASCADE,
        help_text=_('Type of this detection rule.')
    )
    detected_observables = models.ManyToManyField(
        Observable,
    )
    detection_index = models.UUIDField(
        default=uuid.uuid4,
        help_text=_('Elasticsearch index storing the detections.'),
        editable=False
    )


class Event(CommonModel, CaseRelated):
    type = models.ForeignKey(
        EventType,
        on_delete=models.CASCADE,
        help_text=_('Type of this event.')
    )
    first_seen = models.DateTimeField(
        help_text=_('First time the event has occurred.')
    )
    last_seen = models.DateTimeField(
        help_text=_('First time the event has occurred.')
    )
    count = models.BigIntegerField(default=0)
    name = models.CharField(
        max_length=512,
    )
    extracted_from = models.ForeignKey(
        Artifact,
        on_delete=models.CASCADE,
        related_name='events',
        null=True,
        blank=True,
    )
    observed_on = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='events',
        null=True,
        blank=True,
    )
    detected_by = models.ForeignKey(
        DetectionRule,
        on_delete=models.CASCADE,
        related_name='events',
        null=True,
        blank=True,
    )
    involved_observables = models.ManyToManyField(
        Observable,
        related_name='events',
    )
    attributes = HStoreField(null=True, blank=True)


class PiRogueDump(CommonModel, CaseRelated):
    pcap = models.ForeignKey(
        Artifact,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='pirogue_dump_pcap_file'
    )
    socket_trace = models.ForeignKey(
        Artifact,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='pirogue_dump_socket_trace_file'
    )
    target_device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='pirogue_dump_device'
    )
    target_artifact = models.ForeignKey(
        Artifact,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='pirogue_dump_artifact'
    )
    sslkeylog = models.ForeignKey(
        Artifact,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='pirogue_dump_ssl_keys'
    )
    extra_files = models.ManyToManyField(
        Artifact,
        blank=True,
        related_name='extra_files_att'
    )
    traffic_index = models.UUIDField(
        default=uuid.uuid4,
        help_text=_('Elasticsearch index storing the network traffic.'),
        editable=False
    )
    analysis_index = models.UUIDField(
        default=uuid.uuid4,
        help_text=_('Elasticsearch index storing the analysis.'),
        editable=False
    )

    @staticmethod
    def get_user_pirogue_dumps(user):
        return PiRogueDump.objects.all()
