import logging
from tempfile import NamedTemporaryFile
import re

import mandolin_python_client
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from mandolin_python_client import ThumbnailStrategy
from mandolin_python_client.rest import ApiException

from elasticsearch_dsl import Index

from colander.core.models import Artifact, ArtifactAnalysis

logger = logging.getLogger(__name__)


def remove_duplicates_regex(s):
    try:
        tmp = re.sub(r' {2,}', ' ', s)
        tmp = re.sub(r'\t', ' ', tmp)
        tmp = re.sub(r'\n{2,}', '\n', tmp)
        tmp = re.sub(r'( \n){2,}', '\n', tmp)
        return re.sub(r'(\n ){2,}', '\n', tmp).strip()
    except TypeError:
        pass
    return s


def _mandolin_thumbnail(artifact: Artifact, mandolin_configuration):
    if not artifact.mime_type.startswith('image'):
        return
    with NamedTemporaryFile(suffix=artifact.original_name) as artifact_file:
        for chunk in artifact.file.chunks():
            artifact_file.write(chunk)
        artifact_file.flush()
        artifact_file.seek(0)
        with mandolin_python_client.ApiClient(mandolin_configuration) as api_client:
            api_instance = mandolin_python_client.ConvertersApi(api_client)
            try:
                api_response:bytearray = api_instance.generate_thumbnail_converter_thumbnail_post(
                    artifact_file.name,
                    strategy=ThumbnailStrategy.FIT,
                    width=256,
                    height=256,
                    _request_timeout=30,
                )
                if len(api_response) > 0:
                    artifact.thumbnail = ContentFile(api_response, name=artifact_file.name)
                    artifact.save()
            except ApiException as e:
                logger.error(e)


def _mandolin_tika_analysis(artifact: Artifact, mandolin_configuration) -> ArtifactAnalysis | None:
    with NamedTemporaryFile(suffix=artifact.original_name) as artifact_file:
        for chunk in artifact.file.chunks():
            artifact_file.write(chunk)
        artifact_file.flush()
        artifact_file.seek(0)
        with mandolin_python_client.ApiClient(mandolin_configuration) as api_client:
            api_instance = mandolin_python_client.AnalyzersApi(api_client)
            file = artifact_file.name
            try:
                api_response = api_instance.analyze_with_tika_analyzer_tika_post(file, _request_timeout=5 * 60)
                analysis = ArtifactAnalysis()
                analysis.owner = str(artifact.owner_id)
                analysis.case_id = str(artifact.case_id)
                analysis.artifact_id = str(artifact.id)
                analysis.analysis_date = timezone.now()
                analysis.content = api_response.content
                analysis.success = api_response.success
                analysis.processors = api_response.processors
                return analysis
            except ApiException as e:
                logger.error(e)
    return None


def analyze_artifact(artifact_id: str):
    if not settings.USE_MANDOLIN:
        logger.info('Mandolin is disabled')
        return

    # Prepare the ElasticSearch index in which the analysis will be saved
    from elasticsearch_dsl import connections
    connections.create_connection(hosts=['elasticsearch'], timeout=20)
    artifact = Artifact.objects.get(id=artifact_id)
    index_name = artifact.get_es_index()
    try:
        index = Index(index_name)
        if index.exists():
            index.delete()
        if not index.exists():
            index.create()
            ArtifactAnalysis.init(index=index_name)
    except Exception as e:
        logger.exception(e)
        return

    # Call Mandolin to extract the artifact content
    mandolin_configuration = mandolin_python_client.Configuration(
        host=settings.MANDOLIN_BASE_URL
    )
    if analysis := _mandolin_tika_analysis(artifact, mandolin_configuration):
        analysis.save(index=index_name)

    # Call Mandolin to automatically generate the thumbnail of pictures
    _mandolin_thumbnail(artifact, mandolin_configuration)
