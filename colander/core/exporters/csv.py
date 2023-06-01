import csv
import io

from colander.core.models import Case
from colander.core.serializers.generic import *


class CsvCaseExporter:
    case: Case
    __entities: dict = None

    serializers = {
        Actor: ActorSerializer,
        Artifact: ArtifactSerializer,
        Device: DeviceSerializer,
        Observable: ObservableSerializer,
        Threat: ThreatSerializer,
    }

    def __init__(self, case: Case, entities: []):
        self.case = case
        self.input_entities = entities
        self.__entity_ids: list[str] = []

    def __get_entities(self):
        if self.__entities:
            return self.__entities
        self.__entities = {}
        for entity in self.input_entities:
            serializer = EntitySerializer(entity)
            if serializer:
                self.__entity_ids.append(str(entity.id))
                self.__entities[str(entity.id)] = serializer.data
        return self.__entities

    def export(self):
        fields = [
            'id',
            'super_type',
            'type',
            'type_name',
            'value',
            'created_at',
            'updated_at',
            'sha256',
            'tlp',
            'pap',
            'source_url',
            'description',
        ]
        with io.StringIO() as out:
            writer = csv.DictWriter(out, fieldnames=fields)
            writer.writeheader()
            for _, entity in self.__get_entities().items():
                writer.writerow(entity)
            out.seek(0)
            return out.read()
