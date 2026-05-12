import logging
import re
from tempfile import NamedTemporaryFile

import mandolin_python_client
from django.conf import settings
from django.core.files.base import ContentFile
from mandolin_python_client import ThumbnailStrategy, AnalysisTikaResult, AnalyzerResultClamAVResult
from mandolin_python_client.rest import ApiException

from colander.core.models import Artifact

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
                api_response: bytearray = api_instance.generate_thumbnail_converter_thumbnail_post(
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


def _mandolin_tika_analysis(artifact: Artifact, mandolin_configuration) -> AnalysisTikaResult | None:
    with NamedTemporaryFile(suffix=artifact.original_name) as artifact_file:
        for chunk in artifact.file.chunks():
            artifact_file.write(chunk)
        artifact_file.flush()
        artifact_file.seek(0)
        with mandolin_python_client.ApiClient(mandolin_configuration) as api_client:
            api_instance = mandolin_python_client.AnalyzersApi(api_client)
            file = artifact_file.name
            try:
                response = api_instance.analyze_with_tika_analyzer_tika_post(file, _request_timeout=5 * 60)
                return response
            except ApiException as e:
                logger.error(e)
    return None


def _mandolin_clamav_analysis(artifact: Artifact, mandolin_configuration) -> AnalyzerResultClamAVResult | None:
    with NamedTemporaryFile(suffix=artifact.original_name) as artifact_file:
        for chunk in artifact.file.chunks():
            artifact_file.write(chunk)
        artifact_file.flush()
        artifact_file.seek(0)
        with mandolin_python_client.ApiClient(mandolin_configuration) as api_client:
            api_instance = mandolin_python_client.AnalyzersApi(api_client)
            file = artifact_file.name
            try:
                response = api_instance.analyze_with_clamav_analyzer_clamav_post(file, _request_timeout=5 * 60)
                return response.processors.get("clamav", None) if response.processors else None
            except ApiException as e:
                logger.error(e)
    return None


def analyze_artifact(artifact_id: str):
    if not settings.USE_MANDOLIN:
        logger.info('Mandolin is disabled')
        return

    artifact = Artifact.objects.get(id=artifact_id)

    # Call Mandolin to extract the artifact content
    mandolin_configuration = mandolin_python_client.Configuration(
        host=settings.MANDOLIN_BASE_URL
    )

    # Call Mandolin to automatically generate the thumbnail of pictures
    _mandolin_thumbnail(artifact, mandolin_configuration)

    # Call other analyzers
    tika_analysis = _mandolin_tika_analysis(artifact, mandolin_configuration)
    clamav_analysis = _mandolin_clamav_analysis(artifact, mandolin_configuration)
    analysis = {
        "success": bool(tika_analysis) or bool(clamav_analysis),
        "content": None,
        "processors": {}
    }
    if tika_analysis:
        analysis["content"] = tika_analysis.content
        analysis["processors"]["tika"] = tika_analysis.processors["tika"].to_dict()

    if clamav_analysis:
        analysis["processors"]["clamav"] = clamav_analysis.to_dict()
        if clamav_analysis.analysis and clamav_analysis.analysis.infected:
            artifact.add_attribute("is_malicious", True)

    artifact.analysis = analysis
    artifact.save()
