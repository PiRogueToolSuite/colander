from rest_framework import serializers

from colander.core.models import EntityRelation


class EntityRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityRelation
        fields = ['id', 'name', 'obj_from', 'obj_to']
