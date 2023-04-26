import base64
import random
import string
import uuid

import django
from django.db.models import Q
from cryptography.exceptions import InvalidSignature
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from elasticsearch_dsl import Document, Keyword, Date, Object, Text, Nested
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import utils

import os
from datetime import timedelta
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django_q.models import Schedule
from django_q.tasks import async_task, schedule

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


def _random_id(length=16):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))


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
    signing_key = models.TextField(
        editable=True,
        default=''
    )
    es_prefix = models.CharField(
        max_length=16,
        editable=True,
        default=_random_id  )
    verify_key = models.TextField(
        editable=True,
        default=''
    )
    documentation = models.TextField(
        help_text=_('Case documentation.'),
        blank=True,
        null=True,
        editable=True
    )

    def save(self, *args, **kwargs):
        self.generate_key_pair(save=False)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_case_details_view', kwargs={'pk': self.id})

    @property
    def value(self):
        return self.name

    def __str__(self):
        return self.name

    def generate_key_pair(self, save=True):
        if not self.signing_key:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096,
            )
            private_pem = private_key.private_bytes(
               encoding=serialization.Encoding.PEM,
               format=serialization.PrivateFormat.TraditionalOpenSSL,
               encryption_algorithm=serialization.NoEncryption()
            )
            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
               encoding=serialization.Encoding.PEM,
               format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            self.signing_key = private_pem.decode('utf-8')
            self.verify_key = public_pem.decode('utf-8')
            if save:
                self.save()

    def quick_search(self, value, type=None, exclude_types=['EntityRelation']):
        models = colander_models
        if type and type in models:
            models = {type: models.get(type)}
        field_name = ''
        results = []
        for name, model in models.items():
            if name in exclude_types:
                continue
            if hasattr(model, 'name'):
                field_name = 'name'
            elif hasattr(model, 'value'):
                field_name = 'value'
            try:
                if hasattr(model, 'case'):
                    objects = model.objects.filter(**{f'{field_name}__icontains': value, 'case': self})
                else:
                    objects = model.objects.filter(**{f'{field_name}__icontains': value})
                results.extend(objects.all())
            except Exception as e:
                print(model, e)
                pass
        return results

    def get_all_entities(self, exclude_types=[]):
        return self.quick_search('', exclude_types=exclude_types)

    def get_mermaid(self):
        nodes = []
        clicks = []
        links = []
        classes = []
        for name, model in colander_models.items():
            if model in color_scheme:
                classes.append(f'classDef {name} fill:{color_scheme.get(model)}')
        entities = self.get_all_entities(exclude_types=['Threat', 'Event', 'Case'])
        for entity in entities:
            if hasattr(entity, 'to_mermaid'):
                n, c, l = entity.to_mermaid
                nodes.extend(n)
                clicks.extend(c)
                links.extend(l)
        node_txt = '\n\t'.join(list(set(nodes)))
        click_txt = '\n\t'.join(list(set(clicks)))
        link_txt = '\n\t'.join(list(set(links)))
        class_txt = '\n\t'.join(list(set(classes)))
        text = f'flowchart LR\n\t{node_txt}\n\t{click_txt}\n\t{link_txt}\n\t{class_txt}'
        return text

    def get_mermaid_events(self):
        events = Event.objects.filter(case=self).order_by('type__short_name', 'first_seen')
        graph = 'gantt\n\tdateFormat  YYYY-MM-DD HH:mm'
        current_section = ''
        for event in events:
            first_seen = event.first_seen.strftime('%Y-%m-%d %H:%M')
            last_seen = event.last_seen.strftime('%Y-%m-%d %H:%M')
            if current_section != event.type.name:
                current_section = event.type.name
                graph += f'\n\tsection {current_section}'
            if event.first_seen == event.last_seen:
                graph += f'\n\t{event.name}: milestone, {event.id}, {first_seen}, 2min'
            else:
                graph += f'\n\t{event.name}: {event.id}, {first_seen}, {last_seen}'
        return graph


    @property
    def to_mermaid(self):
        return self.get_mermaid()

    @property
    def to_mermaid_events(self):
        return self.get_mermaid_events()

    @staticmethod
    def get_user_cases(user):
        return Case.objects.filter(owner=user)


