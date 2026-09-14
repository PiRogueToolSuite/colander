import time
from threading import Thread

import django.dispatch
from django.core.files import File
from django.dispatch import receiver
from django_q.tasks import async_task

from colander.core.models import Artifact, UploadRequest, DroppedFile
from colander.core.tasks.artifact_tasks import analyze_artifact
from colander.core.utils import hash_file

import logging
logger = logging.getLogger(__name__)

# Signal handling for processing (potentially) long tasks on Artifact
# - Computes hashes on real file
# - Computes signing attribute on Artifact
# - Transfers file content from UploadRequest to Artifact mini.io container
process_hash_and_signing = django.dispatch.Signal()

# Signal handling for cron execution
# Ensures no other cron process execute at the same time
execute_cron = django.dispatch.Signal()

# Signal handling for Dropped File conversion (allow multiple)
process_dropped_files_conversion = django.dispatch.Signal()

# Signal handling the final save of an artifact as it's ready to be processed
artifact_ready_for_analysis = django.dispatch.Signal()

@receiver(process_hash_and_signing)
def _signal_handling_process_hash_and_signing(sender, upload_request_id, **kwargs):
    logger.debug("process_hash_and_signing[%s]: scheduling ...", upload_request_id)
    t = Thread(target=__threaded_artifact_process_hash_and_signing, args = (upload_request_id,))
    t.start()


@receiver(execute_cron)
def _signal_handling_execute_cron(sender, **kwargs):
    # Check for other execution
    # Check for 'minute' frame execution
    pass


@receiver(process_dropped_files_conversion)
def _signal_handling_convert_dropped_files(sender, dropped_file_ids, **kwargs):
    logger.debug("Convert dropped files: %s ...", dropped_file_ids)
    t = Thread(target=__threaded_dropped_files_conversion, args = (dropped_file_ids,))
    t.start()


def __threaded_dropped_files_conversion(dropped_file_ids):
    logger.debug("dropped_files_conversion[%s]: starting ...", dropped_file_ids)
    for df_id in dropped_file_ids:
        logger.debug("DroppedFile conversion[%s]", df_id)
        dropped_file = DroppedFile.objects.get(pk=df_id)
        artifact = Artifact.objects.get(pk=dropped_file.target_artifact_id)
        with dropped_file.file.open('rb') as f:
            sha256, sha1, md5, size = hash_file(f)
        logger.debug("DroppedFile conversion[%s]: sha256:%s sha1:%s md5:%s size:%s",
                     df_id, sha256, sha1, md5, size)
        artifact.file = File(file=dropped_file.file.open('rb'), name=dropped_file.filename)
        artifact.sha256 = sha256
        artifact.sha1 = sha1
        artifact.md5 = md5
        artifact.save()
        artifact_ready_for_analysis.send(
            sender='signaling_hub.__threaded_dropped_files_conversion',
            artifact_id=str(artifact.id)
        )
        dropped_file.delete()


def __threaded_artifact_process_hash_and_signing(upload_request_id):
    logger.debug("process_hash_and_signing[%s]: executing ...", upload_request_id)
    upr = UploadRequest.objects.get(pk=upload_request_id)
    artifact = Artifact.objects.get(pk=upr.target_entity_id)
    logger.debug("process_hash_and_signing[%s]: upr:%s artifact:%s",
                 upload_request_id, upr.name, artifact.name)
    with open(upr.path, 'rb') as f:
        sha256, sha1, md5, size = hash_file(f)
    logger.debug("process_hash_and_signing[%s]: sha256:%s sha1:%s md5:%s size:%s",
                 upload_request_id, sha256, sha1, md5, size)
    artifact.file = File(file=open(upr.path, 'rb'), name=artifact.name)
    artifact.sha256 = sha256
    artifact.sha1 = sha1
    artifact.md5 = md5
    logger.debug("process_hash_and_signing[%s]: saving ...", upload_request_id)
    artifact.save()
    artifact_ready_for_analysis.send(
        sender='signaling_hub.__threaded_artifact_process_hash_and_signing',
        artifact_id=str(artifact.id)
    )
    logger.debug("process_hash_and_signing[%s]: saved.", upload_request_id)
    logger.debug("process_hash_and_signing[%s]: cleaning...", upload_request_id)
    upr.delete()
    logger.debug("process_hash_and_signing[%s]: cleaned.", upload_request_id)


@receiver(artifact_ready_for_analysis)
def _signal_handler_trigger_artifact_analysis(sender, artifact_id, **kwargs):
    async_task(analyze_artifact, artifact_id)
