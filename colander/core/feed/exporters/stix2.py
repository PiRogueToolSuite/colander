from colander_data_converter.base.models import ColanderFeed
from colander_data_converter.converters.stix2.converter import Stix2Converter

from colander.core.feed.serializers import EntityFeedContentSerializer
from colander.core.models import Case, EntityExportFeed


class Stix2FeedExporter:
    case: Case
    __entities: dict = None
    __relations: dict = None

    def __init__(self, feed: EntityExportFeed):
        self.feed = feed

    def export(self):
        s = EntityFeedContentSerializer(self.feed)
        colander_feed = ColanderFeed.load(s.data)
        stix2_bundle = Stix2Converter.colander_to_stix2(colander_feed)
        return stix2_bundle.model_dump()
