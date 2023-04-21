import django.dispatch
from django.core.files import File
from django.dispatch import receiver
from threading import Thread

from colander.core.models import Artifact, UploadRequest
from colander.core.utils import hash_file

# Signal handling for processing (potentially) long tasks on Artifact
# - Computes hashes on real file
# - Computes signing attribute on Artifact
# - Transfers file content from UploadRequest to Artifact mini.io container
process_hash_and_signing = django.dispatch.Signal()

# Signal handling for cron execution
# Ensures no other cron process execute at the same time
execute_cron = django.dispatch.Signal()

@receiver(process_hash_and_signing)
def _signal_handling_process_hash_and_signing(sender, upload_request_id, **kwargs):
    print(f"process_hash_and_signing[{upload_request_id}]: scheduling ...")
    t = Thread(target=__threaded_artifact_process_hash_and_signing, args = (upload_request_id,))
    t.start()

@receiver(execute_cron)
def _signal_handling_execute_cron(sender, **kwargs):
    # Check for other execution
    # Check for 'minute' frame execution
    pass

def __threaded_artifact_process_hash_and_signing(upload_request_id):
    print(f"process_hash_and_signing[{upload_request_id}]: executing ...")
    upr = UploadRequest.objects.get(pk=upload_request_id)
    artifact = Artifact.objects.get(pk=upr.target_artifact_id)
    print(f"process_hash_and_signing[{upload_request_id}]: upr:{upr.name} artifact:{artifact.name}")
    with open(upr.path, 'rb') as f:
        sha256, sha1, md5, size = hash_file(f)
    print(f"process_hash_and_signing[{upload_request_id}]: sha256:{sha256} sha1:{sha1} md5:{sha1} size:{sha1}")
    artifact.file = File(file=open(upr.path, 'rb'), name=artifact.name)
    artifact.sha256 = sha256
    artifact.sha1 = sha1
    artifact.md5 = md5
    print(f"process_hash_and_signing[{upload_request_id}]: saving ...")
    artifact.save()
    print(f"process_hash_and_signing[{upload_request_id}]: saved.")
    print(f"process_hash_and_signing[{upload_request_id}]: cleaning...")
    upr.delete()
    print(f"process_hash_and_signing[{upload_request_id}]: cleaned.")
