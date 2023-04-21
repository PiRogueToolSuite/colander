import pytz
import logging
from datetime import datetime, timedelta
from django.core.files import File

from colander.core.models import Artifact, UploadRequest
from colander.core.utils import hash_file

logger = logging.getLogger(__name__)

def clean_upload_request_orphans():
    logger.info("clean_upload_request_orphans : aborted UploadRequest (no target Artifact id)")
    # To clean:
    # UploadRequest that:
    #   - is older than 1 day
    #   - has empty or null target_artifact_id
    #   - is in any state
    fence_date = datetime.now(tz=pytz.UTC) - timedelta(days=4)
    UploadRequest.objects.filter(created_at__lt=fence_date, target_artifact_id__isnull=True).delete()

    logger.info("clean_upload_request_orphans : UploadRequest without existing Artifact id")
    uprs = UploadRequest.objects.filter(created_at__lt=fence_date)
    for upr in uprs:
        try:
            a = Artifact.objects.get(pk=str(upr.target_artifact_id))
        except Artifact.DoesNotExist:
            upr.delete()

def compute_non_signed_artifacts(batch=1):
    logger.info("compute_non_signed_artifacts")
    fence_date = datetime.now(tz=pytz.UTC) - timedelta(hours=1)
    artifacts = Artifact.objects.filter( sha256__isnull=True, created_at__lt=fence_date )[:batch]
    for artifact in artifacts:
        logger.info(f"compute_non_signed_artifacts[{artifact.id}]: processing ...")
        upr = None
        try:
            upr = UploadRequest.objects.get(target_artifact_id=str(artifact.id))
            logger.info(f"compute_non_signed_artifacts[{artifact.id}]: upr:{upr.name} artifact:{artifact.name}")
            with open(upr.path, 'rb') as f:
                sha256, sha1, md5, size = hash_file(f)
            logger.info(f"compute_non_signed_artifacts[{artifact.id}]: sha256:{sha256} sha1:{sha1} md5:{sha1} size:{sha1}")
            artifact.file = File(file=open(upr.path, 'rb'), name=artifact.name)
            artifact.sha256 = sha256
            artifact.sha1 = sha1
            artifact.md5 = md5
            logger.info(f"compute_non_signed_artifacts[{artifact.id}]: saving ...")
            artifact.save()
            logger.info(f"compute_non_signed_artifacts[{artifact.id}]: saved.")
            logger.info(f"compute_non_signed_artifacts[{artifact.id}]: cleaning...")
            upr.delete()
            logger.info(f"compute_non_signed_artifacts[{artifact.id}]: cleaned.")
        except UploadRequest.DoesNotExist:
            # Will be cleaned by cleanup orphans cron
            logger.info(f"compute_non_signed_artifacts[{artifact.id}]: no associated UploadRequest. Skip.")
        except FileNotFoundError:
            logger.info(f"compute_non_signed_artifacts[{artifact.id}]: file is no more available: {upr.path}. Cleaning.")
            artifact.delete()
            upr.delete()
            # TODO: Log into centry

