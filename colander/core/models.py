import base64
import logging
import os
import random
import string
import uuid
from copy import deepcopy
from hashlib import sha256
from io import StringIO
from tempfile import TemporaryDirectory

import django
from colander_data_converter.base.models import ColanderFeed
from colander_data_converter.exporters.template import TemplateExporter
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import HStoreField
from django.core.validators import FileExtensionValidator
from django.db import models, IntegrityError
from django.db.models import F, Q, JSONField
from django.db.models.signals import pre_delete, pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from elasticsearch_dsl import Date, Document, Index, Keyword, Object, Text, Boolean, Search
from elasticsearch_dsl.response import Response
from requests.structures import CaseInsensitiveDict


logger = logging.getLogger(__name__)


class BusinessIntegrityError(IntegrityError):
    """Generic Error class to raise and describe business logic violation"""
    pass


class OverwritableFileFieldAttrClass(models.fields.files.FieldFile):
    """attr_class used by colander.core.models.OverwritableFileField.
    This attr_class performs the actual task of supporting overwrites on existing files."""

    def __init__(self, instance, field, name):
        super().__init__(instance, field, name)

    def save(self, name, content, save=True):

        if self.field.overwrite_existing_file:
            name = self.field.generate_filename(self.instance, name)
            if self.storage.exists(name):
                self.storage.delete(name)

        super().save(name, content, save)


class OverwritableFileField(models.FileField):
    """A Django FileField that supports existing file overwrite.
    Existing file with same name will be overwritten if 'overwrite_existing_file' is True.
    """
    attr_class = OverwritableFileFieldAttrClass

    def __init__(self, overwrite_existing_file=False, **kwargs):
        self.overwrite_existing_file = overwrite_existing_file
        super().__init__(**kwargs)

    def clean(self, value, model_instance):
        # Supports edge case when:
        # - external storage API is used for FileField
        # - 'upload_to' FileField use a generator function that does not include file extension
        # - 'validators' are used on this FileField (eg: FileExtensionValidator)
        # - Form is POSTED for 'update'
        # Fix: 'case' is only present @update. It's not present @create lifecycle.
        if (hasattr(model_instance, 'case') and
            value == self.generate_filename(model_instance, "dummy-file-name")):
            return value
        return super().clean(value, model_instance)


class Appendix:
    class TlpPap:
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

    class ExportType:
        UNSPECIFIED = 'UNSPECIFIED'
        CASE = 'CASE'
        EXPORT_TYPE_CHOICES = [
            (UNSPECIFIED, 'UNSPECIFIED'),
            (CASE, 'CASE'),
        ]

    class NotificationType:
        INTERNAL = 'INTERNAL'
        MAIL = 'MAIL'
        NOTIFICATION_TYPE_CHOICES = [
            (INTERNAL, 'INTERNAL'),
            (MAIL, 'MAIL'),
        ]


def list_accepted_levels(input_level: str):
    triggered = False
    levels = []
    for _, level in Appendix.TlpPap.TLP_PAP_CHOICES:
        if input_level.upper() == level:
            triggered = True
        if triggered:
            levels.append(level)
    return levels


