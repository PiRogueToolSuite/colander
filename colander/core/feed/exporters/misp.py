from colander_data_converter.base.models import ColanderFeed
from colander_data_converter.converters.misp.converter import MISPConverter
from pymisp import MISPOrganisation

from colander.core.feed.serializers import FullOutgoingFeedSerializer
from colander.core.models import EntityExportFeed


class MISPFeedExporter:
    def __init__(self, feed: EntityExportFeed):
        self.feed = feed

    def export(self):
        s = FullOutgoingFeedSerializer(self.feed)
        colander_feed = ColanderFeed.load(s.data)
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