class Entity(models.Model):
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
        ordering = ['-updated_at']

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
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
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

    def get_relations(self):
        relations = EntityRelation.objects.filter(Q(obj_from_id=self.id) | Q(obj_to_id=self.id)).all()
        return relations

    def get_in_relations(self):
        relations = EntityRelation.objects.filter(obj_to_id=self.id).all()
        return relations

    def get_out_relations(self):
        relations = EntityRelation.objects.filter(obj_from_id=self.id).all()
        return relations

    @property
    def relations(self):
        return self.get_relations()

    @property
    def in_relations(self):
        return self.get_in_relations()

    @property
    def out_relations(self):
        return self.get_out_relations()

    @property
    def sorted_comments(self):
        return self.comments.order_by('created_at')


class Comment(models.Model):
    class Meta:
        ordering = ['-updated_at']

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier of the comment.'),
        editable=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Creation date of the comment.'),
        editable=False
    )
    updated_at = models.DateTimeField(
        help_text=_('Latest modification of the comment.'),
        auto_now=True
    )
    content = models.TextField(
        help_text=_('Add more details about the comment.'),
        default=_('No description')
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_('Who redacted this comment.'),
        related_name='comments',
    )
    commented_object = models.ForeignKey(
        Entity,
        on_delete=models.CASCADE,
        related_name='comments',
    )


class Actor(Entity):
    class Meta:
        ordering = ['name']

    type = models.ForeignKey(
        ActorType,
        on_delete=models.CASCADE,
        help_text=_('Type of this actor.')
    )
    name = models.CharField(
        max_length=512,
    )

    @property
    def icon(self):
        c = self.__class__
        return icons.get(c, '')

    @property
    def color(self):
        c = self.__class__
        return color_scheme.get(c, '')

    @property
    def super_type(self):
        return self.__class__.__name__

    @property
    def value(self):
        return self.name

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_actor_details_view', kwargs={'pk': self.id})

    @property
    def to_mermaid(self):
        icon = ''
        if self.icon:
            icon = f'fa:{self.icon}'
        label = f'{self.name}<br><small><i>{self.type.name}</i></small>'
        nodes = [f'{self.id}("{icon} {label}")']
        clicks = [
            f'click {self.id} "{self.get_absolute_url()}"',
            f'class {self.id} Actor'
        ]
        links = []
        return nodes, clicks, links

    @property
    def absolute_url(self):
        return self.get_absolute_url()

    @staticmethod
    def get_if_exists(name):
        objects = Actor.objects.filter(name=name).all()
        return bool(objects), objects

    @staticmethod
    def get_user_actors(user, case):
        if case:
            return Actor.objects.filter(case=case)
        return Actor.objects.all()


class Device(Entity):
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
        on_delete=models.SET_NULL,
        related_name='devices',
        null=True,
        blank=True,
    )
    attributes = HStoreField(
        blank=True,
        null=True
    )

    @property
    def value(self):
        return self.name

    @property
    def icon(self):
        c = self.__class__
        return icons.get(c, '')

    @property
    def color(self):
        c = self.__class__
        return color_scheme.get(c, '')

    @property
    def super_type(self):
        return self.__class__.__name__

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_device_details_view', kwargs={'pk': self.id})

    @property
    def to_mermaid(self):
        icon = ''
        if self.icon:
            icon = f'fa:{self.icon}'
        links = []
        label = f'{self.name}<br><small><i>{self.type.name}</i></small>'
        nodes = [
            f'{self.id}("{icon} {label}")',
            ]
        clicks = [
            f'click {self.id} "{self.get_absolute_url()}"',
            f'class {self.id} Device'
        ]
        if self.operated_by:
            links.append(
                f'{self.operated_by_id}-- operates -->{self.id}'
            )
        return nodes, clicks, links

    @property
    def absolute_url(self):
        return self.get_absolute_url()

    @staticmethod
    def get_if_exists(name, case_id):
        objects = Device.objects.filter(name=name, case__id=case_id).all()
        return bool(objects), objects

    @staticmethod
    def get_user_devices(user, case=None):
        if case:
            return Device.objects.filter(case=case)
        return []