class ColanderTeam(models.Model):
    name = models.CharField(
        max_length=512,
        verbose_name=_('name'),
        help_text=_('Give a meaningful name to this team.'),
        default=''
    )
    contributors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='teams_as_contrib',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        related_name='teams_as_owner',
    )

    def get_all_contributors(self):
        users = []
        users.extend(self.contributors.all())
        users.append(self.owner)
        return list(set(users))

    @cached_property
    def team_cases(self):
        return self.get_team_cases()

    def get_team_cases(self):
        return Case.objects.filter(teams=self).all()

    @staticmethod
    def get_my_teams(user):
        return ColanderTeam.objects.filter(Q(contributors=user) | Q(owner=user)).distinct().all()

    @staticmethod
    def get_my_teams_as_contrib(user):
        return ColanderTeam.objects.filter(contributors=user).distinct().all()

    @staticmethod
    def get_my_teams_as_owner(user):
        return ColanderTeam.objects.filter(owner=user).distinct().all()

    @staticmethod
    def get_user_teams(user):
        return user.my_teams

    def __str__(self):
        return f'{self.name} managed by {self.owner}'


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
    icon = models.TextField(
        blank=True,
        null=True
    )
    nf_icon = models.CharField(
        max_length=256,
        blank=True,
        null=True
    )
    value_example = models.TextField(
        blank=True,
        null=True
    )
    regex = models.TextField(
        blank=True,
        null=True
    )
    default_attributes = HStoreField(
        verbose_name='Default attributes',
        blank=True,
        null=True
    )
    type_hints = JSONField(
        verbose_name='Type hints',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name


class ArtifactType(CommonModelType):
    @staticmethod
    def get_by_short_name(short_name) -> 'ArtifactType':
        return ArtifactType.objects.get(short_name__iexact=short_name)


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


class DataFragmentType(CommonModelType):
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
    teams = models.ManyToManyField(
        ColanderTeam,
        related_name='cases',
        help_text=_('Share this case with the selected teams. Press ctrl on your keyboard to select/deselect teams.'),
        blank=True,
        null=True,
    )
    name = models.CharField(
        max_length=512,
        verbose_name=_('name'),
        help_text=_('Give a meaningful name to the case.'),
        default=''
    )
    description = models.TextField(
        help_text=_('Add more details about the case here.')
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_('Who owns the current case.'),
        related_name='cases',
        editable=True
    )
    parent_case = models.ForeignKey(
        'self',
        help_text=_('Make this case a sub-case of another one.'),
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
        default=_random_id)
    public_key = models.TextField(
        editable=True,
        default=''
    )
    documentation = models.TextField(
        help_text=_('Case documentation.'),
        blank=True,
        null=True,
        editable=True
    )
    tlp = models.CharField(
        max_length=6,
        choices=Appendix.TlpPap.TLP_PAP_CHOICES,
        help_text=_('Traffic Light Protocol, designed to indicate the sharing boundaries to be applied.'),
        verbose_name='Default TLP level of the case',
        default=Appendix.TlpPap.WHITE
    )
    pap = models.CharField(
        max_length=6,
        choices=Appendix.TlpPap.TLP_PAP_CHOICES,
        help_text=_('Permissible Actions Protocol, designed to indicate how the received information can be used.'),
        verbose_name='Default PAP level of the case',
        default=Appendix.TlpPap.WHITE
    )

    overrides = models.JSONField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.generate_key_pair(save=False)
        super().save(*args, **kwargs)

    def can_contribute(self, user):
        return self in user.all_my_cases

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('case_details_view', kwargs={'pk': self.id})

    @property
    def value(self):
        return self.name

    @cached_property
    def is_parent_case(self):
        return Case.objects.filter(parent_case_id=self.id).exists()

    @property
    def is_sub_case(self):
        return self.parent_case is not None

    @cached_property
    def subcases(self):
        return Case.objects.filter(parent_case_id=self.id).all()

    @cached_property
    def archives(self):
        return ArchiveExport.objects.filter(
            case_id=self.id, type=Appendix.ExportType.CASE
        ).all()

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
            self.public_key = public_pem.decode('utf-8')
            if save:
                self.save()

    def quick_search(self, value, type=None, exclude_types=['EntityRelation', 'Case']):
        models = colander_models
        if type and type in models:
            # If type is used, force no type exclusion
            models = {type: models.get(type)}
            exclude_types = []
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
                    results.extend(objects.all())
            except Exception as e:
                logger.error(e, extra={'model': model})
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
        entities = self.get_all_entities(exclude_types=['Event', 'Case'])
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

    @property
    def entities(self):
        return self.quick_search('')

    @property
    def events(self):
        return Event.objects.filter(case=self).order_by('-first_seen').all()

    @property
    def relations(self):
        return self.quick_search('', type='EntityRelation')

    @staticmethod
    def get_user_cases(user):
        return user.all_my_cases


def _get_subgraph_thumbnails_storage_dir(instance, filename):
    case_id = instance.case.id
    return f'cases/{case_id}/subgraph_thumbnails/{instance.id}'


class SubGraph(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier.'),
        editable=False,
    )
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_related",
        related_query_name="%(app_label)s_%(class)ss",
    )
    name = models.CharField(
        max_length=512,
        verbose_name=_('name'),
        help_text=_('Give a meaningful name to this SubGraph.'),
        default=''
    )
    description = models.TextField(
        help_text=_('Add more details about this SubGraph.'),
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

    overrides = models.JSONField(blank=True, null=True)

    thumbnail = OverwritableFileField(
        overwrite_existing_file=True,
        upload_to=_get_subgraph_thumbnails_storage_dir,
        max_length=512,
        blank=True, null=True
    )

    def pinned(self):
        return True

    @property
    def absolute_url(self):
        from django.urls import reverse
        return reverse('subgraph_editor_view', kwargs={'case_id': self.case.id, 'pk': self.id})

    @property
    def thumbnail_url(self):
        from django.urls import reverse
        return reverse('subgraph_thumbnail_view', kwargs={'case_id': self.case.id, 'pk': self.id})

    @staticmethod
    def get_pinned(user, case):
        pinned_entities_ids = list()

        if user.preferences:
            if 'pinned_entities' in user.preferences:
                pinned_entities_ids = user.preferences['pinned_entities'].keys()

        return SubGraph.objects.filter(owner=user, case=case).filter(id__in=pinned_entities_ids)

    @property
    def entities(self):
        return self.case.entities

    @property
    def relations(self):
        return self.case.relations


@receiver(pre_delete, sender=SubGraph, dispatch_uid='delete_subgraph_thumbnail')
def delete_subgraph_stored_thumbnails(sender, instance: SubGraph, using, **kwargs):
    if instance.thumbnail:
        instance.thumbnail.delete()


def _get_entity_thumbnails_storage_dir(instance, filename):
    case_id = instance.case.id
    return f'cases/{case_id}/entity_thumbnails/{instance.id}'


class Entity(models.Model):
    class Meta:
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
        blank=True,
        max_length=2048,
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
        choices=Appendix.TlpPap.TLP_PAP_CHOICES,
        help_text=_('Traffic Light Protocol, designed to indicate the sharing boundaries to be applied.'),
        verbose_name='TLP',
        default=Appendix.TlpPap.WHITE
    )
    pap = models.CharField(
        max_length=6,
        choices=Appendix.TlpPap.TLP_PAP_CHOICES,
        help_text=_('Permissible Actions Protocol, designed to indicate how the received information can be used.'),
        verbose_name='PAP',
        default=Appendix.TlpPap.WHITE
    )
    thumbnail = OverwritableFileField(
        overwrite_existing_file=True,
        upload_to=_get_entity_thumbnails_storage_dir,
        max_length=512,
        blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])]
    )

    def get_relations(self):
        relations = self.get_in_relations()
        relations += self.get_out_relations()
        return relations

    def get_in_relations(self):
        relations = []
        relations += EntityRelation.objects.filter(obj_to_id=self.id).all()
        relations += self.in_immutable_relations
        return relations

    def get_out_relations(self):
        relations = []
        relations += EntityRelation.objects \
            .filter(obj_from_id=self.id) \
            .exclude(obj_from_id=F('obj_to_id')).all()
        relations += self.out_immutable_relations
        return relations

    @property
    def relations(self):
        return self.get_relations()

    @property
    def in_immutable_relations(self):
        return []

    @property
    def out_immutable_relations(self):
        return []

    @property
    def in_relations(self):
        return self.get_in_relations()

    @property
    def out_relations(self):
        return self.get_out_relations()

    @property
    def sorted_comments(self):
        return self.comments.order_by('created_at')

    @staticmethod
    def filter_by_name_or_value(owner, name_or_value='', q_type=None, exclude_types=['EntityRelation']):
        q_sub_models = colander_models
        if q_type and q_type in q_sub_models:
            q_sub_models = {q_type: q_sub_models.get(q_type)}
        field_name = ''
        results = []
        for name, model in q_sub_models.items():
            if name == 'Case':
                continue
            if name in exclude_types:
                continue
            if hasattr(model, 'name'):
                field_name = 'name'
            elif hasattr(model, 'value'):
                field_name = 'value'
            try:
                objects = model.objects.filter(**{f'{field_name}__icontains': name_or_value, 'owner': owner})
                results.extend(objects.all())
            except Exception as e:
                print(model, e)
                pass
        results.sort(key=lambda a: a.updated_at, reverse=True)
        return results

    def concrete(self):
        if self.id is None:
            raise Exception("Need an id to resolve concrete")
        obj = None
        for name, model in colander_models.items():
            try:
                obj = model.objects.get(pk=self.id)
                break
            except model.DoesNotExist:
                obj = None
        if obj is None:
            raise Exception(f"Concrete type not found for entity id: {self.id}")
        return obj

    @property
    def thumbnail_url(self):
        if bool(self.thumbnail):
            from django.urls import reverse
            return reverse('entity_thumbnail_view', kwargs={'case_id': self.case.id, 'pk': self.id})
        else:
            return None


