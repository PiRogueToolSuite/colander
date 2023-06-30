from rest_framework import serializers


class CommonTypeSerializer(serializers.CharField):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        # We pass the object instance onto `to_representation`,
        # not just the field attribute.
        return instance
    def to_representation(self, instance):
        if hasattr(instance, 'type'):
            return instance.type.short_name
        return None


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