class Artifact(Entity):
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
        blank = True, null = True
    )
    analysis_index = models.UUIDField(
        default=uuid.uuid4,
        help_text=_('Elasticsearch index storing the analysis.'),
        editable=False
    )
    extracted_from = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,
        related_name='artifacts',
        null=True,
        blank=True,
    )
    attributes = HStoreField(
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):
        self.sign(save=False)
        super().save(*args, **kwargs)

    def sign(self, save=True, force=False):
        if not self.detached_signature and self.sha256 or force:
            private_key = serialization.load_pem_private_key(
                self.case.signing_key.encode('utf-8'),
                password=None,
            )
            chosen_hash = hashes.SHA256()
            sig = private_key.sign(
                bytes.fromhex(self.sha256),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                utils.Prehashed(chosen_hash)
            )
            self.detached_signature = base64.b64encode(sig).decode('utf-8')
            if save:
                self.save()

    @property
    def has_valid_signature(self):
        # TODO: FIX: In fact ... it's not applicable here
        if not self.has_been_processed:
            return False

        public_key = serialization.load_pem_public_key(
            self.case.verify_key.encode('utf-8'),
        )
        chosen_hash = hashes.SHA256()
        try:
            public_key.verify(
                base64.b64decode(self.detached_signature),
                bytes.fromhex(self.sha256),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                utils.Prehashed(chosen_hash)
            )
            return True
        except InvalidSignature:
            return False

    @property
    def has_been_processed(self):
        return self.sha256 and self.detached_signature

    @property
    def value(self):
        return self.name

    @property
    def can_be_displayed(self):
        return self.type.short_name in ['IMAGE', 'VIDEO']

    @property
    def icon(self):
        c = self.__class__
        return icons.get(c, '')

    @property
    def color(self):
        c = self.__class__
        return color_scheme.get(c, '')

    @property
    def super_type(self):
        return self.__class__.__name__

    def __str__(self):
        return f'{self.original_name} - {self.type} ({self.created_at})'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_artifact_details_view', kwargs={'pk': self.id})

    @property
    def to_mermaid(self):
        icon = ''
        if self.icon:
            icon = f'fa:{self.icon}'
        links = []
        label = f'{self.name}<br><small><i>{self.type.name}</i></small>'
        nodes = [
            f'{self.id}("{icon} {label}")',
            ]
        clicks = [
            f'click {self.id} "{self.get_absolute_url()}"',
            f'class {self.id} Artifact'
        ]
        if self.extracted_from:
            links.append(
                f'{self.id}-- extracted from -->{self.extracted_from_id}'
            )
        return nodes, clicks, links

    @property
    def absolute_url(self):
        return self.get_absolute_url()

    @staticmethod
    def get_user_artifacts(user, case=None):
        if case:
            return Artifact.objects.filter(case=case)
        return Artifact.objects.filter(owner=user)

@receiver(pre_delete, sender=Artifact, dispatch_uid='delete_artifact_file')
def delete_upload_request_stored_files(sender, instance: Artifact, using, **kwargs):
    instance.file.delete()