@receiver(pre_delete, sender=Entity, dispatch_uid='delete_entity_thumbnail')
def delete_entity_stored_thumbnails(sender, instance: Entity, using, **kwargs):
    if instance.thumbnail:
        instance.thumbnail.delete()


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
        return f'{self.name} ({self.type.name})'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_actor_details_view', kwargs={'case_id': self.case.id, 'pk': self.id})

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
            return Actor.objects.filter(case=case).all()
        return Actor.objects.filter(case__in=user.all_my_cases).all()


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
        help_text=_('Add custom attributes to this device.'),
        verbose_name='Custom attributes',
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
        return f'{self.name} ({self.type.name})'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_device_details_view', kwargs={'case_id': self.case.id, 'pk': self.id})

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
            return Device.objects.filter(case=case).all()
        return Device.objects.filter(case__in=user.all_my_cases).all()

    @property
    def in_immutable_relations(self):
        relations = []
        if self.operated_by:
            relations.append(
                EntityRelation.immutable_instance(
                    name="operates",
                    source=self.operated_by,
                    target=self
                )
            )
        return relations


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
        blank=True, null=True
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
        help_text=_('Add custom attributes to this artifact.'),
        verbose_name='Custom attributes',
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
            self.case.public_key.encode('utf-8'),
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
        return self.type.short_name in ['IMAGE', 'VIDEO', 'WEBPAGE']

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
        return f'{self.original_name} ({self.type}) - [{self.created_at}]'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_artifact_details_view', kwargs={'case_id': self.case.id, 'pk': self.id})

    @cached_property
    def analysis(self):
        from elasticsearch_dsl import connections
        connections.create_connection(hosts=['elasticsearch'], timeout=20)
        try:
            search: Search = ArtifactAnalysis.search(index=self.get_es_index())
            search.sort('-timestamp')
            total = search.count()
            search = search[0]
            response: Response = search.execute()
            if len(response.hits) > 0:
                hit = response.hits[0]
                return hit
            return None
        except Exception:
            return None

    def get_es_index(self):
        return f'c.{self.case.es_prefix}.art.{self.analysis_index}'

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
            return Artifact.objects.filter(case=case).all()
        return Artifact.objects.filter(case__in=user.all_my_cases).all()

    @property
    def out_immutable_relations(self):
        relations = []
        if self.extracted_from:
            relations.append(
                EntityRelation.immutable_instance(
                    name="extracted from",
                    source=self,
                    target=self.extracted_from
                )
            )
        return relations


