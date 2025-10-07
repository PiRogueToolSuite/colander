from typing import List, Type

from colander.core.models import Entity
from colander.core.serializers.generic import *


class JsonCaseExporter:
    case: Case
    __entities: dict = None

    serializers = {
        Actor: ActorSerializer,
        Artifact: ArtifactSerializer,
        Device: DeviceSerializer,
        Observable: ObservableSerializer,
        Threat: ThreatSerializer,
    }

    def __init__(self, case: Case, entities: List[Type[Entity]]):
        self.case = case
        self.input_entities = entities
        self.__entity_ids: list[str] = []

    def __get_entities(self):
        if self.__entities:
            return self.__entities
        self.__entities = {}
        for entity in self.input_entities:
            entity_model = entity.__class__
            serializer = self.serializers.get(entity_model, None)
            if serializer:
                self.__entity_ids.append(str(entity.id))
                self.__entities[str(entity.id)] = serializer(entity, many=False).data
        return self.__entities

    def __get_relations(self):
        if not self.__entities:
            self.__entities = self.__get_entities()
        relations = EntityRelation.objects.filter(
            obj_from_id__in=self.__entity_ids,
            obj_to_id__in=self.__entity_ids,
            case=self.case,
        )
        objects = {}
        for r in relations.all():
            objects[str(r.id)] = EntityRelationSerializer(r).data
        return objects

    def export(self):
        return {
            'cases': {str(self.case.id): CaseSerializer(self.case).data},
            'entities': self.__get_entities(),
            'relations': self.__get_relations(),
        }
