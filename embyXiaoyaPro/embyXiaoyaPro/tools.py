import hashlib


def sha256_hash(text):
    hhh = hashlib.sha256()
    hhh.update(text.encode("utf-8"))
    return hhh.hexdigest()
