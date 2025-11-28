import mimetypes
import pathlib

import magic
from django.db import transaction
from rest_framework import serializers
from rest_framework.serializers import Serializer

from colander.core.models import (
    Artifact,
    ArtifactType,
    Case,
    ColanderTeam,
    Device,
    DeviceType,
    DroppedFile,
    EntityRelation,
    Observable,
    ObservableType,
    PiRogueExperiment,
    UploadRequest, Entity,
)
from colander.core.signals import process_hash_and_signing
from colander.core.utils import get_upload_file_mime_type


class ArtifactTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtifactType
        fields = ['id', 'name', 'short_name', 'default_attributes']


class CaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ['id', 'created_at', 'updated_at', 'name', 'description', 'tlp', 'pap', 'teams']
        read_only_fields = ['created_at', 'updated_at']


class DeviceSerializer(serializers.ModelSerializer):
    type_name = serializers.SerializerMethodField()

    class Meta:
        model = Device
        exclude = [
            'owner',
        ]

    def get_type_name(self, obj):
        return obj.type.short_name

    def create(self, validated_data):
        d = super().create(validated_data)
        if 'tlp' not in validated_data:
            d.tlp = d.case.tlp
        if 'pap' not in validated_data:
            d.pap = d.case.pap
        d.save()
        return d


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
        if 'tlp' not in validated_data:
            artifact.tlp = artifact.case.tlp
        if 'pap' not in validated_data:
            artifact.pap = artifact.case.pap
        artifact.save()

        upr.target_entity_id = str(artifact.id)
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

    def create(self, validated_data):
        pre = super().create(validated_data)
        if 'tlp' not in validated_data:
            pre.tlp = pre.case.tlp
        if 'pap' not in validated_data:
            pre.pap = pre.case.pap
        pre.save()
        return pre


class ObservableSerializer(serializers.ModelSerializer):
    type_name = serializers.SerializerMethodField()

    class Meta:
        model = Observable
        exclude = [
            'owner',
            'raw_value',
            'analysis_index',
            'es_prefix',
        ]

    def get_type_name(self, obj):
        return obj.type.short_name

    def create(self, validated_data):
        d = super().create(validated_data)
        if 'tlp' not in validated_data:
            d.tlp = d.case.tlp
        if 'pap' not in validated_data:
            d.pap = d.case.pap
        d.save()
        return d


class ObservableTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObservableType
        fields = ['id', 'name', 'short_name']


class RelationSerializer(serializers.ModelSerializer):
    #obj_from = serializers.SerializerMethodField()
    obj_from = serializers.PrimaryKeyRelatedField(queryset=Entity.objects)
    #obj_to = serializers.SerializerMethodField()
    obj_to = serializers.PrimaryKeyRelatedField(queryset=Entity.objects)

    class Meta:
        model = EntityRelation
        fields = ['id', 'name', 'case', 'created_at', 'updated_at', 'attributes', 'obj_from', 'obj_to']
        read_only_fields = ['created_at', 'updated_at']


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColanderTeam
        fields = ['id', 'name']


class DroppedFileSerializer(serializers.ModelSerializer):
    source_url = serializers.CharField(write_only=True, allow_blank=True)

    class Meta:
        model = DroppedFile
        exclude = ['owner']

    def create(self, validated_data):
        extra_attributes = {}
        if 'source_url' in validated_data:
            extra_attributes = {
                'source_url': validated_data.pop('source_url'),
                'content_type': validated_data['file'].content_type,
                'magic_mime_type': get_upload_file_mime_type(validated_data['file'])
            }
        dropped_file = super().create(validated_data)
        mime_type = mimetypes.guess_type(validated_data['file'].name)
        if mime_type[0] is None:
            dropped_file.mime_type = get_upload_file_mime_type(validated_data['file'])
        else:
            dropped_file.mime_type = mime_type[0]
        dropped_file.filename = validated_data['file'].name
        dropped_file.attributes = extra_attributes
        dropped_file.save()
        return dropped_file
