from typing import List, Type

from colander_data_converter.base.models import ColanderFeed
from colander_data_converter.converters.misp.converter import MISPConverter
from pymisp import MISPOrganisation

from colander.core.exporters.json import JsonCaseExporter
from colander.core.models import Case, Entity, EntityOutgoingFeed


class MISPCaseExporter:
    case: Case

    def __init__(self, case: Case, feed: EntityOutgoingFeed, entities: List[Type[Entity]]):
        self.case = case
        self.feed = feed
        self.input_entities = entities

    def export(self):
        exporter = JsonCaseExporter(self.case, self.input_entities)
        export = exporter.export()
        colander_feed = ColanderFeed.load(export)
        misp_feed = MISPConverter.colander_to_misp(colander_feed)
        if len(misp_feed or []) == 1:
            misp_event = misp_feed[0]
        else:
            return []
        org = MISPOrganisation()
        org.from_dict(
            **{
                "name": self.feed.misp_org_name,
                "uuid": self.feed.misp_org_id,
            }
        )
        misp_event.orgc = org
        return misp_event.to_feed()
