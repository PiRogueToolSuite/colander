from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from colander.core.models import NetworkDPI, NetworkAlert


class NetworkDPISerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkDPI
        fields = '__all__'


class NetworkAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkAlert
        fields = '__all__'


class NetworkEventSerializer(serializers.Serializer):
    serializer_mapping_str = {
        'network-alert': NetworkAlertSerializer,
        'network-dpi': NetworkDPISerializer,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def get_serializer_from_data(cls, data) -> type[NetworkAlertSerializer | NetworkDPISerializer]:
        serializer_class = None

        if data and isinstance(data, dict) and 'enrichment' in data:
            object_type = data['enrichment'].get('object_type', '')
            serializer_class = cls.serializer_mapping_str.get(object_type, None)

        if not serializer_class:
            raise ValidationError('Data type not supported')

        return serializer_class

    @classmethod
    def get_model_class(cls, data) -> type[NetworkAlert | NetworkDPI]:
        serializer = cls.get_serializer_from_data(data)
        return serializer.Meta.model
