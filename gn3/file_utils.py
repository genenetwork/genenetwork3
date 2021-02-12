"""Procedures that operate on files/ directories"""
import hashlib
import os

from functools import partial


def get_dir_hash(directory: str) -> str:
    """Return the hash of a DIRECTORY"""
    md5hash = hashlib.md5()
    if not os.path.exists(directory):
        raise FileNotFoundError
    for root, _, files in os.walk(directory):
        for names in files:
            file_path = os.path.join(root, names)
            with open(file_path, "rb") as file_:
                for buf in iter(partial(file_.read, 4096), b''):
                    md5hash.update(bytearray(hashlib.md5(buf).hexdigest(),
                                             "utf-8"))
    return md5hash.hexdigest()
