import json

from django.db import transaction
from django.db.migrations.serializer import UUIDSerializer
from requests.structures import CaseInsensitiveDict
from rest_framework.fields import SerializerMethodField, CharField
from rest_framework.serializers import ModelSerializer, Serializer

from colander.core.models import Case, Actor, Artifact, DataFragment, DetectionRule, Device, Event, \
    PiRogueExperiment, Observable, Threat, SubGraph, EntityRelation, ActorType, Entity, \
    ArtifactType, DataFragmentType, DetectionRuleType, DeviceType, EventType, ObservableType, \
    ThreatType
from colander.core.signals import process_hash_and_signing


class EntityTypeSerializer(Serializer):
    name = CharField()
    short_name = CharField()
    description = CharField()
    icon = CharField()

    def __init__(self, super_type_class, **kwargs):
        self.super_type_class = super_type_class
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if isinstance(data, self.super_type_class):
            return data
        return self.super_type_class.objects.get(short_name__iexact=data.get('short_name', 'GENERIC'))


class CaseSerializer(ModelSerializer):
    class Meta:
        model = Case
        exclude = ['owner', 'es_prefix', 'parent_case', 'teams']


class ActorSerializer(ModelSerializer):
    super_type = SerializerMethodField()
    type = EntityTypeSerializer(ActorType)

    class Meta:
        model = Actor
        exclude = ['owner']
        write_only = ['owner', 'case', 'thumbnail']
        extra_kwargs = {
            'case': {'write_only': True},
            'thumbnail': {'write_only': True},
        }

    def get_super_type(self, obj):
        return {'name': 'actor', 'short_name': 'ACTOR'}


class ArtifactSerializer(ModelSerializer):
    super_type = SerializerMethodField()
    type = EntityTypeSerializer(ArtifactType)
    upload_request_ref = CharField(required=False, write_only=True)

    class Meta:
        model = Artifact
        exclude = [
            'owner',
            'stored_name',
            'storage_name',
            'storage_location',
            'analysis_index',
        ]
        write_only = ['owner', 'case', 'file', 'thumbnail']
        extra_kwargs = {
            'case': {'write_only': True},
            'file': {'write_only': True},
            'thumbnail': {'write_only': True},
        }

    def get_super_type(self, obj):
        return {'name': 'artifact', 'short_name': 'ARTIFACT'}

    def update(self, instance, validated_data):
        if 'upload_request_ref' in validated_data:
            upload_request_ref = validated_data.pop('upload_request_ref')
            transaction.on_commit(
                lambda: process_hash_and_signing.send(sender=self.__class__, upload_request_id=upload_request_ref))

        instance = super().update(instance, validated_data)
        return instance


class DataFragmentSerializer(ModelSerializer):
    super_type = SerializerMethodField()
    type = EntityTypeSerializer(DataFragmentType)

    class Meta:
        model = DataFragment
        exclude = ['owner']
        write_only = ['owner', 'case', 'thumbnail']
        extra_kwargs = {
            'case': {'write_only': True},
            'thumbnail': {'write_only': True},
        }

    def get_super_type(self, obj):
        return {'name': 'data_fragment', 'short_name': 'DATA_FRAGMENT'}


class DetectionRuleSerializer(ModelSerializer):
    super_type = SerializerMethodField()
    type = EntityTypeSerializer(DetectionRuleType)

    class Meta:
        model = DetectionRule
        exclude = ['owner']
        write_only = ['owner', 'case', 'thumbnail']
        extra_kwargs = {
            'case': {'write_only': True},
            'thumbnail': {'write_only': True},
        }

    def get_super_type(self, obj):
        return {'name': 'detection_rule', 'short_name': 'DETECTION_RULE'}


class DeviceSerializer(ModelSerializer):
    super_type = SerializerMethodField()
    type = EntityTypeSerializer(DeviceType)

    class Meta:
        model = Device
        exclude = ['owner']
        write_only = ['owner', 'case', 'thumbnail']
        extra_kwargs = {
            'case': {'write_only': True},
            'thumbnail': {'write_only': True},
        }

    def get_super_type(self, obj):
        return {'name': 'device', 'short_name': 'DEVICE'}

