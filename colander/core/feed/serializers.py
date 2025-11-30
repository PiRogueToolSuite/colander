from colander_data_converter.base.models import Entity as cdc_Entity
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from colander.core.models import *


class BaseEntitySuperTypeSerializer(serializers.Serializer):
    name = serializers.CharField()
    short_name = serializers.CharField()


class BaseEntityTypeSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    name = serializers.CharField()
    short_name = serializers.CharField()
    description = serializers.CharField()


class ActorTypeSerializer(BaseEntityTypeSerializer):
    def to_internal_value(self, data):
        if isinstance(data, ActorType):
            return data
        return ActorType.objects.get(short_name__iexact=data.get('short_name', 'GENERIC'))


class ArtifactTypeSerializer(BaseEntityTypeSerializer):
    def to_internal_value(self, data):
        if isinstance(data, ArtifactType):
            return data
        return ArtifactType.objects.get(short_name__iexact=data.get('short_name', 'GENERIC'))


class DataFragmentTypeSerializer(BaseEntityTypeSerializer):
    def to_internal_value(self, data):
        if isinstance(data, DataFragmentType):
            return data
        return DataFragmentType.objects.get(short_name__iexact=data.get('short_name', 'GENERIC'))


class DetectionRuleTypeSerializer(BaseEntityTypeSerializer):
    def to_internal_value(self, data):
        if isinstance(data, DetectionRuleType):
            return data
        return DetectionRuleType.objects.get(short_name__iexact=data.get('short_name', 'GENERIC'))


class DeviceTypeSerializer(BaseEntityTypeSerializer):
    def to_internal_value(self, data):
        if isinstance(data, DeviceType):
            return data
        return DeviceType.objects.get(short_name__iexact=data.get('short_name', 'GENERIC'))


class EventTypeSerializer(BaseEntityTypeSerializer):
    def to_internal_value(self, data):
        if isinstance(data, EventType):
            return data
        return EventType.objects.get(short_name__iexact=data.get('short_name', 'GENERIC'))


class ObservableTypeSerializer(BaseEntityTypeSerializer):
    def to_internal_value(self, data):
        if isinstance(data, ObservableType):
            return data
        return ObservableType.objects.get(short_name__iexact=data.get('short_name', 'GENERIC'))


class ThreatTypeSerializer(BaseEntityTypeSerializer):
    def to_internal_value(self, data):
        if isinstance(data, ThreatType):
            return data
        return ThreatType.objects.get(short_name__iexact=data.get('short_name', 'GENERIC'))


class BaseEntitySerializer(serializers.Serializer):
    colander_internal_type = serializers.SerializerMethodField()
    id = serializers.UUIDField()
    super_type = serializers.SerializerMethodField()
    name = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    source_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    tlp = serializers.CharField()
    pap = serializers.CharField()

    common_attributes = [
        'id',
        'name',
        'case',
        'owner',
        'type',
        'description',
        'created_at',
        'updated_at',
        'tlp',
        'pap',
    ]
    excluded_fields = ['owner']
    write_only = ['owner']

    def __init__(self, *args, **kwargs):
        self.updating = "instance" in kwargs and "data" in kwargs
        super().__init__(*args, **kwargs)

    def prepare(self, validated_data):
        validated_data['case'] = self.context.get('case')
        validated_data['owner'] = self.context.get('case').owner
        validated_data.setdefault('tlp', self.context.get('case').tlp)
        validated_data.setdefault('pap', self.context.get('case').pap)

    def update(self, instance, validated_data):
        self.prepare(validated_data)
        for k, v in validated_data.items():
            if hasattr(instance, k):
                if isinstance(v, list):  # ManyToMany relationship
                    attr = getattr(instance, k)
                    for item in v:
                        attr.add(item)
                else:
                    setattr(instance, k, v)
        instance.save()
        return instance

    def get_colander_internal_type(self, obj):
        return self.get_super_type(obj).get('name', '').lower()

    @staticmethod
    def get_super_type(_):
        return {'name': 'undefined', 'short_name': 'UNDEFINED'}


class CaseSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    class Meta:
        model = Case
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields + [
            'es_prefix',
            'overrides',
            'signing_key',
            'parent_case',
            'teams',
        ]

    def create(self, validated_data):
        return Case.objects.get(id=validated_data)

    @staticmethod
    def get_super_type(_):
        return {'name': 'case', 'short_name': 'CASE'}


class EntityRelationSerializer(serializers.ModelSerializer):
    super_type = serializers.SerializerMethodField()
    colander_internal_type = serializers.SerializerMethodField()

    class Meta:
        model = EntityRelation
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields + [
            'obj_from_type',
            'obj_to_type'
        ]

    def get_colander_internal_type(self, obj):
        return self.get_super_type(obj).get('name', '').lower()

    @staticmethod
    def get_super_type(_):
        return {'name': 'entityrelation', 'short_name': 'ENTITYRELATION'}

    def create(self, validated_data):
        obj_from = Entity.objects.get(case=self.context.get('case'), pk=validated_data['obj_from_id'])
        obj_to = Entity.objects.get(case=self.context.get('case'), pk=validated_data['obj_to_id'])
        validated_data['case'] = self.context.get('case')
        validated_data['owner'] = self.context.get('case').owner
        validated_data['obj_from'] = obj_from.concrete()
        validated_data['obj_to'] = obj_to.concrete()
        return EntityRelation.objects.create(
            **{k: v for k, v in validated_data.items() if v}
        )


class ActorSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    type = ActorTypeSerializer()
    creation_fields = BaseEntitySerializer.common_attributes

    class Meta:
        model = Actor
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields + ['thumbnail']

    def create(self, validated_data):
        self.prepare(validated_data)
        return Actor.objects.create(
            **{k: v for k, v in validated_data.items() if k in self.creation_fields and v}
        )

    @staticmethod
    def get_super_type(_):
        return {'name': 'actor', 'short_name': 'ACTOR'}


class DeviceSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    type = DeviceTypeSerializer()
    creation_fields = BaseEntitySerializer.common_attributes

    class Meta:
        model = Device
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields + ['thumbnail']

    def create(self, validated_data):
        self.prepare(validated_data)
        return Device.objects.create(
            **{k: v for k, v in validated_data.items() if k in self.creation_fields and v}
        )

    def to_internal_value(self, data):
        if not self.updating:
            data.pop('operated_by') if 'operated_by' in data else None
        return super().to_internal_value(data)

    @staticmethod
    def get_super_type(_):
        return {'name': 'device', 'short_name': 'DEVICE'}


class ThreatSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    type = ThreatTypeSerializer()
    creation_fields = BaseEntitySerializer.common_attributes

    class Meta:
        model = Threat
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields + ['thumbnail']

    def create(self, validated_data):
        self.prepare(validated_data)
        return Threat.objects.create(
            **{k: v for k, v in validated_data.items() if k in self.creation_fields and v}
        )

    @staticmethod
    def get_super_type(_):
        return {'name': 'threat', 'short_name': 'THREAT'}


class ArtifactSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    type = ArtifactTypeSerializer()
    creation_fields = BaseEntitySerializer.common_attributes + [
        'md5', 'sha1', 'sha256', 'mime_type', 'extension', 'original_name', 'size_in_bytes', 'attributes'
    ]

    class Meta:
        model = Artifact
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields + [
            'stored_name',
            'storage_name',
            'storage_location',
            'analysis_index',
            'thumbnail',
            'file'
        ]

    def create(self, validated_data):
        self.prepare(validated_data)
        artifact = Artifact.objects.create(
            **{k: v for k, v in validated_data.items() if k in self.creation_fields and v}
        )
        artifact.file = ContentFile(b'', artifact.name)
        artifact.save()
        return artifact

    def to_internal_value(self, data):
        if not self.updating:
            data.pop('extracted_from') if 'extracted_from' in data else None
        return super().to_internal_value(data)

    @staticmethod
    def get_super_type(_):
        return {'name': 'artifact', 'short_name': 'ARTIFACT'}


class ObservableSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    type = ObservableTypeSerializer()
    creation_fields = BaseEntitySerializer.common_attributes

    class Meta:
        model = Observable
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields + [
            'raw_value',
            'es_prefix',
            'analysis_index',
            'thumbnail',
        ]

    def create(self, validated_data):
        self.prepare(validated_data)
        return Observable.objects.create(
            **{k: v for k, v in validated_data.items() if k in self.creation_fields and v}
        )

    def to_internal_value(self, data):
        if not self.updating:
            data.pop('extracted_from') if 'extracted_from' in data else None
            data.pop('associated_threat') if 'associated_threat' in data else None
            data.pop('operated_by') if 'operated_by' in data else None
        return super().to_internal_value(data)

    @staticmethod
    def get_super_type(_):
        return {'name': 'observable', 'short_name': 'OBSERVABLE'}


class DataFragmentSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    type = DataFragmentTypeSerializer()
    creation_fields = BaseEntitySerializer.common_attributes + [
        'content'
    ]

    class Meta:
        model = DataFragment
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields + ['thumbnail']

    def create(self, validated_data):
        self.prepare(validated_data)
        return DataFragment.objects.create(
            **{k: v for k, v in validated_data.items() if k in self.creation_fields and v}
        )

    def to_internal_value(self, data):
        if not self.updating:
            data.pop('extracted_from') if 'extracted_from' in data else None
        return super().to_internal_value(data)

    @staticmethod
    def get_super_type(_):
        return {'name': 'datafragment', 'short_name': 'DATAFRAGMENT'}


class DetectionRuleSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    type = DetectionRuleTypeSerializer()
    creation_fields = BaseEntitySerializer.common_attributes + [
        'content'
    ]

    class Meta:
        model = DetectionRule
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields + ['thumbnail']

    def create(self, validated_data):
        self.prepare(validated_data)
        return DetectionRule.objects.create(
            **{k: v for k, v in validated_data.items() if k in self.creation_fields and v}
        )

    def to_internal_value(self, data):
        if not self.updating:
            data.pop('targeted_observables') if 'targeted_observables' in data else None
        return super().to_internal_value(data)

    @staticmethod
    def get_super_type(_):
        return {'name': 'detectionrule', 'short_name': 'DETECTIONRULE'}


class EventSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    # Not fully supported yet, waiting for a new release of MISP
    type = EventTypeSerializer()
    creation_fields = BaseEntitySerializer.common_attributes + [
        'first_seen', 'last_seen', 'count'
    ]

    class Meta:
        model = Event
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields + ['thumbnail']

    def create(self, validated_data):
        self.prepare(validated_data)
        return Event.objects.create(
            **{k: v for k, v in validated_data.items() if k in self.creation_fields and v}
        )

    def to_internal_value(self, data):
        if not self.updating:
            data.pop('extracted_from') if 'extracted_from' in data else None
            data.pop('observed_on') if 'observed_on' in data else None
            data.pop('detected_by') if 'detected_by' in data else None
            data.pop('attributed_to') if 'attributed_to' in data else None
            data.pop('target') if 'target' in data else None
            data.pop('involved_observables') if 'involved_observables' in data else None
        return super().to_internal_value(data)

    @staticmethod
    def get_super_type(_):
        return {'name': 'event', 'short_name': 'EVENT'}


class OutgoingFeedInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutgoingFeed
        fields = [
            'name',
            'description',
            'created_at',
            'updated_at',
            'max_tlp',
            'max_pap',
        ]


class PolymorphicSerializer(serializers.Serializer):
    """
    A polymorphic serializer that handles serialization and deserialization
    of multiple object types with different serializers.

    This serializer supports two output modes:
    - 'list': Returns a list of serialized objects (default)
    - 'dict': Returns a dictionary with object IDs as keys and serialized objects as values

    Attributes:
        serializer_mapping (dict): Mapping of model classes to their respective serializers
        output_mode (str): Either 'list' or 'dict' to control format
    """

    # Mapping from model classes to their respective serializer classes
    serializer_mapping = {
        Case: CaseSerializer,
        EntityRelation: EntityRelationSerializer,
        Actor: ActorSerializer,
        Artifact: ArtifactSerializer,
        DataFragment: DataFragmentSerializer,
        DetectionRule: DetectionRuleSerializer,
        Device: DeviceSerializer,
        Event: EventSerializer,
        Observable: ObservableSerializer,
        Threat: ThreatSerializer,
    }
    serializer_mapping_str = {
        'case': CaseSerializer,
        'entityrelation': EntityRelationSerializer,
        'actor': ActorSerializer,
        'artifact': ArtifactSerializer,
        'datafragment': DataFragmentSerializer,
        'detectionrule': DetectionRuleSerializer,
        'device': DeviceSerializer,
        'event': EventSerializer,
        'observable': ObservableSerializer,
        'threat': ThreatSerializer,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        # Get the specific serializer class for this instance
        serializer_class = self.serializer_mapping.get(type(instance))

        if serializer_class:
            # If a serializer is found, use it to serialize the object
            serializer = serializer_class(instance, context=self.context)
            data = serializer.data
            return data
        else:
            raise ValidationError('Serializer not supported')

    @classmethod
    def get_serializer_by_model(cls, model):
        return cls.serializer_mapping.get(type(model))

    @classmethod
    def get_serializer_from_data(cls, data):
        serializer_class = None
        if isinstance(data, dict):
            colander_internal_type = data.get('colander_internal_type', None)
            super_type_name = colander_internal_type or data.get('super_type', {}).get('short_name', '').lower()
            serializer_class = cls.serializer_mapping_str.get(super_type_name, None)
        elif isinstance(data, cdc_Entity):
            colander_internal_type = data.colander_internal_type or None
            super_type_name = colander_internal_type or data.super_type.short_name.lower()
            serializer_class = cls.serializer_mapping_str.get(super_type_name, None)
        if not serializer_class:
            raise ValidationError(f'Super type for "{data}" not supported')
        return serializer_class


class EntityFeedContentSerializer(serializers.ModelSerializer):
    entities = serializers.SerializerMethodField()
    relations = serializers.SerializerMethodField()
    cases = serializers.SerializerMethodField()

    class Meta:
        model = EntityExportFeed
        fields = [
            'name',
            'description',
            'created_at',
            'updated_at',
            'max_tlp',
            'max_pap',
            'entities',
            'relations',
            'cases',
        ]

    def get_entities(self, obj):
        _entities = {}
        for entity in obj.entities:
            s = PolymorphicSerializer(entity)
            _entities[str(entity.id)] = s.data
        return _entities

    def get_relations(self, obj):
        _relations = {}
        for entity in obj.relations:
            s = PolymorphicSerializer(entity)
            _relations[str(entity.id)] = s.data
        return _relations

    def get_cases(self, obj):
        return {
            str(obj.case.id): PolymorphicSerializer(obj.case).data
        }