class Threat(Entity):
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

    @property
    def value(self):
        return self.name

    @property
    def icon(self):
        c = self.__class__
        return icons.get(c, '')

    @property
    def color(self):
        c = self.__class__
        return color_scheme.get(c, '')

    @property
    def super_type(self):
        return self.__class__.__name__

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_threat_details_view', kwargs={'pk': self.id})

    @property
    def to_mermaid(self):
        icon = ''
        if self.icon:
            icon = f'fa:{self.icon}'
        links = []
        nodes = [
            f'{self.id}("{icon} {self.name}")',
            ]
        clicks = [
            f'click {self.id} "{self.get_absolute_url()}"',
            f'class {self.id} Threat'
        ]
        return nodes, clicks, links

    @property
    def absolute_url(self):
        return self.get_absolute_url()

    @staticmethod
    def get_if_exists(name):
        objects = Threat.objects.filter(name=name).all()
        return bool(objects), objects

    def __str__(self):
        return f'{self.name} - {self.type}'

    @staticmethod
    def get_user_threats(user, case=None):
        if case:
            return Threat.objects.filter(case=case)
        return Threat.objects.all()


class Observable(Entity):
    type = models.ForeignKey(
        ObservableType,
        on_delete=models.CASCADE,
        help_text=_('Type of this observable.')
    )
    name = models.CharField(
        max_length=512,
        verbose_name='Value',
        help_text=_('Value of this observable')
    )
    classification = models.CharField(
        max_length=512,
        blank=True,
        null=True
    )
    raw_value = models.TextField(
        blank=True,
        null=True
    )
    extracted_from = models.ForeignKey(
        Artifact,
        on_delete=models.SET_NULL,
        related_name='observables',
        null=True,
        blank=True,
    )
    associated_threat = models.ForeignKey(
        Threat,
        on_delete=models.SET_NULL,
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
        on_delete=models.SET_NULL,
        related_name='observables',
        null=True,
        blank=True,
    )
    attributes = HStoreField(
        blank=True,
        null=True
    )

    es_prefix = models.CharField(
        max_length=16,
        editable=False,
        default=_random_id   )
    @property
    def icon(self):
        c = self.__class__
        return icons.get(c, '')

    @property
    def color(self):
        c = self.__class__
        return color_scheme.get(c, '')

    @property
    def value(self):
        return self.name

    @property
    def super_type(self):
        return self.__class__.__name__

    def __str__(self):
        return f'{self.value} ({self.type.name.lower()})'

    def get_es_index(self):
        return f'c.{self.case.es_prefix}.o.{self.type.short_name.lower()}'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_observable_details_view', kwargs={'pk': self.id})

    @property
    def to_mermaid(self):
        icon = ''
        if self.icon:
            icon = f'fa:{self.icon}'
        links = []

        label = f'<samp>{self.value}</samp><br><small><i>{self.type.name}</i></small>'
        if self.associated_threat:
            label += f'<br><small>fa:fa-bug {self.associated_threat.name}</small>'
        nodes = [
            f'{self.id}("{icon} {label}")',
            ]
        clicks = [
            f'click {self.id} "{self.get_absolute_url()}"',
            f'class {self.id} Observable'
        ]
        if self.extracted_from:
            links.append(
                f'{self.id}-- extracted from -->{self.extracted_from_id}'
            )
        if self.operated_by:
            links.append(
                f'{self.operated_by_id}-- operates -->{self.id}'
            )
        return nodes, clicks, links

    @property
    def absolute_url(self):
        return self.get_absolute_url()

    @property
    def event_count(self):
        return self.events.count()

    @property
    def sorted_events(self):
        return self.events.order_by('first_seen')

    @property
    def is_malicious(self):
        return bool(self.associated_threat)

    @staticmethod
    def get_if_exists(value, case_id):
        objects = Observable.objects.filter(value=value, case__id=case_id).all()
        return bool(objects), objects

    @staticmethod
    def get_user_observables(user, case=None):
        if case:
            return Observable.objects.filter(case=case)
        return Observable.objects.filter(owner=user)


