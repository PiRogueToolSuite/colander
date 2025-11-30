from rest_framework import serializers
from rest_framework.fields import empty

from colander.core.models import Entity, EntityRelation, colander_models, SubGraph, FeedTemplate
from colander.core.rest.commons import CommonTypeSerializer, KeyedListSerializer
from colander.users.models import User


class EntityRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityRelation
        fields = ['id', 'name', 'obj_from', 'obj_to']


class FeedTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedTemplate
        fields = [
            'id',
            'name',
            'description',
            'content',
            'visibility',
            'in_error'
        ]


class DetailedEntitySerializer(serializers.ModelSerializer):

    absolute_url = serializers.CharField(allow_null=True, read_only=True)
    name = serializers.CharField(allow_null=True)
    super_type = serializers.CharField(allow_null=True)
    type = CommonTypeSerializer(allow_null=True, required=False)
    content = serializers.CharField(allow_null=True, required=False)
    mime_type = serializers.CharField(allow_null=True, read_only=True)
    thumbnail_url = serializers.CharField(allow_null=True, read_only=True)
    thumbnail = serializers.FileField(allow_null=True, write_only=True, required=False)
    thumbnail_delete = serializers.BooleanField(allow_null=True, write_only=True, required=False)
    attributes = serializers.JSONField(allow_null=True, required=False)

    class Meta:
        model = Entity
        fields = [
            'id', 'tlp', 'pap', 'created_at', 'updated_at', 'source_url', 'description',
            'absolute_url', 'content', 'mime_type', 'name', 'super_type', 'type',
            'thumbnail', 'thumbnail_url', 'thumbnail_delete', 'attributes'
        ]
        read_only_fields = [
            'absolute_url', 'created_at', 'mime_type', 'updated_at', 'thumbnail_url',
        ]
        write_only_fields = [
            'thumbnail', 'thumbnail_delete',
        ]
        list_serializer_class = KeyedListSerializer
        keyed_list_serializer_field = 'id'

    def __init__(self, instance=None, data=empty, **kwargs):
        self.entity_model = None
        self.entity_type = None
        super(DetailedEntitySerializer, self).__init__(instance=instance, data=data, **kwargs)

    def is_valid(self, *, raise_exception=False):
        super(DetailedEntitySerializer, self).is_valid(raise_exception=raise_exception)
        self.entity_model = colander_models.get(self.validated_data['super_type'])
        self.validated_data.pop('super_type')
        type_model = self.entity_model.type.field.related_model
        self.entity_type = type_model.objects.get(short_name=self.validated_data['type'])
        self.validated_data['type'] = self.entity_type

    def create(self, validated_data):
        instance = self.entity_model(**validated_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        if 'thumbnail_delete' in validated_data:
            validated_data.pop('thumbnail_delete')
            if 'thumbnail' in validated_data:
                validated_data.pop('thumbnail')
            instance.thumbnail.delete()

        if hasattr( instance, 'type'):
            validated_data['type'] = self.entity_type
        return super().update(instance, validated_data)


class SubGraphSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubGraph
        fields = ['id', 'case', 'name', 'description', 'absolute_url', 'overrides']


class UserSerializer(serializers.ModelSerializer):
    available_templates = FeedTemplateSerializer(many=True, read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'available_templates']
