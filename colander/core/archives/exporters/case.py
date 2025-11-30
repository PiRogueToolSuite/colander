import datetime
import io
import json
import zipfile
from django.core.serializers.json import DjangoJSONEncoder

from colander.core.archives.exporters.utils import Buffer
from colander.core.archives.serializers import serializers_by_model
from colander.core.models import Case, SubGraph


class CaseArchiveExporter:
    _case: Case

    def __init__(self, case: Case):
        self._case = case
        self._entities = case.entities
        self._entities.extend(SubGraph.objects.filter(case=self._case).all())
        self._relations = case.relations
        print('all entities', self._entities)

    def export(self, pretty:bool=False):
        buffer = io.BytesIO()
        for buf in self.async_export(pretty=pretty):
            buffer.write(buf)
        buffer.seek(0)
        return buffer.getvalue()

    def async_export(self, pretty:bool=False):
        manifest = {
            'export_date': datetime.datetime.now(),
            'files': {}
        }
        buffer = Buffer()
        with zipfile.ZipFile(buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as archive:
            serializer = serializers_by_model.get(Case, None)
            json_content = json.dumps( serializer(self._case, many=False).data, cls=DjangoJSONEncoder, indent=2 if pretty else None )

            fname = "data.json"
            archive.writestr("data.json", json_content)
            yield buffer.take()
            manifest['files'][fname] = 'md5sum'

            for entity in self._entities:
                entity_model = entity.__class__
                serializer = serializers_by_model.get(entity_model, None)
                if serializer:
                    data = serializer(entity, many=False).data
                    json_content = json.dumps( data, cls=DjangoJSONEncoder, indent=2 if pretty else None )
                    fname = f"{str(entity_model.__name__)}/{str(entity.id)}/data.json"
                    archive.writestr(fname, json_content)
                    yield buffer.take()
                    manifest['files'][fname] = 'md5sum'

                    if hasattr(entity, 'thumbnail'):
                        if entity.thumbnail:
                            thumbnail_data = entity.thumbnail.file.read()
                            fname = f"{str(entity_model.__name__)}/{str(entity.id)}/thumbnail.png"
                            archive.writestr(fname, thumbnail_data)
                            yield buffer.take()
                            manifest['files'][fname] = 'md5sum'

                    if hasattr(entity, 'file'):
                        if entity.file:
                            file_data = entity.file.file.read()
                            fname = f"{str(entity_model.__name__)}/{str(entity.id)}/file{str(entity.extension)}"
                            archive.writestr(fname, file_data)
                            yield buffer.take()
                            manifest['files'][fname] = 'md5sum'

            for relation in self._relations:
                if relation.immutable: continue
                entity_model = relation.__class__
                serializer = serializers_by_model.get(entity_model, None)
                if serializer:
                    data = serializer(relation, many=False).data
                    json_content = json.dumps( data, cls=DjangoJSONEncoder, indent=2 if pretty else None )
                    fname = f"{str(entity_model.__name__)}/{str(relation.id)}/data.json"
                    archive.writestr(fname, json_content)
                    yield buffer.take()
                    manifest['files'][fname] = 'md5sum'

            json_content = json.dumps( manifest, cls=DjangoJSONEncoder, indent=2 if pretty else None )
            archive.writestr("manifest.json", json_content)
            yield buffer.take()

        yield buffer.end()