class EntityRelation(models.Model):
    class Meta:
        unique_together = [['name', 'obj_from_id', 'obj_to_id']]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier.'),
        editable=False
    )
    name = models.CharField(
        max_length=512,
        help_text=_('Name of this relation between two entities.'),
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_('Who owns this object.'),
        related_name="%(app_label)s_%(class)s_related",
        related_query_name="%(app_label)s_%(class)ss",
    )
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
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
    attributes = HStoreField(
        blank=True,
        null=True
    )
    obj_from_id = models.UUIDField()
    obj_from_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='obj_from_types')
    obj_from = GenericForeignKey('obj_from_type', 'obj_from_id')
    obj_to_id = models.UUIDField()
    obj_to_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='obj_to_types')
    obj_to = GenericForeignKey('obj_to_type', 'obj_to_id')

    def __str__(self):
        return f'{self.obj_from} -{self.name}-> {self.obj_to}'

    @property
    def value(self):
        return self.name

    @property
    def icon(self):
        c = self.__class__
        return icons.get(c, '')

    @property
    def color(self):
        c = self.__class__
        return color_scheme.get(c, '')

    @property
    def super_type(self):
        return self.__class__.__name__

    @staticmethod
    def get_user_entity_relations(user, case=None):
        if case:
            return EntityRelation.objects.filter(case=case)
        return EntityRelation.objects.filter(owner=user)

    @property
    def to_mermaid(self):
        icon = ''
        if self.icon:
            icon = f'fa:{self.icon}'
        links = [
            f'{self.obj_from_id}-- {icon} {self.name} -->{self.obj_to_id}'
        ]
        nodes = []
        clicks = []
        return nodes, clicks, links

@receiver(pre_delete, sender=Entity, dispatch_uid="entity_relation_cascade")
def entity_relation_cascade(sender, instance, using, **kwargs):
    EntityRelation.objects.filter(
        #obj_from_type=ContentType.objects.get_for_model(instance),
        obj_from_id=str(instance.pk)
    ).delete()

    EntityRelation.objects.filter(
        #obj_to_type=ContentType.objects.get_for_model(instance),
        obj_to_id=str(instance.pk)
    ).delete()

class ObservableRelation(Entity):
    class Meta:
        ordering = ['-updated_at']

    name = models.CharField(
        max_length=512,
        help_text=_('Name of this relation between two observables.'),
    )
    observable_from = models.ForeignKey(
        Observable,
        on_delete=models.CASCADE,
        related_name='relation_origins'
    )
    observable_to = models.ForeignKey(
        Observable,
        on_delete=models.CASCADE,
        related_name='relation_targets'
    )

    @property
    def value(self):
        return self.name

    @property
    def icon(self):
        c = self.__class__
        return icons.get(c, '')

    @property
    def color(self):
        c = self.__class__
        return color_scheme.get(c, '')

    @property
    def super_type(self):
        return self.__class__.__name__

    def __str__(self):
        return f'{self.observable_from} -> {self.observable_to}'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_relation_details_view', kwargs={'pk': self.id})

    @property
    def to_mermaid(self):
        icon = ''
        if self.icon:
            icon = f'fa:{self.icon}'
        links = [
            f'{self.observable_from_id}-- {icon} {self.name} -->{self.observable_to_id}'
        ]
        nodes = []
        clicks = []
        return nodes, clicks, links

    @property
    def absolute_url(self):
        return self.get_absolute_url()

    @staticmethod
    def get_if_exists(name, case_id, from_id, to_id):
        objects = ObservableRelation.objects.filter(name=name, case__id=case_id, observable_from__id=from_id,
                                                    observable_to__id=to_id)
        return bool(objects), objects

    @staticmethod
    def get_user_relations(user, case=None):
        if case:
            return ObservableRelation.objects.filter(case=case)
        return ObservableRelation.objects.all()