class EventSerializer(ModelSerializer):
    super_type = SerializerMethodField()
    type = EntityTypeSerializer(EventType)

    class Meta:
        model = Event
        exclude = ['owner']
        write_only = ['owner', 'case', 'thumbnail']
        extra_kwargs = {
            'case': {'write_only': True},
            'thumbnail': {'write_only': True},
        }

    def get_super_type(self, obj):
        return {'name': 'event', 'short_name': 'EVENT'}


class ObservableSerializer(ModelSerializer):
    super_type = SerializerMethodField()
    type = EntityTypeSerializer(ObservableType)

    class Meta:
        model = Observable
        exclude = ['owner', 'es_prefix', 'analysis_index', 'raw_value']
        write_only = ['owner', 'case', 'thumbnail']
        extra_kwargs = {
            'case': {'write_only': True},
            'thumbnail': {'write_only': True},
        }

    def get_super_type(self, obj):
        return {'name': 'observable', 'short_name': 'OBSERVABLE'}


class PiRogueExperimentSerializer(ModelSerializer):
    super_type = SerializerMethodField()

    class Meta:
        model = PiRogueExperiment
        exclude = ['owner']
        write_only = ['owner', 'case', 'thumbnail']
        extra_kwargs = {
            'case': {'write_only': True},
            'thumbnail': {'write_only': True},
        }

    def get_super_type(self, obj):
        return {'name': 'pirogue_experiment', 'short_name': 'PIROGUE_EXPERIMENT'}


class SubGraphSerializer(ModelSerializer):
    class Meta:
        model = SubGraph
        exclude = ['owner']
        write_only = ['owner', 'case', 'thumbnail']
        extra_kwargs = {
            'case': {'write_only': True},
            'thumbnail': {'write_only': True},
        }


class ThreatSerializer(ModelSerializer):
    super_type = SerializerMethodField()
    type = EntityTypeSerializer(ThreatType)

    class Meta:
        model = Threat
        exclude = ['owner']
        write_only = ['owner', 'case', 'thumbnail']
        extra_kwargs = {
            'case': {'write_only': True},
            'thumbnail': {'write_only': True},
        }

    def get_super_type(self, obj):
        return {'name': 'threat', 'short_name': 'THREAT'}


class EntityRelationSerializer(ModelSerializer):
    class Meta:
        model = EntityRelation
        exclude = ['owner', 'obj_from_type', 'obj_to_type']
        extra_kwargs = {
            'case': {'write_only': True},
        }

    def create(self, validated_data):
        abstract_from = Entity.objects.get(case=validated_data['case'], pk=validated_data['obj_from_id'])
        abstract_to = Entity.objects.get(case=validated_data['case'], pk=validated_data['obj_to_id'])

        concrete_from = abstract_from.concrete()
        concrete_to = abstract_to.concrete()

        validated_data['obj_from'] = concrete_from
        validated_data['obj_to'] = concrete_to

        return super().create(validated_data)

    def get_super_type(self, obj):
        return {'name': 'entity_relation', 'short_name': 'ENTITY_RELATION'}



serializers_by_model = {
    # Case main type
    Case: CaseSerializer,
    # 'Entity' types
    Actor: ActorSerializer,
    Artifact: ArtifactSerializer,
    DataFragment: DataFragmentSerializer,
    DetectionRule: DetectionRuleSerializer,
    Device: DeviceSerializer,
    EntityRelation: EntityRelationSerializer,
    Event: EventSerializer,
    PiRogueExperiment: PiRogueExperimentSerializer,
    Observable: ObservableSerializer,
    Threat: ThreatSerializer,
    # # Extra non 'Entity' type
    SubGraph: SubGraphSerializer,
}

model_by_super_types_str = CaseInsensitiveDict({
    # Case main type
    'Case': Case,
    # 'Entity' types
    'Actor': Actor,
    'Artifact': Artifact,
    'DataFragment': DataFragment,
    'DetectionRule': DetectionRule,
    'Device': Device,
    'EntityRelation': EntityRelation,
    'Event': Event,
    'PiRogueExperiment': PiRogueExperiment,
    'Observable': Observable,
    'Threat': Threat,
    # Extra non 'Entity' type
    'SubGraph': SubGraph,
})
