from io import StringIO

from colander_data_converter.base.models import ColanderFeed
from colander_data_converter.converters.misp.converter import MISPConverter
from colander_data_converter.exporters.mermaid import MermaidExporter
from pymisp import MISPOrganisation

from colander.core.feed.serializers import EntityFeedContentSerializer
from colander.core.models import EntityExportFeed


class MermaidFeedExporter:
    def __init__(self, feed: EntityExportFeed):
        self.feed = feed

    def export(self):
        s = EntityFeedContentSerializer(self.feed)
        colander_feed = ColanderFeed.load(s.data)
        exporter = MermaidExporter(colander_feed)
        io = StringIO()
        exporter.export(io)
        io.seek(0)
        return io.read()
