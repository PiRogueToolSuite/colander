import hashlib

import magic


def hash_file(file):
    h_sha256 = hashlib.sha256()
    h_sha1 = hashlib.sha1()
    h_md5 = hashlib.md5()
    chunk = 0
    size = 0
    while chunk != b'':
        chunk = file.read(4096)
        size += len(chunk)
        h_sha256.update(chunk)
        h_sha1.update(chunk)
        h_md5.update(chunk)
    return h_sha256.hexdigest(), h_sha1.hexdigest(), h_md5.hexdigest(), size


def get_upload_file_mime_type(file):
    """
    Get MIME by reading the header of the file
    """
    initial_pos = file.tell()
    file.seek(0)
    mime_type = magic.from_buffer(file.read(2048), mime=True)
    file.seek(initial_pos)
    return mime_type
