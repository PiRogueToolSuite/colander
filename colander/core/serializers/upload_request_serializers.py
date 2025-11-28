from rest_framework import serializers

from colander.core.models import UploadRequest


class UploadRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadRequest
        exclude = [
            #'target_entity_id',
            'owner'
        ]
        read_only_fields = [
            'eof',
            'status',
            'next_addr',
            'created_at',
        ]

    addr = serializers.IntegerField(required=False, allow_null=False, write_only=True)
    file = serializers.FileField(required=False, allow_empty_file=True, write_only=True)

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.touch()
        return instance

    def update(self, instance, validated_data):
        if 'addr' in validated_data or 'file' in validated_data:
            if instance.eof:
                raise Exception("UploadRequest update can't accept new chunk as it already reached EOF")
            if 'addr' not in validated_data:
                raise Exception("UploadRequest update need an addr address")
            if 'file' not in validated_data:
                raise Exception("UploadRequest update need a file")

            provided_addr = validated_data['addr']
            provided_fchunk = validated_data['file']

            instance.append_chunk(provided_addr, provided_fchunk.read())

            validated_data.pop('addr')
            validated_data.pop('file')

            instance.save()

        return super().update(instance, validated_data)

