from colander.core.feed.serializers import EntityFeedContentSerializer
from colander.core.models import EntityExportFeed


class JsonFeedExporter:

    def __init__(self, feed: EntityExportFeed):
        self.feed = feed

    def export(self):
        return EntityFeedContentSerializer(self.feed).data