@receiver(pre_delete, sender=Artifact, dispatch_uid='delete_artifact_file')
def delete_artifact_stored_files(sender, instance: Artifact, using, **kwargs):
    instance.file.delete()
    from elasticsearch_dsl import connections
    connections.create_connection(hosts=['elasticsearch'], timeout=20)
    index_name = instance.get_es_index()
    try:
        index = Index(index_name)
        if index.exists():
            index.delete()
    except Exception as e:
        logger.error(e)


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
        return reverse('collect_threat_details_view', kwargs={'case_id': self.case.id, 'pk': self.id})

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
        return f'{self.name} ({self.type.name})'

    @staticmethod
    def get_user_threats(user, case=None):
        if case:
            return Threat.objects.filter(case=case).all()
        return Threat.objects.filter(case__in=user.all_my_cases).all()


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
        help_text=_('Optional field containing an arbitrary string of your choice.'),
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
        help_text=_('Add custom attributes to this observable.'),
        verbose_name='Custom attributes',
        blank=True,
        null=True
    )
    es_prefix = models.CharField(
        max_length=16,
        editable=False,
        default=_random_id)

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
        return f'{self.value} ({self.type.name})'

    def get_es_index(self):
        return f'c.{self.case.es_prefix}.o.{self.type.short_name.lower()}'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_observable_details_view', kwargs={'case_id': self.case.id, 'pk': self.id})

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
        return self.events.order_by('-first_seen')

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
            return Observable.objects.filter(case=case).all()
        return Observable.objects.filter(case__in=user.all_my_cases).all()

    @property
    def out_immutable_relations(self):
        relations = []
        if self.extracted_from:
            relations.append(
                EntityRelation.immutable_instance(
                    name="extracted from",
                    source=self,
                    target=self.extracted_from
                )
            )
        if self.associated_threat:
            relations.append(
                EntityRelation.immutable_instance(
                    name="indicates",
                    source=self,
                    target=self.associated_threat
                )
            )
        return relations

    @property
    def in_immutable_relations(self):
        relations = []
        for e in self.sorted_events:
            relations.append(
                EntityRelation.immutable_instance(
                    name="involves",
                    source=e,
                    target=self
                )
            )
        if self.operated_by:
            relations.append(
                EntityRelation.immutable_instance(
                    name="operates",
                    source=self.operated_by,
                    target=self
                )
            )
        return relations


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

    immutable = False

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
        return EntityRelation.objects.filter(case__in=user.all_my_cases).all()

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

    @staticmethod
    def immutable_instance(source, target, name):
        ier = EntityRelation(
            name=name,
            obj_from=source,
            obj_to=target,
        )
        ier.id = f'{source.id}|{name}|{target.id}'
        ier.immutable = True
        return ier


@receiver(pre_save, sender=EntityRelation, dispatch_uid="bic_entity_relation_pre_save")
def bic_entity_relation_pre_save(sender, instance, **kwargs):
    if instance.case.pk != instance.obj_from.case.pk:
        raise BusinessIntegrityError("Relation 'case' differs from related source entity 'case'")
    if instance.case.pk != instance.obj_to.case.pk:
        raise BusinessIntegrityError("Relation 'case' differs from related target entity 'case'")