class DetectionRule(Entity):
    name = models.CharField(
        max_length=512,
        help_text=_('Name of this detection rule.'),
    )
    type = models.ForeignKey(
        DetectionRuleType,
        on_delete=models.CASCADE,
        help_text=_('Type of this detection rule.')
    )
    content = models.TextField()
    targeted_observables = models.ManyToManyField(
        Observable,
        blank=True,
        null=True
    )
    detection_index = models.UUIDField(
        default=uuid.uuid4,
        help_text=_('Elasticsearch index storing the detections.'),
        editable=False
    )

    @property
    def icon(self):
        c = self.__class__
        return icons.get(c, '')

    @property
    def color(self):
        c = self.__class__
        return color_scheme.get(c, '')

    @property
    def value(self):
        return self.name

    @property
    def super_type(self):
        return self.__class__.__name__

    def __str__(self):
        return f'{self.value} ({self.type.name.lower()})'

    @staticmethod
    def get_user_detection_rules(user, case=None):
        if case:
            return DetectionRule.objects.filter(case=case)
        return DetectionRule.objects.filter(owner=user)


class Event(Entity):
    type = models.ForeignKey(
        EventType,
        on_delete=models.CASCADE,
        help_text=_('Type of this event.')
    )
    first_seen = models.DateTimeField(
        help_text=_('First time the event has occurred.'),
        default=django.utils.timezone.now
    )
    last_seen = models.DateTimeField(
        help_text=_('First time the event has occurred.'),
        default=django.utils.timezone.now
    )
    count = models.BigIntegerField(
        help_text=_('How many times this event has occurred.'),
        default=0
    )
    name = models.CharField(
        max_length=512,
    )
    extracted_from = models.ForeignKey(
        Artifact,
        help_text=_('Select the artifact from which this event was extracted.'),
        on_delete=models.SET_NULL,
        related_name='events',
        null=True,
        blank=True,
    )
    observed_on = models.ForeignKey(
        Device,
        help_text=_('Select the device on which this event was observed.'),
        on_delete=models.SET_NULL,
        related_name='events',
        null=True,
        blank=True,
    )
    detected_by = models.ForeignKey(
        DetectionRule,
        help_text=_('Select the rule which has detected this event.'),
        on_delete=models.SET_NULL,
        related_name='events',
        null=True,
        blank=True,
    )
    involved_observables = models.ManyToManyField(
        Observable,
        help_text=_('Select the observables involved with this event.'),
        related_name='events',
    )
    attributes = HStoreField(null=True, blank=True)

    @property
    def value(self):
        return self.name

    @property
    def icon(self):
        c = self.__class__
        return icons.get(c, '')

    @property
    def color(self):
        c = self.__class__
        return color_scheme.get(c, '')

    @property
    def super_type(self):
        return self.__class__.__name__

    def __str__(self):
        return f'{self.name} ({self.type.name})'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_event_details_view', kwargs={'pk': self.id})

    @property
    def to_mermaid(self):
        icon = ''
        if self.icon:
            icon = f'fa:{self.icon}'
        links = []
        label = f'{self.name}<br><small><i>{self.type.name}</i></small>'
        nodes = [
            f'{self.id}("{icon} {label}")',
            ]
        clicks = [
            f'click {self.id} "{self.get_absolute_url()}"',
            f'class {self.id} Event'
        ]
        if self.extracted_from:
            links.append(
                f'{self.id}-- extracted from -->{self.extracted_from_id}'
            )
        if self.observed_on:
            links.append(
                f'{self.id}-- observed on -->{self.observed_on_id}'
            )
        if self.involved_observables:
            for obj in self.involved_observables.all():
                links.append(
                    f'{self.id}-- involves -->{obj.id}'
                )
        return nodes, clicks, links

    @property
    def absolute_url(self):
        return self.get_absolute_url()

    @staticmethod
    def get_user_events(user, case=None):
        if case:
            return Event.objects.filter(case=case)
        return Event.objects.all()

    @staticmethod
    def get_if_exists(name, case_id):
        objects = Event.objects.filter(name=name, case__id=case_id)
        return bool(objects), objects


