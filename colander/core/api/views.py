import json

from django.http import Http404, HttpResponse, JsonResponse
from django.urls import reverse
from rest_framework import mixins, status, permissions
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from colander.core.api.security import (
    BearerTokenAuthentication,
    ApiTokenAuthentication,
    HasViewPermission,
)
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
    Device,
    DeviceType,
    EntityRelation,
    Observable,
    ObservableType,
    PiRogueExperiment,
    UploadRequest, DeviceMonitoring,
)
from colander.core.serializers.device_monitoring_serializers import NetworkEventSerializer
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


class ApiRootActionsForbiddenViewSet(GenericViewSet):
    def list(self, request):
        return JsonResponse({}, status=400)

    def create(self, request):
        return JsonResponse({}, status=400)

    def retrieve(self, request, pk=None):
        return JsonResponse({}, status=400)

    def update(self, request, pk=None):
        return JsonResponse({}, status=400)

    def partial_update(self, request, pk=None):
        return JsonResponse({}, status=400)

    def destroy(self, request, pk=None):
        return JsonResponse({}, status=400)

    @action(detail=True, methods=['post'])
    def foo(self, request, pk=None):  # bar/<pk>/foo/
        return JsonResponse({}, status=400)


class NetworkEventsViewSet(GenericViewSet):
    authentication_classes = [ApiTokenAuthentication]
    permission_classes = [HasViewPermission]

    @staticmethod
    def import_network_events(device_monitoring: DeviceMonitoring, raw_data):
        if not device_monitoring or not raw_data or not isinstance(raw_data, list):
            return

        for data in raw_data:
            serializer_class = NetworkEventSerializer.get_serializer_from_data(data)
            if not serializer_class:
                return
            data['device_monitoring'] = str(device_monitoring.id)
            serializer = serializer_class(data=data, context={'device_monitoring': device_monitoring})
            if serializer.is_valid():
                serializer.save()
            else:
                print('not valid', serializer.errors)

    @action(detail=False, methods=['post'], url_path=r'(?P<pk>[^/.]+)')
    def ingest(self, request, pk=None):
        """
        Handle incoming webhook requests for device monitoring.
        This view processes network events sent to the device monitoring webhook endpoint.
        It validates the request authentication, checks if monitoring is active, and imports
        the network events data.

        Args:
            request: The HTTP request object containing the webhook payload.
            pk: The primary key of the :class:`~colander.core.models.DeviceMonitoring` instance.

        Returns:
            An :class:`~django.http.JsonResponse` with status 200 and empty content.
            Returns 200 for all cases (success, failure, unauthorized) to prevent
            information disclosure to potential attackers.

        Note:
            Authentication is verified either through Django's user authentication
            or via the X-Authentication header with the monitoring's authentication token.
        """
        # Retrieve the monitoring instance
        try:
            monitoring = DeviceMonitoring.objects.get(id=pk)
        except DeviceMonitoring.DoesNotExist:
            return JsonResponse({}, status=400)

        if request.api_token != monitoring.api_token:
            return JsonResponse({}, status=400)

        # Check if the monitoring period has expired
        if monitoring.has_expired():
            return JsonResponse({}, status=400)

        # Parse the JSON payload, returning success on invalid JSON to avoid information disclosure
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({}, status=200)

        # Import the network events from the validated payload
        try:
            self.import_network_events(monitoring, data)
        except (Exception,):
            return JsonResponse({}, status=200)

        return JsonResponse({'success': True}, status=200)


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
        CaseContextConsumer.send_message_to_user_consumers(
            self.request.user, {
                'msg': 'A new drop is available',
                'detail': inst.filename,
                'url': reverse('dropped_files_triage_base_view'),
            }
        )
        return inst
