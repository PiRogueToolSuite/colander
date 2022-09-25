import hashlib


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