class PiRogueExperiment(Entity):
    class Meta:
        verbose_name = 'PiRogue experiment'

    name = models.CharField(
        max_length=512,
    )
    pcap = models.ForeignKey(
        Artifact,
        on_delete=models.CASCADE,
        related_name='pirogue_dump_pcap_file'
    )
    socket_trace = models.ForeignKey(
        Artifact,
        on_delete=models.CASCADE,
        related_name='pirogue_dump_socket_trace_file'
    )
    target_device = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pirogue_dump_device'
    )
    target_artifact = models.ForeignKey(
        Artifact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pirogue_dump_artifact'
    )
    sslkeylog = models.ForeignKey(
        Artifact,
        on_delete=models.CASCADE,
        related_name='pirogue_dump_ssl_keys'
    )
    screencast = models.ForeignKey(
        Artifact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pirogue_dump_screencast'
    )
    aes_trace = models.ForeignKey(
        Artifact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pirogue_aes_trace'
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

    analysis_index = models.CharField(
        max_length=64,
        default=_random_id,
        help_text=_('Elasticsearch index storing the analysis.'),
        editable=True
    )
    @property
    def value(self):
        return self.name

    @property
    def icon(self):
        c = self.__class__
        return icons.get(c, '')

    def __str__(self):
        return f'{self.name}'

    @property
    def color(self):
        c = self.__class__
        return color_scheme.get(c, '')

    @property
    def super_type(self):
        return self.__class__.__name__

    @cached_property
    def analysis(self):
        from elasticsearch_dsl import connections
        connections.create_connection(hosts=['elasticsearch'], timeout=20)
        try:
            search = PiRogueExperimentAnalysis.search(index=self.get_es_index())
            search.sort('timestamp')
            total = search.count()
            search = search[0:total]
            return search.sort('-timestamp').execute()
        except Exception as e:
            return None

    def get_es_index(self):
        return f'c.{self.case.es_prefix}.ex.{self.analysis_index}'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_experiment_details_view', kwargs={'pk': self.id})

    @property
    def to_mermaid(self):
        icon = ''
        if self.icon:
            icon = f'fa:{self.icon}'
        links = []
        nodes = [
            f'{self.id}("{icon} {self.name}")',
            ]
        clicks = [
            f'click {self.id} "{self.get_absolute_url()}"',
            f'class {self.id} PiRogueExperiment'
        ]
        if self.pcap:
            links.append(f'{self.id}-- generated -->{self.pcap_id}')
        if self.socket_trace:
            links.append(f'{self.id}-- generated -->{self.socket_trace_id}')
        if self.target_device:
            links.append(f'{self.id}-- executed on -->{self.target_device_id}')
        if self.target_artifact:
            links.append(f'{self.id}-- execution of -->{self.target_artifact_id}')
        if self.sslkeylog:
            links.append(f'{self.id}-- generated -->{self.sslkeylog_id}')
        if self.screencast:
            links.append(f'{self.id}-- generated -->{self.screencast_id}')
        if self.aes_trace:
            links.append(f'{self.id}-- generated -->{self.aes_trace_id}')
        return nodes, clicks, links

    @property
    def absolute_url(self):
        return self.get_absolute_url()

    @staticmethod
    def get_user_pirogue_dumps(user, case=None):
        if case:
            return PiRogueExperiment.objects.filter(case=case)
        return PiRogueExperiment.objects.all()


class ObservableAnalysisEngine(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier.'),
        editable=False
    )
    observable_type = models.ForeignKey(
        ObservableType,
        on_delete=models.CASCADE,
        help_text=_('Type of observable this engine can handle.')
    )
    name = models.CharField(
        max_length=512,
    )
    description = models.TextField(
        help_text=_('Add more details about this engine.'),
        null=True,
        blank=True
    )
    source_url = models.URLField(
        help_text=_('Specify the link to this engine.'),
        verbose_name='Source URL',
        null=True,
        blank=True
    )

class BackendCredentials(models.Model):
    class Meta:
        ordering = ['last_usage']
        unique_together = ['backend', 'credentials']

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier.'),
        editable=False
    )
    backend = models.CharField(
        max_length=512,
        verbose_name=_('backend identifier'),
        default=''
    )
    last_usage = models.DateTimeField(
        default=timezone.now
    )
    credentials = HStoreField(
        default=dict
    )


