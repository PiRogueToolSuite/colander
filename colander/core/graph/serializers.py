from typing import Any

from rest_framework import serializers

from colander.core.models import Case, Entity, Actor, EntityRelation


class KeyedListSerializer(serializers.ListSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        meta = getattr(self.child, 'Meta', None)
        assert hasattr(meta, 'keyed_list_serializer_field'), \
            "Must provide a field name at keyed_list_serializer_field when using KeyedListSerializer"
        self._keyed_field = meta.keyed_list_serializer_field

    def to_internal_value(self, data):
        data = [{**v, **{self._keyed_field: k}} for k, v in data.items()]
        return super().to_internal_value(data)

    def to_representation(self, data):
        response = super().to_representation(data)
        return {v[self._keyed_field]: v for v in response}


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


class GraphEntitySerializer(serializers.ModelSerializer):
    # id = serializers.CharField()
    name = serializers.CharField(allow_null=True)
    absolute_url = serializers.CharField(allow_null=True)
    super_type = serializers.CharField(allow_null=True)
    type = serializers.CharField(allow_null=True)
    # tlp = serializers.CharField(allow_null=True)
    # pap = serializers.CharField(allow_null=True)
    # type = serializers.CharField()

    class Meta:
        model = Entity
        fields = ['id', 'super_type', 'type', 'name', 'tlp', 'pap', 'absolute_url']
        list_serializer_class = KeyedListSerializer
        keyed_list_serializer_field = 'id'


class GraphCaseSerializer(serializers.ModelSerializer):
    entities = GraphEntitySerializer(
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
