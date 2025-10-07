from rest_framework import serializers

from colander.core.models import Actor, Artifact, Device, EntityRelation, Event, Observable, Threat, Case


class EntitySerializer(serializers.Serializer):
    super_type = serializers.SerializerMethodField()
    colander_internal_type = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    type_name = serializers.SerializerMethodField()
    sha256 = serializers.SerializerMethodField()
    id = serializers.UUIDField()
    value = serializers.CharField()
    description = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    source_url = serializers.URLField()
    tlp = serializers.CharField()
    pap = serializers.CharField()

    def get_colander_internal_type(self, obj):
        return 'actor'

    def get_super_type(self, obj):
        return obj.super_type

    def get_type(self, obj):
        return obj.type.short_name

    def get_type_name(self, obj):
        return obj.type.name

    def get_sha256(self, obj):
        if hasattr(obj, 'sha256'):
            return obj.sha256
        else:
            return ''


class EntityTypeSerializer(serializers.Serializer):
    name = serializers.CharField()
    short_name = serializers.CharField()
    description = serializers.CharField()
    nf_icon = serializers.CharField()


class CaseSerializer(serializers.ModelSerializer):
    colander_internal_type = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = ['id', 'name', 'description', 'tlp', 'pap', 'created_at', 'updated_at', 'colander_internal_type']

    def get_colander_internal_type(self, obj):
        return 'case'


class ArtifactSerializer(serializers.ModelSerializer):
    super_type = serializers.SerializerMethodField()
    colander_internal_type = serializers.SerializerMethodField()
    type = EntityTypeSerializer()

    class Meta:
        model = Artifact
        exclude = [
            'stored_name',
            'storage_name',
            'storage_location',
            'analysis_index',
            'owner',
            'file'
        ]

    def get_colander_internal_type(self, obj):
        return 'artifact'

    def get_super_type(self, obj):
        return {'name': 'artifact', 'short_name': 'ARTIFACT'}


class ActorSerializer(serializers.ModelSerializer):
    super_type = serializers.SerializerMethodField()
    colander_internal_type = serializers.SerializerMethodField()
    type = EntityTypeSerializer()

    class Meta:
        model = Actor
        exclude = ['owner']

    def get_colander_internal_type(self, obj):
        return 'actor'

    def get_super_type(self, obj):
        return {'name': 'actor', 'short_name': 'ACTOR'}


class EventSerializer(serializers.ModelSerializer):
    super_type = serializers.SerializerMethodField()
    colander_internal_type = serializers.SerializerMethodField()
    type = EntityTypeSerializer()

    class Meta:
        model = Event
        exclude = ['owner']

    def get_colander_internal_type(self, obj):
        return 'event'

    def get_super_type(self, obj):
        return {'name': 'event', 'short_name': 'EVENT'}


class DeviceSerializer(serializers.ModelSerializer):
    super_type = serializers.SerializerMethodField()
    colander_internal_type = serializers.SerializerMethodField()
    type = EntityTypeSerializer()

    class Meta:
        model = Device
        exclude = ['owner']

    def get_colander_internal_type(self, obj):
        return 'device'

    def get_super_type(self, obj):
        return {'name': 'device', 'short_name': 'DEVICE'}


class ThreatSerializer(serializers.ModelSerializer):
    super_type = serializers.SerializerMethodField()
    colander_internal_type = serializers.SerializerMethodField()
    type = EntityTypeSerializer()

    class Meta:
        model = Threat
        exclude = ['owner']

    def get_colander_internal_type(self, obj):
        return 'threat'

    def get_super_type(self, obj):
        return {'name': 'threat', 'short_name': 'THREAT'}


class ObservableSerializer(serializers.ModelSerializer):
    super_type = serializers.SerializerMethodField()
    colander_internal_type = serializers.SerializerMethodField()
    type = EntityTypeSerializer()

    class Meta:
        model = Observable
        exclude = ['owner',  'es_prefix', 'analysis_index', 'raw_value']

    def get_colander_internal_type(self, obj):
        return 'observable'

    def get_super_type(self, obj):
        return {'name': 'observable', 'short_name': 'OBSERVABLE'}


class EntityRelationSerializer(serializers.ModelSerializer):
    colander_internal_type = serializers.SerializerMethodField()

    class Meta:
        model = EntityRelation
        exclude = ['owner', 'obj_from_type', 'obj_to_type']

    def get_colander_internal_type(self, obj):
        return 'relation'

    def get_super_type(self, obj):
        return {'name': 'entity_relation', 'short_name': 'ENTITY_RELATION'}


class OutgoingFeedSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    max_tlp = serializers.CharField()
    max_pap = serializers.CharField()
