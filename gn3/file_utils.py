"""Procedures that operate on files/ directories"""
import hashlib
import json
import os

from functools import partial
from typing import Dict


def get_dir_hash(directory: str) -> str:
    """Return the hash of a DIRECTORY"""
    md5hash = hashlib.md5()
    if not os.path.exists(directory):
        raise FileNotFoundError
    for root, _, files in os.walk(directory):
        for names in sorted(files):
            file_path = os.path.join(root, names)
            with open(file_path, "rb") as file_:
                for buf in iter(partial(file_.read, 4096), b''):
                    md5hash.update(bytearray(hashlib.md5(buf).hexdigest(),
                                             "utf-8"))
    return md5hash.hexdigest()


def lookup_file(environ_var: str,
                root_dir: str,
                file_name: str) -> str:
    """Look up FILE_NAME in the path defined by ENVIRON_VAR/ROOT_DIR/; If
ENVIRON_VAR/ROOT_DIR/FILE_NAME does not exist, raise an exception.
Otherwise return ENVIRON_VAR/ROOT_DIR/FILE_NAME.

    """
    _dir = os.environ.get(environ_var)
    if _dir:
        _file = os.path.join(_dir, root_dir, file_name)
        if os.path.isfile(_file):
            return _file
    raise FileNotFoundError


def jsonfile_to_dict(json_file: str) -> Dict:
    """Give a JSON_FILE, return a python dict"""
    with open(json_file) as _file:
        data = json.load(_file)
        return data
    raise FileNotFoundError
