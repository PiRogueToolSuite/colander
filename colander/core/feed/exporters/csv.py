import csv
import io

from colander.core.serializers.generic import EntitySerializer


class CsvFeedExporter:
    def __init__(self, feed):
        self.feed = feed
        self.__entities = {}

    def __get_entities(self):
        self.__entities = {}
        for entity in self.feed.entities:
            serializer = EntitySerializer(entity)
            if serializer:
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
