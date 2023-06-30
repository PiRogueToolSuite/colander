from typing import Any

from rest_framework import serializers

from colander.core.models import Case, Entity, EntityRelation
from colander.core.rest.commons import KeyedListSerializer
from colander.core.rest.serializers import DetailedEntitySerializer


class GraphRelationSerializer(serializers.ModelSerializer):

    # FIXME: Overload  serializers.PrimaryKeyRelatedField(queryset) to be user accessible entity only
    # class UserFilteredPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    #     def get_queryset(self):
    #         request = self.context.get('request', None)
    #         queryset = super(UserFilteredPrimaryKeyRelatedField, self).get_queryset()
    #         if not request or not queryset:
    #             return None
    #         return queryset.filter(user=request.user)
    obj_from = serializers.PrimaryKeyRelatedField(queryset=Entity.objects)
    obj_to = serializers.PrimaryKeyRelatedField(queryset=Entity.objects)

    class Meta:
        model = EntityRelation
        fields = ['id', 'name', 'obj_from', 'obj_to', 'immutable']
        read_only_fields = ['immutable']
        list_serializer_class = KeyedListSerializer
        keyed_list_serializer_field = 'id'


class GraphCaseSerializer(serializers.ModelSerializer):
    # entities = GraphEntitySerializer(
    #     many=True
    # )
    entities = DetailedEntitySerializer(
        many=True
    )
    relations = GraphRelationSerializer(
        many=True
    )

    class Meta:
        model = Case
        fields = ['name', 'entities', 'relations', 'overrides']

    def to_representation(self, data):
        response = super().to_representation(data)
        for ce in data.entities:
            for er in ce.relations:
                if str(er.id) in response['relations']:
                    continue
                response['relations'][str(er.id)] = GraphRelationSerializer().to_representation(instance=er)
        return response