class PiRogueExperimentAnalysis(Document):
    owner = Keyword(required=True)
    case_id = Keyword()
    experiment_id = Keyword()
    decoded_data = Text()
    analysis_date = Date()
    detections = Object()
    result = Object()
    tracker = Object()
    timestamp = Date()

    @property
    def analysis_id(self):
        return self.meta.id


# class IndexedEntity(Document):
#     owner = Keyword(required=True)
#     case_id = Keyword()
#     entity_id = Keyword()
#     super_type = Keyword()
#     type = Keyword()
#     value = Keyword()
#
#
# def _index_entity(entity, index_name):
#     pass
#
# @receiver(post_save, sender=Observable)
# def index_observable(sender, instance, **kwargs):
#     ie = IndexedEntity()
#     ie.owner = instance.owner.id
#     ie.super_type = "Observable"


class UploadRequest(models.Model):
    class Status(models.TextChoices):
        CREATED = 'CREATED', _('Created')
        PROCESSING = 'PROCESSING', _('Processing')
        SUCCEEDED = 'SUCCEEDED', _('Succeeded')
        FAILED = 'FAILED', _('Failed')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Creation date of this object.'),
        editable=False
    )

    eof = models.BooleanField(default=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        editable=False
    )
    name = models.CharField(
        max_length=512,
        blank=True,
        null=True
    )
    size = models.IntegerField(
        default=0
    )
    next_addr = models.IntegerField(
        default=0
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.CREATED,
    )
    chunks = models.JSONField(blank=True, null=True)

    # Weak reference style
    # Will be set only at Artifact (first data) POST
    target_artifact_id = models.CharField(
        max_length=36,
        blank=True,
        null=True
    )

    @property
    def path(self):
        import pathlib
        extension = pathlib.Path(self.name).suffix
        return f'/tmp/upload.{self.id}{extension}'

    def cleanup(self):
        if os.path.exists(self.path):
            os.remove(self.path)

@receiver(pre_delete, sender=UploadRequest, dispatch_uid='delete_upload_request_file')
def delete_upload_request_stored_files(sender, instance: UploadRequest, using, **kwargs):
    instance.cleanup()

colander_models = {
    'Case': Case,
    'Actor': Actor,
    'Artifact': Artifact,
    'DetectionRule': DetectionRule,
    'Device': Device,
    'Event': Event,
    'Observable': Observable,
    'EntityRelation': EntityRelation,
    'PiRogueExperiment': PiRogueExperiment,
    'Threat': Threat,
}

icons = {
    Actor: 'fa-users',
    Artifact: 'fa-archive',
    DetectionRule: 'fa-magic',
    Device: 'fa-server',
    Event: 'fa-bolt',
    Observable: 'fa-bullseye',
    EntityRelation: 'fa-link',
    PiRogueExperiment: 'fa-flask',
    Threat: 'fa-bug',
}

color_scheme = {
    Actor: '#8dd3c7',
    Artifact: '#ffffb3',
    DetectionRule: '#bebada',
    Device: '#fb8072',
    Event: '#80b1d3',
    Observable: '#fdb462',
    EntityRelation: '#b3de69',
    PiRogueExperiment: '#fccde5',
    Threat: '#d9d9d9',
    # #bc80bd #ccebc5 #ffed6f
}
