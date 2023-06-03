import uuid

from colander.core.models import Case
from colander.core.serializers.generic import *


class Stix2CaseExporter:
    case: Case
    __entities: dict = None
    __relations: dict = None

    def __init__(self, case: Case, feed, entities: []):
        self.case = case
        self.feed = feed
        self.input_entities = entities
        self.__entity_ids: list[str] = []
        self.__relations: dict = {}

    def __indicator(self, entity) -> (str, dict):
        _id = f'indicator--{entity.id}'
        pattern_prefix = entity.type.stix2_pattern
        if entity.super_type.lower() == 'observable':
            associated_threat = entity.associated_threat
            operated_by = entity.operated_by
            extracted_from = entity.extracted_from
            if associated_threat and associated_threat in self.input_entities:
                _r_id = f'relationship--{uuid.uuid4()}'
                self.__relations[_r_id] = {
                    'type': 'relationship',
                    'spec_version': '2.1',
                    'id': _r_id,
                    'created': entity.created_at.isoformat(),
                    'modified': entity.updated_at.isoformat(),
                    'relationship_type': 'indicates',
                    'source_ref': _id,
                    'target_ref': f'{associated_threat.type.stix2_type}--{associated_threat.id}'
                }
            if operated_by and operated_by in self.input_entities:
                _r_id = f'relationship--{uuid.uuid4()}'
                self.__relations[_r_id] = {
                    'type': 'relationship',
                    'spec_version': '2.1',
                    'id': _r_id,
                    'created': entity.created_at.isoformat(),
                    'modified': entity.updated_at.isoformat(),
                    'relationship_type': 'indicates',
                    'source_ref': _id,
                    'target_ref': f'{operated_by.type.stix2_type}--{operated_by.id}'
                }
            if extracted_from and extracted_from in self.input_entities:
                _r_id = f'relationship--{uuid.uuid4()}'
                self.__relations[_r_id] = {
                    'type': 'relationship',
                    'spec_version': '2.1',
                    'id': _r_id,
                    'created': entity.created_at.isoformat(),
                    'modified': entity.updated_at.isoformat(),
                    'relationship_type': 'extracted from',
                    'source_ref': _id,
                    'target_ref': f'{extracted_from.type.stix2_type}--{extracted_from.id}'
                }
        indicator_types = []
        if hasattr(entity, 'associated_threat') and entity.associated_threat:
            indicator_types = ['malicious-activity']
        return _id, {
            'id': _id,
            'type': 'indicator',
            'spec_version': '2.1',
            'created': entity.created_at.isoformat(),
            'modified': entity.updated_at.isoformat(),
            'description': entity.description,
            'indicator_types': indicator_types,
            'pattern': f"{pattern_prefix}='{entity.value}'",
            'pattern_type': entity.type.stix2_pattern_type,
            'pattern_version': '2.1',
            'valid_from': entity.created_at.timestamp()
        }

    def __identity(self, entity) -> (str, dict):
        _id = f'identity--{entity.id}'
        identity_class = None
        if ':' in entity.type.stix2_value_field_name:
            identity_class = entity.type.stix2_value_field_name.split(':')[1]
        return _id, {
            'id': _id,
            'type': 'identity',
            'spec_version': '2.1',
            'created': entity.created_at.isoformat(),
            'modified': entity.updated_at.isoformat(),
            'description': entity.description,
            'name': entity.value,
            'identity_class': identity_class
        }

    def __threat_actor(self, entity) -> (str, dict):
        _id = f'threat-actor--{entity.id}'
        return _id, {
            'id': _id,
            'type': 'threat-actor',
            'spec_version': '2.1',
            'created': entity.created_at.isoformat(),
            'modified': entity.updated_at.isoformat(),
            'description': entity.description,
            'name': entity.value,
        }

    def __malware(self, entity) -> (str, dict):
        _id = f'malware--{entity.id}'
        malware_class = None
        if ':' in entity.type.stix2_value_field_name:
            malware_class = [entity.type.stix2_value_field_name.split(':')[1]]
        return _id, {
            'id': _id,
            'type': 'malware',
            'spec_version': '2.1',
            'created': entity.created_at.isoformat(),
            'modified': entity.updated_at.isoformat(),
            'description': entity.description,
            'name': entity.value,
            'malware_types': malware_class
        }

    def __infrastructure(self, entity) -> (str, dict):
        _id = f'infrastructure--{entity.id}'
        infrastructure_class = None
        if ':' in entity.type.stix2_value_field_name:
            infrastructure_class = [entity.type.stix2_value_field_name.split(':')[1]]
        return _id, {
            'id': _id,
            'type': 'infrastructure',
            'spec_version': '2.1',
            'created': entity.created_at.isoformat(),
            'modified': entity.updated_at.isoformat(),
            'description': entity.description,
            'name': entity.value,
            'infrastructure_types': infrastructure_class
        }

    def __artifact(self, entity) -> (str, dict):
        _id = f'artifact--{entity.id}'
        return _id, {
            'id': _id,
            'type': 'artifact',
            'spec_version': '2.1',
            'created': entity.created_at.isoformat(),
            'modified': entity.updated_at.isoformat(),
            'description': entity.description,
            'mime_type': entity.mime_type,
            'hashes': {
                'MD5': entity.md5,
                'SHA-1': entity.sha1,
                'SHA-256': entity.sha256,
            }
        }

    def __get_entities(self):
        if self.__entities:
            return self.__entities
        self.__entities = {}
        for entity in self.input_entities:
            stix2_type = entity.type.stix2_type
            entity_id, _entity = '', None
            if stix2_type == 'indicator':
                entity_id, _entity = self.__indicator(entity)
            elif stix2_type == 'identity':
                entity_id, _entity = self.__identity(entity)
            elif stix2_type == 'threat-actor':
                entity_id, _entity = self.__threat_actor(entity)
            elif stix2_type == 'malware':
                entity_id, _entity = self.__malware(entity)
            elif stix2_type == 'infrastructure':
                entity_id, _entity = self.__infrastructure(entity)
            elif stix2_type == 'artifact':
                entity_id, _entity = self.__artifact(entity)
            if entity_id and _entity:
                self.__entity_ids.append(entity_id)
                self.__entities[entity_id] = _entity
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
        entities = list(self.__get_entities().values())
        relations = list(self.__relations.values())
        return {
            'type': 'bundle',
            'id': f'bundle--{self.feed.id}',
            'objects': entities + relations
        }
