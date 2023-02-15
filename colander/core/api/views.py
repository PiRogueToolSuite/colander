from django.http import Http404, HttpResponse
from rest_framework import mixins
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from colander.core.api.serializers import ArtifactSerializer, DeviceSerializer, DeviceTypeSerializer
from colander.core.models import Artifact, Device, DeviceType


class ApiArtifactViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         # mixins.CreateModelMixin,
                         GenericViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ArtifactSerializer

    def get_queryset(self):
        return Artifact.objects.filter(owner=self.request.user)

    @action(detail=False, methods=['POST'])
    def upload(self):
        pass

    @action(detail=True)
    def download(self, request, pk):
        try:
            artifact =  Artifact.objects.get(pk=pk, owner=request.user)
        except Artifact.DoesNotExist:
            raise Http404
        response = HttpResponse(artifact.file, content_type=artifact.mime_type)
        response['Content-Disposition'] = 'attachment; filename=' + artifact.name
        return response


# class ApiArtifactDownload(APIView):
#     authentication_classes = [SessionAuthentication, TokenAuthentication]
#     permission_classes = [IsAuthenticated]
#
#     def get_object(self, pk, owner):
#         try:
#             return Artifact.objects.get(pk=pk, owner=owner)
#         except Artifact.DoesNotExist:
#             raise Http404
#
#     def get(self, request, pk, format=None):
#         artifact = self.get_object(pk, request.user)
#         response = HttpResponse(artifact.file, content_type=artifact.mime_type)
#         response['Content-Disposition'] = 'attachment; filename=' + artifact.name
#         return response


class ApiDeviceTypeViewSet(mixins.RetrieveModelMixin,
                           mixins.ListModelMixin,
                           GenericViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DeviceTypeSerializer
    queryset = DeviceType.objects.all()


class ApiDeviceViewSet(mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.ListModelMixin,
                       GenericViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DeviceSerializer

    def get_queryset(self):
        return Device.objects.filter(owner=self.request.user).all()

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user)
