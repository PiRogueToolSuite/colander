from rest_framework import serializers

from colander.core.models import Experiment, NetworkDump, Evidence


class ExperimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experiment
        fields = '__all__'


class NetworkDumpSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkDump
        fields = '__all__'


class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = '__all__'
