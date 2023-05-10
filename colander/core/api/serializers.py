import magic
import pathlib

from rest_framework import serializers
from django.db import transaction

from rest_framework.reverse import reverse_lazy, reverse

from colander.core.models import Artifact, ArtifactType, Case, Device, DeviceType, UploadRequest, PiRogueExperiment
from colander.core.signals import process_hash_and_signing


class ArtifactTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtifactType
        fields = ['id', 'name', 'short_name']


class CaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ['id', 'created_at', 'updated_at', 'name', 'description']


class DeviceSerializer(serializers.ModelSerializer):
    type_name = serializers.SerializerMethodField()

    class Meta:
        model = Device
        exclude = [
            'owner',
        ]

    def get_type_name(self, obj):
        return obj.type.short_name


class DeviceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceType
        fields = ['id', 'name', 'short_name']


class ArtifactSerializer(serializers.ModelSerializer):
    type_name = serializers.SerializerMethodField()
    upload_request_ref = serializers.CharField(
        write_only=True, required=False, help_text="For creation only. A valid Upload Request id must be provided"
    )

    class Meta:
        model = Artifact
        exclude = [
            'detached_signature',
            'file',
            'owner',
            'storage_name',
            'storage_location',
            'stored_name',
        ]
        read_only_fields = [
            'created_at',
            'updated_at',
            'extension',
            'original_name',
            'mime_type',
            'md5',
            'sha1',
            'sha256',
            'size_in_bytes',
        ]

    def get_type_name(self, obj):
        return obj.type.short_name

    def create(self, validated_data):
        if 'upload_request_ref' not in validated_data:
            raise Exception("create: Upload Request Ref not provided")

        uprr = validated_data.pop('upload_request_ref')

        upr = UploadRequest.objects.get(pk=uprr)

        if uprr is None:
            raise Exception(f"create: the given UploadRequest reference does not exists: {uprr}")

        artifact = super().create(validated_data)

        file_name = upr.name

        mime_type = magic.from_file(upr.path, mime=True)

        # TODO: To clean
        # delegate to an 'async'ish task
        # with open(upr.path, 'rb') as f:
        #   sha256, sha1, md5, size = hash_file(f)

        extension = pathlib.Path(file_name).suffix

        # TODO: To clean
        # delegate to an 'async'ish task
        # artifact.file = File(file=open(upr.path, 'rb'), name=file_name)
        # artifact.sha256 = sha256
        # artifact.sha1 = sha1
        # artifact.md5 = md5
        artifact.size_in_bytes = upr.size

        artifact.extension = extension
        artifact.mime_type = mime_type
        artifact.name = file_name
        artifact.original_name = file_name
        artifact.case = validated_data['case']
        artifact.save()

        upr.target_artifact_id = str(artifact.id)
        upr.save()

        transaction.on_commit(
            lambda: process_hash_and_signing.send(sender=self.__class__, upload_request_id=str(upr.id)))

        return artifact


class PiRogueExperimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PiRogueExperiment
        # fields = '__all__'
        exclude = [
            'owner',
        ]
