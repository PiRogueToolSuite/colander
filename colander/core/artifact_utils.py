import os

from django.core.files import File

from colander.core.models import Artifact
from colander.core.utils import hash_file


def import_file_as_artifact(input_file, owner, case, artifact_type, name, mimetype, tlp, pap) -> Artifact:
    sha256, sha1, md5, size = hash_file(input_file)
    input_file.seek(0)
    input_file.seek(0, os.SEEK_END)
    size_in_bytes = input_file.tell()
    input_file.seek(0)
    artifact = Artifact(
        type=artifact_type,
        name=name,
        original_name=name,
        owner=owner,
        case=case,
        tlp=tlp,
        pap=pap,
        mime_type=mimetype,
        sha1=sha1,
        sha256=sha256,
        md5=md5,
        size_in_bytes=size_in_bytes,
        file=File(file=input_file, name=name)
    )
    artifact.save()
    return artifact
