from django.http import Http404, HttpResponse
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import CreateAPIView, UpdateAPIView, RetrieveUpdateAPIView

from colander.core.api.serializers import ArtifactSerializer, \
    ArtifactTypeSerializer, \
    CaseSerializer, \
    DeviceSerializer, \
    DeviceTypeSerializer, PiRogueExperimentSerializer
from colander.core.serializers.upload_request_serializers import UploadRequestSerializer
from colander.core.models import Artifact, ArtifactType, Case, Device, DeviceType, UploadRequest


class ApiCaseViewSet(mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     GenericViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CaseSerializer

    def get_queryset(self):
        return Case.objects.filter(owner=self.request.user)


class ApiDeviceTypeViewSet(mixins.RetrieveModelMixin,
                           mixins.ListModelMixin,
                           GenericViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DeviceTypeSerializer
    queryset = DeviceType.objects.all()


class ApiArtifactViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         mixins.CreateModelMixin,
                         GenericViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ArtifactSerializer

    def get_queryset(self):
        return Artifact.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user)

    @action(detail=True)
    def download(self, request, pk):
        try:
            artifact = Artifact.objects.get(pk=pk, owner=request.user)
        except Artifact.DoesNotExist:
            raise Http404
        response = HttpResponse(artifact.file, content_type=artifact.mime_type)
        response['Content-Disposition'] = 'attachment; filename=' + artifact.name
        return response


class ApiArtifactTypeViewSet(mixins.RetrieveModelMixin,
                             mixins.ListModelMixin,
                             GenericViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ArtifactTypeSerializer
    queryset = ArtifactType.objects.all()


class ApiUploadRequestViewSet(mixins.RetrieveModelMixin,
                              mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              mixins.UpdateModelMixin,
                              GenericViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "put"]
    serializer_class = UploadRequestSerializer

    def get_queryset(self):
        return UploadRequest.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user)


class ApiDeviceViewSet(mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       # mixins.UpdateModelMixin,
                       mixins.ListModelMixin,
                       GenericViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DeviceSerializer

    def get_queryset(self):
        return Device.objects.filter(owner=self.request.user).all()

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user)


class ApiPiRogueExperimentViewSet(mixins.CreateModelMixin,
                                  mixins.RetrieveModelMixin,
                                  # mixins.UpdateModelMixin,
                                  mixins.ListModelMixin,
                                  GenericViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PiRogueExperimentSerializer

    def get_queryset(self):
        return Device.objects.filter(owner=self.request.user).all()

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user)
