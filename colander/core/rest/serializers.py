from rest_framework import serializers

import colander.core.templatetags.colander_tags
from colander.core.models import colander_models, Entity, EntityRelation


class EntityRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityRelation
        fields = ['id', 'name', 'obj_from', 'obj_to']


class DetailedEntitySerializer(serializers.ModelSerializer):

    absolute_url = serializers.CharField(allow_null=True, read_only=True)
    name = serializers.CharField(allow_null=True)
    super_type = serializers.CharField(allow_null=True)
    type = serializers.CharField(allow_null=True)
    content = serializers.CharField(allow_null=True, read_only=True)
    mime_type = serializers.CharField(allow_null=True, read_only=True)

    class Meta:
        model = Entity
        fields = [
            'id', 'tlp', 'pap', 'created_at', 'updated_at', 'source_url', 'description',
            'absolute_url', 'content', 'mime_type', 'name', 'super_type', 'type',
        ]
        read_only_fields = [
            'absolute_url', 'created_at', 'mime_type', 'updated_at',
        ]

    def create(self, validated_data):
        print("DetailedEntitySerializer create", validated_data)
        model = colander_models.get(validated_data['super_type'])
        validated_data.pop('super_type')

        type_model = model.type.field.related_model
        type = type_model.objects.get(short_name=validated_data['type'])
        validated_data['type'] = type

        instance = model(**validated_data)
        instance.save()
        return instance


