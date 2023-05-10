from rest_framework import serializers

from colander.core.models import UploadRequest


class UploadRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadRequest
        exclude = [
            'target_artifact_id',
            'owner'
        ]
        read_only_fields = [
            'eof',
            'status',
            'next_addr',
            'created_at',
            'size',
            'name',
        ]

    addr = serializers.IntegerField(required=False, allow_null=False, write_only=True)
    file = serializers.FileField(required=False, allow_empty_file=False, write_only=True)

    def create(self, validated_data):
        print('UploadRequestSerializer create', validated_data)
        instance = super().create(validated_data)
        instance.touch()
        return instance

    def update(self, instance, validated_data):
        print('UploadRequestSerializer update', instance, validated_data)

        if 'addr' not in validated_data:
            raise Exception("UploadRequest update need an addr address")
        if 'file' not in validated_data:
            raise Exception("UploadRequest update need a file")

        provided_addr = validated_data['addr']
        provided_fchunk = validated_data['file']

        instance.append_chunk(provided_addr, provided_fchunk.read())
        instance.save()

        return instance

