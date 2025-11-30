from functools import cached_property

from django.contrib.contenttypes.models import ContentType

from colander.core.feed.serializers import PolymorphicSerializer
from colander.core.models import EntityRelation


class InternalFeed:
    def __init__(self, case):
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
