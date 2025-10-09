from colander.core.feed.serializers import FullOutgoingFeedSerializer
from colander.core.models import EntityExportFeed


class JsonFeedExporter:

    def __init__(self, feed: EntityExportFeed):
        self.feed = feed

    def export(self):
        return FullOutgoingFeedSerializer(self.feed).data
