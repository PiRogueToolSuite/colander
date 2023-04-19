from rest_framework import serializers

from colander.core.models import UploadRequest


class UploadRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadRequest
        fields = '__all__'
