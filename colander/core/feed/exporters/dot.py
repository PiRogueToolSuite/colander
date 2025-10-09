from io import StringIO

from colander_data_converter.base.models import ColanderFeed
from colander_data_converter.converters.misp.converter import MISPConverter
from colander_data_converter.exporters.graphviz import GraphvizExporter
from colander_data_converter.exporters.mermaid import MermaidExporter
from pymisp import MISPOrganisation

from colander.core.feed.serializers import FullOutgoingFeedSerializer
from colander.core.models import EntityExportFeed


class DotFeedExporter:
    def __init__(self, feed: EntityExportFeed):
        self.feed = feed

    def export(self):
        s = FullOutgoingFeedSerializer(self.feed)
        colander_feed = ColanderFeed.load(s.data)
        exporter = GraphvizExporter(colander_feed)
        io = StringIO()
        exporter.export(io)
        io.seek(0)
        return io.read()
