from functools import cached_property
from typing import get_args, List

from colander_data_converter.base.common import ObjectReference
from colander_data_converter.base.models import ColanderFeed, Observable, ColanderRepository, Artifact
from colander_data_converter.base.types.observable import ObservableTypes
from colander_data_converter.base.utils import FeedMerger
from django.contrib.contenttypes.models import ContentType
from rest_framework.exceptions import ValidationError

from colander.core.feed.serializers import PolymorphicSerializer, EntityRelationSerializer
from colander.core.models import Case, EntityRelation


class InternalFeed:
    case: Case

    def __init__(self, case: Case):
        self.case = case
        self.content_types = ContentType.objects.filter(
            app_label='core',
            model__in=[
                'actor',
                'artifact',
                'datafragment',
                'detectionrule',
                'device',
                'event',
                'observable',
                'threat'
            ]).all()

    @cached_property
    def cases(self):
        return {
            str(self.case.id): PolymorphicSerializer(self.case).data
        }

    @cached_property
    def entities(self):
        entities = {}
        for content_type in self.content_types:
            entities_from_orm = content_type.model_class().objects.filter(case=self.case).iterator()
            for entity in entities_from_orm:
                entities[str(entity.id)] = PolymorphicSerializer(entity).data
        return entities

    @cached_property
    def relations(self):
        return {
            str(relation.id): PolymorphicSerializer(relation).data for relation in EntityRelation.objects.filter(
                obj_from_id__in=self.entities.keys(),
                obj_to_id__in=self.entities.keys(),
                case=self.case
            ).iterator()
        }

    @cached_property
    def content(self):
        return {
            'cases': self.cases,
            'entities': self.entities,
            'relations': self.relations,
        }


# noinspection DuplicatedCode
class FeedImporter:
    case: Case
    input_feed: ColanderFeed

    def __init__(self, case: Case, input_feed: ColanderFeed):
        ColanderRepository().clear()
        self.case = case
        self.input_feed = input_feed
        self.internal_feed_object = InternalFeed(case)
        self._clean_input_feed()

    @classmethod
    def get_serializer_class(cls, data):
        return PolymorphicSerializer.get_serializer_from_data(data)

    @classmethod
    def get_model_class(cls, data):
        serializer = cls.get_serializer_class(data)
        return serializer.Meta.model

    def create_or_update(self, data):
        model_class = self.get_model_class(data)
        if not model_class:
            raise ValidationError(f'Model not found for {data}')

    def _clean_input_feed(self):
        for source in self.input_feed.entities.values():
            for field_name, field_info in source.__class__.model_fields.items():
                source_field_value = getattr(source, field_name, None)
                if ObjectReference in get_args(field_info.annotation):
                    if not self.input_feed.contains(source_field_value):
                        setattr(source, field_name, None)
                if List[ObjectReference] in get_args(field_info.annotation):
                    new_refs = []
                    for ref in source_field_value:
                        if self.input_feed.contains(ref):
                            new_refs.append(ref)
                    setattr(source, field_name, new_refs)

    def _convert_new_artifacts(self, internal_feed: ColanderFeed):
        # Replace new artifacts with SHA256
        self.input_feed.break_immutable_relations()
        to_update = []
        for _, entity in self.input_feed.entities.items():
            if isinstance(entity, Artifact):
                internal_entity = None
                for e in internal_feed.entities.values():
                    if (isinstance(e, Observable) and
                        e.type.short_name == 'SHA256' and
                        e.name == entity.sha256
                    ):
                        internal_entity = e
                        break
                # The artifact has already been converted and is present in the internal feed
                if isinstance(internal_entity, Observable) and internal_entity.type.short_name == 'SHA256':
                    to_update.append((entity, internal_entity))
                else:
                    observable = Observable(
                        id=entity.id,
                        type=ObservableTypes.SHA256.value,
                        name=entity.sha256,
                        description=entity.description,
                        attributes=entity.attributes or {},
                        created_at=entity.created_at,
                        updated_at=entity.updated_at,
                    )
                    observable.attributes['filename'] = entity.name
                    if entity.md5:
                        observable.attributes['md5'] = entity.md5
                    if entity.sha1:
                        observable.attributes['sha1'] = entity.sha1
                    if entity.mime_type:
                        observable.attributes['mime_type'] = entity.mime_type
                    if entity.original_name:
                        observable.attributes['original_name'] = entity.original_name
                    if entity.size_in_bytes:
                        observable.attributes['size_in_bytes'] = entity.size_in_bytes
                    self.input_feed.entities[str(entity.id)] = observable
        for original, new in to_update:
            self.input_feed.entities.pop(str(original.id))
            self.input_feed.entities[str(new.id)] = new
            for _, relation in self.input_feed.get_relations(original, exclude_immutables=True).items():
                if relation.obj_from == original:
                    relation.obj_from = new
                if relation.obj_to == original:
                    relation.obj_to = new
        self.input_feed.rebuild_immutable_relations()

    def import_feed(self):
        # Generate feed of the case
        c = self.internal_feed_object.content
        internal_feed = ColanderFeed.load(c)

        # Merge the two feeds
        feed_merger = FeedMerger(self.input_feed, internal_feed)
        feed_merger.merge(aggressive=True)

        internal_feed.unlink_references()
        # Create new entities
        for entity_id, entity in internal_feed.entities.items():
            entity.case = self.case.id
            entity_data = entity.model_dump(mode='json')
            model_class = self.get_model_class(entity_data)
            serializer_class = self.get_serializer_class(entity_data)
            if not model_class.objects.filter(id=entity_id).exists():
                serializer = serializer_class(data=entity_data, context={'case': self.case})
                if serializer.is_valid():
                    serializer.save()

        # Update entities
        for entity_id, entity in internal_feed.entities.items():
            entity.case = self.case.id
            entity_data = entity.model_dump(mode='json')
            model_class = self.get_model_class(entity_data)
            serializer_class = self.get_serializer_class(entity_data)
            if model_class.objects.filter(id=entity_id).exists():
                instance = model_class.objects.get(id=entity_id)
                serializer = serializer_class(instance=instance, data=entity_data, context={'case': self.case})
                if serializer.is_valid():
                    serializer.save()

        # Create new relations
        for relation_id, relation in internal_feed.relations.items():
            relation.case = self.case.id
            relation_data = relation.model_dump(mode='json')
            obj_from_id = relation_data.get('obj_from')
            obj_to_id = relation_data.get('obj_to')
            if isinstance(obj_from_id, dict):
                obj_from_id = obj_from_id.get('id')
            if isinstance(obj_to_id, dict):
                obj_to_id = obj_to_id.get('id')
            relation_data['obj_from_id'] = obj_from_id
            relation_data['obj_to_id'] = obj_to_id
            model_class = self.get_model_class(relation_data)
            if not model_class.objects.filter(id=relation_id).exists():
                serializer = EntityRelationSerializer(data=relation_data, context={'case': self.case})
                if serializer.is_valid():
                    serializer.save()
