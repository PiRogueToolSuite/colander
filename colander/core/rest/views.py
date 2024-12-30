import fnmatch
import mimetypes

import json
import magic

from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import JsonResponse
from rest_framework import mixins, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ViewSet

from colander.core import datasets
from colander.core.api.serializers import DroppedFileSerializer, CaseSerializer, \
    ArtifactTypeSerializer, DeviceSerializer
from colander.core.graph.serializers import GraphRelationSerializer
from colander.core.models import (
    Case,
    Entity,
    EntityRelation,
    Event,
    EventType,
    Observable,
    ObservableType,
    Threat,
    ThreatType, Device, DeviceType, Actor, ActorType, DroppedFile, ArtifactType,
)
from colander.core.rest.serializers import DetailedEntitySerializer


class DatasetViewSet(ViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False)
    def creatable_entities(self, request):
        return Response(datasets.creatable_entity_and_types)

    @action(detail=False)
    def all_styles(self, request):
        return Response(datasets.all_styles)


class EntityRelationViewSet(mixins.CreateModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = GraphRelationSerializer

    def get_queryset(self):
        cases = self.request.user.all_my_cases
        return EntityRelation.objects.filter(case__in=cases)

    def perform_create(self, serializer):
        case_id = self.request.data.pop("case_id")

        # Bug-0004 : 'upgrade' obj_form and obj_to value to their respective concrete class
        abstract_from = serializer.validated_data['obj_from']
        abstract_to = serializer.validated_data['obj_to']

        concrete_from = abstract_from.concrete()
        concrete_to = abstract_to.concrete()

        serializer.validated_data['obj_from'] = concrete_from
        serializer.validated_data['obj_to'] = concrete_to

        return serializer.save(
            owner=self.request.user,
            case=Case.objects.get(pk=case_id)
        )


class EntityViewSet(mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    RetrieveModelMixin,
                    GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DetailedEntitySerializer

    def get_queryset(self):
        cases = self.request.user.all_my_cases
        return Entity.objects.filter(case__in=cases)

    def get_object(self):
        obj = super().get_object()
        obj = obj.concrete()
        return obj

    def perform_create(self, serializer):
        case_id = self.request.data.pop("case_id")
        case = Case.objects.get(pk=case_id) #get_active_case(self.request)
        return serializer.save(
            owner=self.request.user,
            case=case,
            tlp=case.tlp,
            pap=case.pap,
        )


class DroppedFileViewSet(RetrieveModelMixin,
                         GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DroppedFileSerializer

    def get_queryset(self):
        return DroppedFile.objects.filter(owner=self.request.user)


class CaseViewSet(RetrieveModelMixin,
                  GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CaseSerializer

    def get_queryset(self):
        return self.request.user.all_my_cases

    @action(detail=True, methods=['GET'])
    def devices(self, request, pk=None):
        # Implicitly 'case' the user can contribute
        case = self.get_queryset().get(pk=pk)
        devices = Device.objects.filter(case__id=case.id)
        devicesDictionary = {}
        serializer = DeviceSerializer()
        for device in devices:
            devicesDictionary[str(device.id)] = serializer.to_representation(device)
        return JsonResponse(devicesDictionary, safe=False)


class ArtifactTypeViewSet(ListModelMixin,
                          RetrieveModelMixin,
                          GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ArtifactTypeSerializer

    def get_queryset(self):
        return ArtifactType.objects.all()

    def _get_artifact_types_from_mime_type(self, tested_mime_type):
        serialized_artifact_types = []

        for at in ArtifactType.objects.all():
            if 'suggested_by_mime_types' not in at.type_hints:
                continue
            if 'types' not in at.type_hints['suggested_by_mime_types']:
                continue
            print(at.type_hints['suggested_by_mime_types']['types'])
            for t in at.type_hints['suggested_by_mime_types']['types']:
                print(f'type: {tested_mime_type} against {t}')
                if fnmatch.fnmatch(tested_mime_type, t):
                    serializer = self.get_serializer(at)
                    serialized_artifact_types.append(serializer.data)
                    break

        return serialized_artifact_types

    @action(detail=False, methods=['POST'])
    def suggest_by_filename(self, request):
        if 'filename' not in request.data:
            return Response("Missing filename field", status.HTTP_400_BAD_REQUEST)
        mime_type = mimetypes.guess_type(request.data['filename'])
        if mime_type[0] is None:
            return JsonResponse([], safe=False)
        serialized_artifact_types = self._get_artifact_types_from_mime_type(mime_type[0])
        return JsonResponse(serialized_artifact_types, safe=False)

    @action(detail=False, methods=['POST'])
    def suggest_by_mimetype(self, request):
        if 'mime_type' not in request.data:
            return Response("Missing mime_type field", status.HTTP_400_BAD_REQUEST)
        serialized_artifact_types = self._get_artifact_types_from_mime_type(request.data['mime_type'])
        return JsonResponse(serialized_artifact_types, safe=False)


def get_threatr_entity_type(entity):
    if entity['super_type']['short_name'] == 'OBSERVABLE':
        try:
            return Observable, ObservableType.objects.get(short_name=entity['type']['short_name'])
        except Exception:
            return None, None
    if entity['super_type']['short_name'] == 'DEVICE':
        try:
            return Device, DeviceType.objects.get(short_name=entity['type']['short_name'])
        except Exception:
            return None, None
    if entity['super_type']['short_name'] == 'THREAT':
        try:
            return Threat, ThreatType.objects.get(short_name=entity['type']['short_name'])
        except Exception:
            return None, None
    if entity['super_type']['short_name'] == 'ACTOR':
        try:
            return Actor, ActorType.objects.get(short_name=entity['type']['short_name'])
        except Exception:
            return None, None
    if entity['super_type']['short_name'] == 'EVENT':
        try:
            return Event, EventType.objects.get(short_name=entity['type']['short_name'])
        except Exception:
            return None, None
    return None, None


def update_or_create_entity(entity: dict, model: type, entity_type, case: Case, owner):
    obj, created = model.objects.update_or_create(
        type=entity_type,
        name=entity.get('name'),
        case=case,
        defaults={
            'owner': owner,
            'tlp': entity.get('tlp'),
            'pap': entity.get('pap'),
            'description': entity.get('description'),
            'source_url': entity.get('source_url'),
        }
    )
    if hasattr(obj, 'attributes'):
        obj_attributes = obj.attributes
        if obj_attributes:
            obj.attributes.update(entity.get('attributes'))
            obj.save()
        elif entity.get('attributes'):
            obj.attributes = entity.get('attributes')
            obj.save()
    return obj, created


def update_or_create_event(entity: dict, entity_type, root_entity, case: Case, owner):
    obj, created = Event.objects.update_or_create(
        type=entity_type,
        name=entity.get('name'),
        # ToDo: unique together "type", "name", "first_seen", "last_seen", "involved_entity"
        # 'first_seen': entity.get('first_seen'),
        # 'last_seen': entity.get('last_seen'),
        case=case,
        defaults={
            'owner': owner,
            'first_seen': entity.get('first_seen'),
            'last_seen': entity.get('last_seen'),
            'count': entity.get('count'),
            'description': entity.get('description'),
            'source_url': entity.get('source_url'),
        }
    )
    if root_entity.super_type == 'Observable':
        obj.involved_observables.add(root_entity)
        obj.save()
    obj_attributes = obj.attributes
    if obj_attributes:
        obj.attributes.update(entity.get('attributes'))
        obj.save()
    elif entity.get('attributes'):
        obj.attributes = entity.get('attributes')
        obj.save()
    return obj, created


def __create_immutable_relation(obj_from, obj_to, relation):
    attr_name = relation.get('name').strip().lower().replace(' ', '_')
    if hasattr(obj_to, attr_name) and not getattr(obj_to, attr_name):
        try:
            setattr(obj_to, attr_name, obj_from)
            obj_to.save()
            return True
        except:
            pass
    elif hasattr(obj_from, attr_name) and not getattr(obj_from, attr_name):
        try:
            setattr(obj_from, attr_name, obj_to)
            obj_from.save()
            return True
        except:
            pass
    return False


def update_or_create_entity_relation(obj_from, obj_to, relation, case: Case, owner):
    obj = None
    created = True

    if __create_immutable_relation(obj_from, obj_to, relation):
        return obj, created

    existing_relations = EntityRelation.objects.filter(
        name=relation.get('name'),
        case=case,
        obj_from_id=obj_from.id,
        obj_to_id=obj_to.id)
    if existing_relations:
        obj = existing_relations.first()
        created = False
    if not obj:
        obj = EntityRelation(
            name=relation.get('name'),
            case=case,
            obj_from=obj_from,
            obj_to=obj_to,
            owner=owner
        )
        obj.save()
    obj_attributes = obj.attributes
    if obj_attributes:
        obj.attributes.update(relation.get('attributes'))
        obj.save()
    elif relation.get('attributes'):
        obj.attributes = relation.get('attributes')
        obj.save()
    return obj, created

@login_required
def import_entity_from_threatr(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        case_id = data.get('case_id', None)
        root = data.get('root', None)
        entity = data.get('entity', None)
        event = data.get('event', None)
        relation = data.get('relation', None)
        case = Case.objects.get(pk=case_id)
        if root :
            root_model, root_type = get_threatr_entity_type(root)
            root_obj, _ = update_or_create_entity(root, root_model, root_type, case, request.user)
            if event:
                _, entity_type = get_threatr_entity_type(event)
                try:
                    update_or_create_event(event, entity_type, root_obj, case, request.user)
                except:
                    return JsonResponse({'status': -1})
            elif entity and relation:
                entity_model, entity_type = get_threatr_entity_type(entity)
                if not entity_model:
                    return JsonResponse({'status': -1})
                entity_obj, _ = update_or_create_entity(entity, entity_model, entity_type, case, request.user)
                if relation.get('obj_from') == root.get('id'):
                    obj_from = root_obj
                    obj_to = entity_obj
                else:
                    obj_from = entity_obj
                    obj_to = root_obj
                update_or_create_entity_relation(obj_from, obj_to, relation, case, request.user)
            return JsonResponse({'status': 0})
    return JsonResponse({'status': -1})
