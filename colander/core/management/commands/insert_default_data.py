import enum
from typing import Tuple, List, Type

from colander_data_converter.base.types.actor import ActorTypes as cdc_ActorTypes
from colander_data_converter.base.types.artifact import ArtifactTypes as cdc_ArtifactTypes
from colander_data_converter.base.types.base import CommonEntityType as cdc_CommonEntityType
from colander_data_converter.base.types.data_fragment import DataFragmentTypes as cdc_DataFragmentTypes
from colander_data_converter.base.types.detection_rule import DetectionRuleTypes as cdc_DetectionRuleTypes
from colander_data_converter.base.types.device import DeviceTypes as cdc_DeviceTypes
from colander_data_converter.base.types.event import EventTypes as cdc_EventTypes
from colander_data_converter.base.types.observable import ObservableTypes as cdc_ObservableTypes
from colander_data_converter.base.types.threat import ThreatTypes as cdc_ThreatTypes
from django.core.management.base import BaseCommand

from colander.core.models import (
    ActorType,
    ArtifactType,
    DataFragmentType,
    DetectionRuleType,
    DeviceType,
    EventType,
    ObservableType,
    ThreatType, CommonModelType,
)


class Command(BaseCommand):
    help = 'Insert default data.'

    def handle(self, *args, **options):
        """
        Inserts default data into the database for each entity type defined in the system.

        Iterates over a list of model types and their corresponding enum definitions,
        and for each enum value, updates or creates a database entry with the default attributes.

        Side Effects:
            Updates or creates records in the database for each entity type.
        """
        definitions: List[Tuple[Type[CommonModelType], Type[enum.Enum[cdc_CommonEntityType]]]] = [
            (ArtifactType, cdc_ArtifactTypes),
            (ObservableType, cdc_ObservableTypes),
            (ThreatType, cdc_ThreatTypes),
            (ActorType, cdc_ActorTypes),
            (EventType, cdc_EventTypes),
            (DeviceType, cdc_DeviceTypes),
            (DetectionRuleType, cdc_DetectionRuleTypes),
            (DataFragmentType, cdc_DataFragmentTypes),
        ]

        for entity_type, type_definitions in definitions:
            for obj_type in type_definitions:
                obj_type_definition: cdc_CommonEntityType = obj_type.value
                entity_type.objects.update_or_create(
                    short_name=obj_type_definition.short_name,
                    defaults={
                        'name': obj_type_definition.name,
                        'description': obj_type_definition.description,
                        'value_example': obj_type_definition.value_example,
                        'regex': obj_type_definition.regex,
                        'default_attributes': obj_type_definition.default_attributes or {},
                        'icon': obj_type_definition.icon,
                        'nf_icon': obj_type_definition.nf_icon,
                        'type_hints': obj_type_definition.type_hints or {},
                    }
                )
