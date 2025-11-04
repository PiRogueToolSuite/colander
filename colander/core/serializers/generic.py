from rest_framework import serializers


# noinspection PyMethodMayBeStatic
class EntitySerializer(serializers.Serializer):
    super_type = serializers.SerializerMethodField()
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