@receiver(pre_delete, sender=Entity, dispatch_uid="entity_relation_cascade")
def entity_relation_cascade(sender, instance, using, **kwargs):
    EntityRelation.objects.filter(
        # obj_from_type=ContentType.objects.get_for_model(instance),
        obj_from_id=str(instance.pk)
    ).delete()

    EntityRelation.objects.filter(
        # obj_to_type=ContentType.objects.get_for_model(instance),
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
        return reverse('collect_relation_details_view', kwargs={'case_id': self.case.id, 'pk': self.id})

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
            return ObservableRelation.objects.filter(case=case).all()
        return ObservableRelation.objects.filter(case__in=user.all_my_cases).all()


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
        return f'{self.value} ({self.type.name})'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_detection_rule_details_view', kwargs={'case_id': self.case.id, 'pk': self.id})

    @property
    def absolute_url(self):
        return self.get_absolute_url()

    @staticmethod
    def get_user_detection_rules(user, case=None):
        if case:
            return DetectionRule.objects.filter(case=case).all()
        return DetectionRule.objects.filter(case__in=user.all_my_cases).all()


class DataFragment(Entity):
    name = models.CharField(
        max_length=512,
        help_text=_('Name of this fragment of data.'),
    )
    type = models.ForeignKey(
        DataFragmentType,
        on_delete=models.CASCADE,
        help_text=_('Type of this fragment of data.')
    )
    content = models.TextField()
    extracted_from = models.ForeignKey(
        Artifact,
        help_text=_('Select the artifact from which this fragment of data was extracted.'),
        on_delete=models.SET_NULL,
        related_name='data_fragments',
        null=True,
        blank=True,
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
        return f'{self.value} ({self.type.name})'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_data_fragment_details_view', kwargs={'case_id': self.case.id, 'pk': self.id})

    @property
    def absolute_url(self):
        return self.get_absolute_url()

    @property
    def to_mermaid(self):
        icon = ''
        if self.icon:
            icon = f'fa:{self.icon}'
        links = []

        label = f'<samp>{self.name}</samp><br><small><i>{self.type.name}</i></small>'
        nodes = [
            f'{self.id}("{icon} {label}")',
        ]
        clicks = [
            f'click {self.id} "{self.get_absolute_url()}"',
            f'class {self.id} DataFragment'
        ]
        if self.extracted_from:
            links.append(
                f'{self.id}-- extracted from -->{self.extracted_from_id}'
            )
        return nodes, clicks, links

    @staticmethod
    def get_user_data_fragments(user, case=None):
        if case:
            return DataFragment.objects.filter(case=case).all()
        return DataFragment.objects.filter(case__in=user.all_my_cases).all()

    @property
    def out_immutable_relations(self):
        relations = []
        if self.extracted_from:
            relations.append(
                EntityRelation.immutable_instance(
                    name="extracted from",
                    source=self,
                    target=self.extracted_from
                )
            )
        return relations


class Event(Entity):
    type = models.ForeignKey(
        EventType,
        on_delete=models.CASCADE,
        help_text=_('Type of this event.')
    )
    first_seen = models.DateTimeField(
        help_text=_('First time you observed this event.'),
        default=django.utils.timezone.now
    )
    last_seen = models.DateTimeField(
        help_text=_('Most recent time you observed this event.'),
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
        null=True,
        blank=True,
    )
    attributed_to = models.ForeignKey(
        Actor,
        help_text=_('Select the actor attributed to this event.'),
        on_delete=models.SET_NULL,
        related_name='attributed_events',
        null=True,
        blank=True,
    )
    target = models.ForeignKey(
        Actor,
        help_text=_('Select the actor targeted during this event.'),
        on_delete=models.SET_NULL,
        related_name='targeted_events',
        null=True,
        blank=True,
    )
    attributes = HStoreField(
        help_text=_('Add custom attributes to this event.'),
        verbose_name='Custom attributes',
        null=True,
        blank=True
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
        return f'{self.name} ({self.type.name})'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_event_details_view', kwargs={'case_id': self.case.id, 'pk': self.id})

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
            return Event.objects.filter(case=case).order_by('-first_seen').all()
        return Event.objects.filter(case__in=user.all_my_cases).order_by('-first_seen').all()

    @staticmethod
    def get_if_exists(name, case_id):
        objects = Event.objects.filter(name=name, case__id=case_id)
        return bool(objects), objects

    @property
    def out_immutable_relations(self):
        relations = []
        if self.extracted_from:
            relations.append(
                EntityRelation.immutable_instance(
                    name="extracted from",
                    source=self,
                    target=self.extracted_from
                )
            )
        if self.observed_on:
            relations.append(
                EntityRelation.immutable_instance(
                    name="observed on",
                    source=self,
                    target=self.observed_on
                )
            )
        if self.detected_by:
            relations.append(
                EntityRelation.immutable_instance(
                    name="detected by",
                    source=self,
                    target=self.detected_by
                )
            )
        if self.attributed_to:
            relations.append(
                EntityRelation.immutable_instance(
                    name="attributed to",
                    source=self,
                    target=self.attributed_to
                )
            )
        if self.target:
            relations.append(
                EntityRelation.immutable_instance(
                    name="target",
                    source=self,
                    target=self.target
                )
            )
        if self.involved_observables:
            for io in self.involved_observables.all():
                relations.append(
                    EntityRelation.immutable_instance(
                        name="involves",
                        source=self,
                        target=io
                    )
                )
        return relations


class FeedTemplate(models.Model):
    class Meta:
        ordering = ['name']

    class Visibility:
        CASES = "Cases"
        # TEAMS = "Teams"
        PUBLIC = "Public"
        VISIBILITY_CHOICES = [
            (CASES, "Cases"),
            # (TEAMS, "Teams"),
            (PUBLIC, "Public"),
        ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier.'),
        editable=False
    )
    name = models.CharField(
        max_length=512,
    )
    description = models.TextField(
        help_text=_('Add more details about this object.'),
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
    content = models.TextField()
    in_error = models.BooleanField(
        default=False,
        editable=False,
    )
    visibility = models.CharField(
        max_length=6,
        choices=Visibility.VISIBILITY_CHOICES,
        help_text=_('The visibility of the template, either limited to the case, to the teams or public'),
        verbose_name='Visibility',
        default=Visibility.CASES
    )
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_related",
        related_query_name="%(app_label)s_%(class)ss",
    )
    teams = models.ManyToManyField(
        ColanderTeam,
        related_name='templates',
        help_text=_('Share this template with the selected teams. Press ctrl to select/deselect teams.'),
        blank=True,
    )

    @classmethod
    def get_public_templates_qs(cls):
        return (FeedTemplate.objects.
                filter(visibility=cls.Visibility.PUBLIC)
                .order_by('name'))

    def used_by(self):
        include_clause = 'include "%s"' % self.name
        extend_clause = 'extends "%s"' % self.name
        includes = FeedTemplate.objects.filter(content__icontains=include_clause)
        extends = FeedTemplate.objects.filter(content__icontains=extend_clause)
        return includes.union(extends)

    # @classmethod
    # def get_teams_templates_qs(cls, teams):
    #     return (FeedTemplate.objects.
    #             filter(visibility=cls.Visibility.TEAMS).
    #             filter(teams__in=teams).
    #             order_by('name'))

    @classmethod
    def get_cases_templates_qs(cls, cases):
        return (FeedTemplate.objects.
                filter(visibility=cls.Visibility.CASES).
                filter(case__in=cases).
                order_by('name'))

    def __str__(self):
        return self.name

    def render(self, feed: dict) -> str:
        """
        Renders the content of an InternalFeed object using a specified template.

        This method uses the TemplateExporter to process the content of the
        feed and outputs the rendered result as a string. The TemplateExporter
        is initialized with the content of the feed and a template that is
        specified internally by the class. The final rendered content is
        returned as a string.

        Parameters:
            feed: The feed data.

        Returns:
            str: The rendered string output from the provided feed content.

        Raises:
            ~jinja2.TemplateError: If there are errors in template syntax or rendering
            ~jinja2.TemplateNotFound: If the specified template file cannot be found
            IOError: If there are issues writing to the output stream
        """
        # Copy all templates in the same folder
        with TemporaryDirectory() as tmpdir:
            for template in self.owner.available_templates_qs:
                with open(os.path.join(tmpdir, template.name), mode='w') as f:
                    f.write(template.content)
            colander_feed = ColanderFeed.load(feed)
            exporter = TemplateExporter(
                colander_feed,
                tmpdir,
                self.name
            )
            io = StringIO()
            exporter.export(io)
            io.seek(0)

            return io.read()


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
        return f'{self.name} (PiRogue experiment)'

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
        except Exception:
            return None

    def get_es_index(self):
        return f'c.{self.case.es_prefix}.ex.{self.analysis_index}'

    def get_traffic_es_index(self) -> str:
        """
        Generates the Elasticsearch index ID for traffic data.

        This method constructs and returns the Elasticsearch index string
        based on the specific format 'c.{es_prefix}.ex.{traffic_index}'.
        It uses the `es_prefix` and `traffic_index` attributes of the
        instance to dynamically generate the string.

        Returns:
            str: The Elasticsearch index ID, using the instance's
            `es_prefix` and `traffic_index` attributes, formatted as
            'c.{es_prefix}.ex.{traffic_index}'.
        """
        return f'c.{self.case.es_prefix}.ex.{self.traffic_index}'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collect_experiment_details_view', kwargs={'case_id': self.case.id, 'pk': self.id})

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
            return PiRogueExperiment.objects.filter(case=case).all()
        return PiRogueExperiment.objects.filter(case__in=user.all_my_cases).all()

    @property
    def out_immutable_relations(self):
        relations = []
        if self.pcap:
            relations.append(
                EntityRelation.immutable_instance(
                    name="generated",
                    source=self,
                    target=self.pcap
                )
            )
        if self.socket_trace:
            relations.append(
                EntityRelation.immutable_instance(
                    name="generated",
                    source=self,
                    target=self.socket_trace
                )
            )
        if self.target_device:
            relations.append(
                EntityRelation.immutable_instance(
                    name="executed on",
                    source=self,
                    target=self.target_device
                )
            )
        if self.target_artifact:
            relations.append(
                EntityRelation.immutable_instance(
                    name="execution of",
                    source=self,
                    target=self.target_artifact
                )
            )
        if self.sslkeylog:
            relations.append(
                EntityRelation.immutable_instance(
                    name="generated",
                    source=self,
                    target=self.sslkeylog
                )
            )
        if self.screencast:
            relations.append(
                EntityRelation.immutable_instance(
                    name="generated",
                    source=self,
                    target=self.screencast
                )
            )
        if self.aes_trace:
            relations.append(
                EntityRelation.immutable_instance(
                    name="generated",
                    source=self,
                    target=self.aes_trace
                )
            )
        if self.extra_files:
            for ef in self.extra_files.all():
                relations.append(
                    EntityRelation.immutable_instance(
                        name="generated",
                        source=self,
                        target=ef
                    )
                )
        return relations


@receiver(pre_delete, sender=PiRogueExperiment, dispatch_uid='delete_elastic_search_experiment_index')
def delete_experiment(sender, instance: PiRogueExperiment, using, **kwargs):
    print(f'Delete the PiRogue experiment [{instance.name}] {instance.id}')
    from elasticsearch_dsl import connections
    connections.create_connection(hosts=['elasticsearch'], timeout=20)
    index_name = instance.get_es_index()
    try:
        index = Index(index_name)
        if index.exists():
            index.delete()
    except Exception as e:
        logger.error(e)


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


class ArtifactAnalysis(Document):
    owner = Keyword(required=True)
    case_id = Keyword(required=True)
    artifact_id = Keyword(required=True)
    error = Keyword()
    error_short = Keyword()
    success = Boolean()
    content = Text()
    processors = Object()
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
    target_entity_id = models.CharField(
        max_length=36,
        blank=True,
        null=True
    )

    @property
    def path(self):
        import pathlib
        extension = pathlib.Path(self.name).suffix
        return f'/tmp/upload.{self.id}{extension}'

    def touch(self):
        if not self.name:
            raise Exception("Can't touch file without name")
        if self.size == 0:
            open(self.path, 'wb').close()
            # raise Exception("Can't touch zero sized file")
        else:
            with open(self.path, 'wb') as f:
                f.seek(self.size - 1)
                f.write(b'\0')

    def append_chunk(self, addr, buf):
        if str(addr) not in self.chunks:
            raise Exception(f"Invalid chunk addr@{addr}")

        expected_hash = self.chunks.get(str(addr))
        buf_hash = sha256(buf).hexdigest()

        if not expected_hash == buf_hash:
            raise Exception(f"Integrity fail for chunk addr@{addr}")

        with open(self.path, mode='r+b') as destination:
            destination.seek(int(addr))
            destination.write(buf)
            destination.flush()

        self.chunks.pop(str(addr))

        if len(self.chunks) > 0:
            self.next_addr = list(self.chunks.keys())[0]
            self.status = UploadRequest.Status.PROCESSING
        else:
            self.eof = True
            self.next_addr = -1
            self.status = UploadRequest.Status.SUCCEEDED

    def cleanup(self):
        if self.name:
            if os.path.exists(self.path):
                os.remove(self.path)


@receiver(pre_delete, sender=UploadRequest, dispatch_uid='delete_upload_request_file')
def delete_upload_request_stored_files(sender, instance: UploadRequest, using, **kwargs):
    instance.cleanup()


class OutgoingFeed(models.Model):
    class Meta:
        ordering = ['name']

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier.'),
        editable=False
    )
    name = models.CharField(
        max_length=512,
    )
    secret = models.CharField(
        max_length=512,
        help_text=_('Feeds are protected by a secret. You can reset it at anytime invalidating the previous one.'),
        default=_random_id
    )
    description = models.TextField(
        help_text=_('Add more details about this feed.'),
        null=True,
        blank=True
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_('Who owns this feed.'),
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
    max_tlp = models.CharField(
        max_length=6,
        choices=Appendix.TlpPap.TLP_PAP_CHOICES,
        help_text=_('Traffic Light Protocol, designed to indicate the sharing boundaries to be applied.'),
        verbose_name='Maximum TLP level of exported data',
        default=Appendix.TlpPap.WHITE
    )
    max_pap = models.CharField(
        max_length=6,
        choices=Appendix.TlpPap.TLP_PAP_CHOICES,
        help_text=_('Permissible Actions Protocol, designed to indicate how the received information can be used.'),
        verbose_name='Maximum PAP level of exported data',
        default=Appendix.TlpPap.WHITE
    )


class EntityExportFeed(OutgoingFeed):
    misp_org_name = models.CharField(
        max_length=512,
        help_text=_(
            'Name of your organization as set in MISP. The Orgc name of your events will be set accordingly. '
            'Must be set to make your feed available in MISP format.'),
        verbose_name='MISP: name of your organization',
        blank=True,
        null=True
    )
    misp_org_id = models.CharField(
        max_length=512,
        help_text=_(
            'UUID of your organization as set in MISP. The Orgc UUID of your events will be set accordingly. '
            'Must be set to make your feed available in MISP format.'),
        verbose_name='MISP: UUID of your organization',
        blank=True,
        null=True
    )
    content_type = models.ManyToManyField(
        ContentType,
        related_name='entity_out_feed_types',
        limit_choices_to={
            'model__in': ['actor', 'artifact', 'datafragment', 'detectionrule', 'device', 'observable', 'threat'],
            'app_label': 'core',
        },
    )

    @property
    def feed_type(self):
        return 'entities'

    def get_entities(self):
        entities = []
        for entity_type in self.content_type.all():
            if hasattr(entity_type.model_class(), 'tlp'):
                entities.extend(entity_type.model_class().objects.filter(
                    case=self.case,
                    tlp__in=self.tlp_levels,
                    pap__in=self.pap_levels).all())
            else:
                entities.extend(entity_type.model_class().objects.filter(case=self.case).all())
        return entities

    def get_relations(self):
        return [e for e in EntityRelation.objects.filter(
            obj_from_id__in=self.entity_ids,
            obj_to_id__in=self.entity_ids,
            case=self.case,
        ).iterator()]

    @cached_property
    def tlp_levels(self):
        return list_accepted_levels(self.max_tlp)

    @cached_property
    def pap_levels(self):
        return list_accepted_levels(self.max_pap)

    @cached_property
    def cases(self):
        dummy_case = deepcopy(self.case)
        if self.case.tlp not in self.tlp_levels or self.case.pap not in self.pap_levels:
            dummy_case.name = 'REDACTED for confidentiality reasons.'
            dummy_case.description = 'REDACTED for confidentiality reasons.'
            dummy_case.documentation = 'REDACTED for confidentiality reasons.'
        return [dummy_case]

    @cached_property
    def entities(self):
        return self.get_entities()

    @cached_property
    def relations(self):
        return self.get_relations()

    @cached_property
    def entity_ids(self):
        return [e.id for e in self.get_entities()]

    @staticmethod
    def get_user_entity_out_feeds(user, case=None):
        if case:
            return EntityExportFeed.objects.filter(case=case).all()
        return EntityExportFeed.objects.filter(case__in=user.all_my_cases).all()


class DetectionRuleExportFeed(OutgoingFeed):
    content_type = models.ForeignKey(
        DetectionRuleType,
        on_delete=models.CASCADE
    )

    @staticmethod
    def get_user_detection_rule_out_feeds(user, case=None):
        if case:
            return DetectionRuleExportFeed.objects.filter(case=case).all()
        return DetectionRuleExportFeed.objects.filter(case__in=user.all_my_cases).all()

    @property
    def feed_type(self):
        return 'detection_rules'

    def get_entities(self):
        tlp_levels = list_accepted_levels(self.max_tlp)
        pap_levels = list_accepted_levels(self.max_pap)
        rules = DetectionRule.objects.filter(
            case=self.case,
            type=self.content_type,
            tlp__in=tlp_levels,
            pap__in=pap_levels)
        return rules.all()


class CustomExportFeed(OutgoingFeed):
    template = models.ForeignKey(
        FeedTemplate,
        on_delete=models.CASCADE
    )
    @staticmethod
    def get_user_custom_out_feeds(user, case=None):
        if case:
            return CustomExportFeed.objects.filter(case=case).all()
        return CustomExportFeed.objects.filter(case__in=user.all_my_cases).all()

    @property
    def feed_type(self):
        return 'custom'

    def get_content(self):
        from colander.core.feed.internal import InternalFeed  # prevents import loop
        try:
            rendered_content = self.template.render(InternalFeed(self.case).content)
            return rendered_content
        except (Exception,):
            return "An error occurred."


def _get_dropped_file_upload_dir(instance, filename):
    user_id = instance.owner.id
    return f'user/{user_id}/dropbox/{instance.id}'


class DroppedFile(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier.'),
        editable=False
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dropped_files',
    )

    dropped_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Drop date of this file.'),
        editable=False
    )

    name = models.CharField(
        max_length=512,
        blank=True,
        null=True
    )

    filename = models.CharField(
        max_length=512,
        blank=True,
        null=True
    )

    file = models.FileField(
        upload_to=_get_dropped_file_upload_dir,
        max_length=512,
        blank=True, null=True
    )

    mime_type = models.CharField(
        max_length=512,
        blank=True,
        null=True)

    case = models.ForeignKey(
        Case,
        help_text=_('Associated case of this dropped file.'),
        on_delete=models.SET_NULL,
        related_name='dropped_files',
        null=True,
        blank=True,
    )

    attributes = HStoreField(
        help_text=_('Custom attributes related to this dropped file.'),
        verbose_name='Custom attributes',
        null=True,
        blank=True
    )

    # Weak reference style
    # Will be set only at DroppedFile conversion POST
    target_artifact_id = models.CharField(
        max_length=36,
        blank=True,
        null=True
    )

    @staticmethod
    def all_drops_by_user(user):
        return (DroppedFile.objects
                .filter(owner=user)
                .exclude(target_artifact_id__gt='')
                .exclude(target_artifact_id__isnull=False))


@receiver(pre_delete, sender=DroppedFile, dispatch_uid='delete_dropped_file')
def delete_dropped_file_stored_file(sender, instance: DroppedFile, using, **kwargs):
    instance.file.delete()


def _get_export_file_dir(instance, filename):
    case_id = instance.case.id
    return f'cases/{case_id}/exports/{instance.id}'


class ArchiveExport(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier.'),
        editable=False
    )

    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_related",
        related_query_name="%(app_label)s_%(class)ss",
    )

    type = models.CharField(
        max_length=16,
        choices=Appendix.ExportType.EXPORT_TYPE_CHOICES,
        help_text=_('Export type.'),
        verbose_name='Export type',
        default=Appendix.ExportType.UNSPECIFIED,
    )

    requested_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Export request date.'),
        editable=False
    )

    done_at = models.DateTimeField(
        help_text=_('Export done date.'),
        editable=False,
        blank=True, null=True,
    )

    file = models.FileField(
        upload_to=_get_export_file_dir,
        max_length=512,
        blank=True, null=True
    )

    @property
    def is_done(self):
        return self.done_at is not None and self.file

    @property
    def is_pending(self):
        return not self.is_done

    @property
    def filename(self):
        return f"{self.case.name} - {self.requested_at.isoformat(timespec='minutes')}.zip"


