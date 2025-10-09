from rest_framework import serializers

from colander.core.models import *


class BaseEntitySuperTypeSerializer(serializers.Serializer):
    name = serializers.CharField()
    short_name = serializers.CharField()


class BaseEntityTypeSerializer(serializers.Serializer):
    name = serializers.CharField()
    short_name = serializers.CharField()
    description = serializers.CharField()


class ActorTypeSerializer(BaseEntityTypeSerializer):
    def to_internal_value(self, data):
        return ActorType.objects.get(short_name__iexact=data.get('short_name', 'GENERIC'))


class ArtifactTypeSerializer(BaseEntityTypeSerializer):
    def to_internal_value(self, data):
        return ArtifactType.objects.get(short_name__iexact=data.get('short_name', 'GENERIC'))


class DataFragmentTypeSerializer(BaseEntityTypeSerializer):
    def to_internal_value(self, data):
        return DataFragmentType.objects.get(short_name__iexact=data.get('short_name', 'GENERIC'))


class DetectionRuleTypeSerializer(BaseEntityTypeSerializer):
    def to_internal_value(self, data):
        return DetectionRuleType.objects.get(short_name__iexact=data.get('short_name', 'GENERIC'))


class DeviceTypeSerializer(BaseEntityTypeSerializer):
    def to_internal_value(self, data):
        return DeviceType.objects.get(short_name__iexact=data.get('short_name', 'GENERIC'))


class EventTypeSerializer(BaseEntityTypeSerializer):
    def to_internal_value(self, data):
        return EventType.objects.get(short_name__iexact=data.get('short_name', 'GENERIC'))


class ObservableTypeSerializer(BaseEntityTypeSerializer):
    def to_internal_value(self, data):
        return ObservableType.objects.get(short_name__iexact=data.get('short_name', 'GENERIC'))


class ThreatTypeSerializer(BaseEntityTypeSerializer):
    def to_internal_value(self, data):
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

    excluded_fields = ['owner']
    write_only = ['owner']

    def get_colander_internal_type(self, obj):
        return self.get_super_type(obj).get('name', '').lower()

    def get_super_type(self, obj):
        return {'name': 'actor', 'short_name': 'ACTOR'}


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

    def get_super_type(self, obj):
        return {'name': 'case', 'short_name': 'CASE'}


class EntityRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityRelation
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields + [
            'obj_from_type',
            'obj_to_type'
        ]


class ActorSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    type = ActorTypeSerializer()

    class Meta:
        model = Actor
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields

    def get_super_type(self, obj):
        return {'name': 'actor', 'short_name': 'ACTOR'}


class ArtifactSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    type = ArtifactTypeSerializer()

    class Meta:
        model = Artifact
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields + [
            'stored_name',
            'storage_name',
            'storage_location',
            'analysis_index',
            'file'
        ]

    def get_super_type(self, obj):
        return {'name': 'artifact', 'short_name': 'ARTIFACT'}


class DataFragmentSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    type = DataFragmentTypeSerializer()

    class Meta:
        model = DataFragment
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields

    def get_super_type(self, obj):
        return {'name': 'datafragment', 'short_name': 'DATAFRAGMENT'}


class DetectionRuleSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    type = DetectionRuleTypeSerializer()

    class Meta:
        model = DetectionRule
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields

    def get_super_type(self, obj):
        return {'name': 'detectionrule', 'short_name': 'DETECTIONRULE'}


class DeviceSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    type = DeviceTypeSerializer()

    class Meta:
        model = Device
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields

    def get_super_type(self, obj):
        return {'name': 'device', 'short_name': 'DEVICE'}


class EventSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    type = EventTypeSerializer()

    class Meta:
        model = Event
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields

    def get_super_type(self, obj):
        return {'name': 'event', 'short_name': 'EVENT'}


class ObservableSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    type = ObservableTypeSerializer()

    class Meta:
        model = Observable
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields + [
            'raw_value',
            'es_prefix',
            'analysis_index',
        ]

    def get_super_type(self, obj):
        return {'name': 'observable', 'short_name': 'OBSERVABLE'}


class ThreatSerializer(BaseEntitySerializer, serializers.ModelSerializer):
    type = ThreatTypeSerializer()

    class Meta:
        model = Threat
        write_only = BaseEntitySerializer.write_only
        exclude = BaseEntitySerializer.excluded_fields

    def get_super_type(self, obj):
        return {'name': 'threat', 'short_name': 'THREAT'}


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

    def __init__(self, *args, **kwargs):
        # Set output_mode to 'list' or 'dict', default to 'dict'
        self.output_mode = kwargs.pop('output_mode', 'dict')
        super().__init__(*args, **kwargs)

    def _to_representation(self, instance):
        """
        Override the serialization method.
        `instance` can be a single object or an object within a list.
        """
        # Get the specific serializer class for this instance
        serializer_class = self.serializer_mapping.get(type(instance))

        if serializer_class:
            # If a serializer is found, use it to serialize the object
            serializer = serializer_class(instance, context=self.context)
            data = serializer.data
            return data
        else:
            return super().to_representation(instance)

    def to_representation(self, instances):
        """
        Handle serialization for multiple instances based on output_mode.
        """
        if not isinstance(instances, list):
            return self._to_representation(instances)
        if self.output_mode == 'dict':
            # Dictionary mode: keys are IDs, values are serialized objects
            return {
                str(instance.id): self._to_representation(instance)
                for instance in instances
            }
        else:
            # List mode: default behavior
            return [self._to_representation(instance) for instance in instances]


class FullOutgoingFeedSerializer(serializers.ModelSerializer):
    entities = PolymorphicSerializer()
    relations = PolymorphicSerializer()
    cases = PolymorphicSerializer()

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
            'cases'
        ]
