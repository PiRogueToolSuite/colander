from rest_framework import serializers
from rest_framework.reverse import reverse_lazy, reverse

from colander.core.models import Artifact, ArtifactType, Device, DeviceType, Case


class ArtifactTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtifactType
        fields = ['id', 'name', 'short_name']


class DeviceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceType
        fields = ['id', 'name', 'short_name']


class ArtifactUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artifact
        fields = [
            'file',
            'type',
            'description',
            'extracted_from',
        ]


class ArtifactUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True, allow_empty_file=False)
    type = serializers.ChoiceField(choices=[(t.id, t.short_name.lower()) for t in ArtifactType.objects.all()])

class ArtifactSerializer(serializers.ModelSerializer):
    type_name = serializers.SerializerMethodField()

    class Meta:
        model = Artifact
        exclude = [
            'stored_name',
            'storage_name',
            'storage_location',
            'detached_signature',
            'owner',
            'file'
        ]

    def get_type_name(self, obj):
        return obj.type.short_name

class DeviceSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.id')
    type_name = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = '__all__'

    def get_type_name(self, obj):
        return obj.type.short_name