@receiver(pre_delete, sender=ArchiveExport, dispatch_uid='delete_export_file')
def delete_archive_export_file(sender, instance: ArchiveExport, using, **kwargs):
    instance.file.delete()


class NotificationMessage(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier.'),
        editable=False
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )

    type = models.CharField(
        max_length=16,
        choices=Appendix.NotificationType.NOTIFICATION_TYPE_CHOICES,
        help_text=_('Notification type.'),
        verbose_name='Notification type',
        default=Appendix.NotificationType.INTERNAL,
    )

    requested_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Notification request date.'),
        editable=False
    )

    processed_at = models.DateTimeField(
        help_text=_('Notification process date.'),
        editable=False,
        blank=True, null=True,
    )

    success = models.BooleanField(
        help_text=_('Notification process result success.'),
        editable=False,
        default=False,
    )

    template_path = models.CharField(
        max_length=512,
        verbose_name=_('template_path'),
        help_text=_('Internal template path used to generate the notification content with the given context.'),
        default='',
    )

    context = JSONField(
        verbose_name='Template context used to generate the notification content.',
        default=dict,
    )


colander_models = CaseInsensitiveDict({
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
    'DataFragment': DataFragment,
})

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
    DataFragment: 'fa-code',
}

icons_unicodes = {
    Actor: '\uf0c0',
    Artifact: '\uf187',
    DetectionRule: '\uf0d0',
    Device: '\uf233',
    Event: '\uf0e7',
    Observable: '\uf140',
    EntityRelation: '\uf0c1',
    PiRogueExperiment: '\uf0c3',
    Threat: '\uf188',
    DataFragment: '\uf121',
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
    DataFragment: '#bc80bd',
    # #bc80bd #ccebc5 #ffed6f
}
