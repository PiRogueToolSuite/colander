# /experiment
# /experiment/{id}/pcap
# /experiment/{id}/sslkeylog
# /experiment/{id}/socket_trace
# /experiment/{id}/aes_trace
# /experiment/{id}/trace
from tempfile import NamedTemporaryFile

import magic
import pathlib

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from colander.core.api.serializers import ExperimentSerializer, NetworkDumpSerializer, EvidenceSerializer
from colander.core.models import Experiment, NetworkDump, Evidence
from colander.core.utils import hash_file


class ExperimentViewSet(viewsets.ModelViewSet):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class NetworkDumpViewSet(viewsets.ModelViewSet):
    queryset = NetworkDump.objects.all()
    serializer_class = NetworkDumpSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class EvidenceViewSet(viewsets.ModelViewSet):
    queryset = Evidence.objects.all()
    serializer_class = EvidenceSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        evidence_type = Evidence.OTHER
        supported_types = [k for k,_ in Evidence.EVIDENCE_TYPE]
        print(supported_types)
        if 'type' in self.request.query_params:
            type = self.request.query_params.get('type')
            print(type)
            if type in supported_types:
                evidence_type = type
        print(evidence_type)
        file_name = str(self.request.FILES['file'])
        uploaded_file = self.request.FILES['file']
        with NamedTemporaryFile(suffix=file_name) as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp.seek(0)
            sha256, sha1, md5, size = hash_file(tmp)
            mime_type = magic.from_file(tmp.name, mime=True)
        extension = pathlib.Path(file_name).suffix
        serializer.save(
            owner=self.request.user,
            md5=md5,
            sha1=sha1,
            sha256=sha256,
            size_in_bytes=size,
            mime_type=mime_type,
            original_name=file_name,
            extension=extension,
            type = evidence_type
        )
