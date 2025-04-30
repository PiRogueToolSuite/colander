from rest_framework import serializers

from colander.core.models import Entity, EntityRelation, colander_models, SubGraph
from colander.core.rest.commons import CommonTypeSerializer, KeyedListSerializer


class EntityRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityRelation
        fields = ['id', 'name', 'obj_from', 'obj_to']


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

    class Meta:
        model = Entity
        fields = [
            'id', 'tlp', 'pap', 'created_at', 'updated_at', 'source_url', 'description',
            'absolute_url', 'content', 'mime_type', 'name', 'super_type', 'type',
            'thumbnail', 'thumbnail_url', 'thumbnail_delete',
        ]
        read_only_fields = [
            'absolute_url', 'created_at', 'mime_type', 'updated_at', 'thumbnail_url',
        ]
        write_only_fields = [
            'thumbnail', 'thumbnail_delete',
        ]
        list_serializer_class = KeyedListSerializer
        keyed_list_serializer_field = 'id'

    def create(self, validated_data):
        print('create', validated_data)
        model = colander_models.get(validated_data['super_type'])
        validated_data.pop('super_type')

        type_model = model.type.field.related_model
        type = type_model.objects.get(short_name=validated_data['type'])
        validated_data['type'] = type

        instance = model(**validated_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        print('update', validated_data)

        if 'thumbnail_delete' in validated_data:
            validated_data.pop('thumbnail_delete')
            if 'thumbnail' in validated_data:
                validated_data.pop('thumbnail')
            instance.thumbnail.delete()

        model = colander_models.get(validated_data['super_type'])
        validated_data.pop('super_type')

        if hasattr( instance, 'type'):
            type_model = model.type.field.related_model
            type = type_model.objects.get(short_name=validated_data['type'])
            validated_data['type'] = type

        return super().update(instance, validated_data)


class SubGraphSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubGraph
        fields = ['id', 'case', 'name', 'description', 'absolute_url', 'overrides']

