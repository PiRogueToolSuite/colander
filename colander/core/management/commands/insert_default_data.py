from django.core.management.base import BaseCommand, CommandError
import pkg_resources
import json

from colander.core.models import ArtifactType, ObservableType, ThreatType, ActorType, EventType, DeviceType, DetectionRuleType


class Command(BaseCommand):
    help = 'Insert default data.'

    def handle(self, *args, **options):
        definitions = [
            (ArtifactType, 'data/artifact_types.json'),
            (ObservableType, 'data/observable_types.json'),
            (ThreatType, 'data/threat_types.json'),
            (ActorType, 'data/actor_types.json'),
            (EventType, 'data/event_types.json'),
            (DeviceType, 'data/device_types.json'),
            (DetectionRuleType, 'data/detection_rule_types.json'),
        ]

        resource_package = __name__

        for obj, data_file in definitions:
            types_file = pkg_resources.resource_stream(resource_package, data_file)
            obj_types = json.load(types_file)
            for obj_type in obj_types:
                obj.objects.update_or_create(
                    short_name=obj_type.get('short_name'),
                    defaults={
                        'name': obj_type.get('name'),
                        'description': obj_type.get('description'),
                        'svg_icon': obj_type.get('svg_icon'),
                        'nf_icon': obj_type.get('nf_icon'),
                        'stix2_type': obj_type.get('stix2_type'),
                        'stix2_value_field_name': obj_type.get('stix2_value_field_name'),
                        'stix2_pattern': obj_type.get('stix2_pattern'),
                        'stix2_pattern_type': obj_type.get('stix2_pattern_type'),
                    }
                )
