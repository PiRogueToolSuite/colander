from django.http import Http404, HttpResponse, JsonResponse
from rest_framework import mixins, status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from colander.core.api.security import BearerTokenAuthentication

from colander.core.api.serializers import (
    ArtifactSerializer,
    ArtifactTypeSerializer,
    CaseSerializer,
    DeviceSerializer,
    DeviceTypeSerializer,
    DroppedFileSerializer,
    ObservableSerializer,
    ObservableTypeSerializer,
    PiRogueExperimentSerializer,
    RelationSerializer,
    TeamSerializer,
)
from colander.core.models import (
    Artifact,
    ArtifactType,
    ColanderTeam,
    Device,
    DeviceType,
    DroppedFile,
    EntityRelation,
    Observable,
    ObservableType,
    PiRogueExperiment,
    UploadRequest,
)
from colander.core.serializers.upload_request_serializers import UploadRequestSerializer
from colander.websocket.consumers import CaseContextConsumer


class ApiCaseViewSet(mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     GenericViewSet):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CaseSerializer

    def get_queryset(self):
        queryset = self.request.user.all_my_cases
        # queryset = Case.objects.filter(case__in=cases)

        name = self.request.query_params.get('name')
        if name is not None:
            queryset = queryset.filter(name__icontains=name)

        return queryset

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user)


class ApiDeviceTypeViewSet(mixins.RetrieveModelMixin,
                           mixins.ListModelMixin,
                           GenericViewSet):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DeviceTypeSerializer
    queryset = DeviceType.objects.all()


class ApiArtifactViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         mixins.CreateModelMixin,
                         GenericViewSet):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ArtifactSerializer

    def get_queryset(self):
        cases = self.request.user.all_my_cases
        return Artifact.objects.filter(case__in=cases)

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
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ArtifactTypeSerializer
    queryset = ArtifactType.objects.all()


class ApiUploadRequestViewSet(mixins.RetrieveModelMixin,
                              mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              mixins.UpdateModelMixin,
                              GenericViewSet):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
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
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DeviceSerializer

    def get_queryset(self):
        cases = self.request.user.all_my_cases
        queryset = Device.objects.filter(case__in=cases)

        case_id = self.request.query_params.get('case_id')
        if case_id is not None:
            queryset = queryset.filter(case=case_id)

        name = self.request.query_params.get('name')
        if name is not None:
            queryset = queryset.filter(name__icontains=name)

        return queryset

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user)


class ApiPiRogueExperimentViewSet(mixins.CreateModelMixin,
                                  mixins.RetrieveModelMixin,
                                  mixins.ListModelMixin,
                                  GenericViewSet):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PiRogueExperimentSerializer

    def get_queryset(self):
        cases = self.request.user.all_my_cases
        queryset = PiRogueExperiment.objects.filter(case__in=cases)

        case_id = self.request.query_params.get('case_id')
        if case_id is not None:
            queryset = queryset.filter(case=case_id)

        name = self.request.query_params.get('name')
        if name is not None:
            queryset = queryset.filter(name__icontains=name)

        return queryset

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user)

    @action(methods=['get'], detail=True)
    def analysis(self, request, pk):
        _analysis = None
        cases = self.request.user.all_my_cases
        try:
            experiment = PiRogueExperiment.objects.get(pk=pk, case__in=cases)
            _analysis = experiment.analysis
        except Artifact.DoesNotExist:
            raise Http404
        if _analysis:
            return JsonResponse(_analysis.to_dict(), safe=False, status=status.HTTP_200_OK)
        raise Http404


class ApiObservableViewSet(mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin,
                           # mixins.UpdateModelMixin,
                           mixins.ListModelMixin,
                           GenericViewSet):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ObservableSerializer

    def get_queryset(self):
        cases = self.request.user.all_my_cases
        queryset = Observable.objects.filter(case__in=cases)

        case_id = self.request.query_params.get('case_id')
        if case_id is not None:
            queryset = queryset.filter(case=case_id)

        name = self.request.query_params.get('name')
        if name is not None:
            queryset = queryset.filter(name__icontains=name)

        return queryset

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user)


class ApiObservableTypeViewSet(mixins.RetrieveModelMixin,
                               mixins.ListModelMixin,
                               GenericViewSet):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ObservableTypeSerializer
    queryset = ObservableType.objects.all()


class ApiRelationViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         mixins.CreateModelMixin,
                         GenericViewSet):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = RelationSerializer

    def get_queryset(self):
        cases = self.request.user.all_my_cases
        queryset = EntityRelation.objects.filter(case__in=cases)

        name = self.request.query_params.get('name')
        if name is not None:
            queryset = queryset.filter(name__icontains=name)

        case_id = self.request.query_params.get('case_id')
        if case_id is not None:
            queryset = queryset.filter(case=case_id)

        return queryset

    def perform_create(self, serializer):
        # Bug-0004 : 'upgrade' obj_form and obj_to value to their respective concrete class
        abstract_from = serializer.validated_data['obj_from']
        abstract_to = serializer.validated_data['obj_to']

        concrete_from = abstract_from.concrete()
        concrete_to = abstract_to.concrete()

        serializer.validated_data['obj_from'] = concrete_from
        serializer.validated_data['obj_to'] = concrete_to

        return serializer.save(owner=self.request.user)


class ApiTeamViewSet(mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     GenericViewSet):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TeamSerializer

    def get_queryset(self):
        teams = self.request.user.my_teams_as_qset

        name = self.request.query_params.get('name')
        if name is not None:
            teams = teams.filter(name__icontains=name)

        return teams


class ApiDroppedFileViewSet(mixins.CreateModelMixin,
                            GenericViewSet):
    # authentication_classes class order matter: SessionAuthentication must be last
    # The order matter when the following conditions are met simultaneously:
    #   - POST is made by a webextension (using default [now standard] fetch api)
    #   - POST is made in a browser the user is also authenticated to colander frontend
    # The 'crfstoken' cookie is sent by the fetch api POST if it exists,
    # and webextension can't bypass this behavior. On the other side, Django SessionAuthenfication
    # will fail AND shortcut other authenticators on that specific 'crfstoken' check even
    # the POST doesn't care about Session challenge by providing Token challenge.
    authentication_classes = [TokenAuthentication, BearerTokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DroppedFileSerializer

    def perform_create(self, serializer):
        inst = serializer.save(owner=self.request.user)
        CaseContextConsumer.send_message_to_user_consumers(self.request.user, { 'msg': 'New dropped file' })
        return inst
