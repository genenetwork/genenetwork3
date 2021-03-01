"""Procedures that operate on files/ directories"""
import hashlib
import json
import os
import random
import string
import tarfile

from functools import partial
from typing import Dict
from werkzeug.utils import secure_filename
from gn3.settings import APP_DEFAULTS


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
    _dir = APP_DEFAULTS.get(environ_var,
                            os.environ.get(environ_var))
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


def generate_random_n_string(n_length: int) -> str:
    """Generate a random string that is N chars long"""
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for _ in range(n_length))


def extract_uploaded_file(gzipped_file, target_dir: str, token="") -> Dict:
    """Get the (directory) hash of extracted contents of GZIPPED_FILE; and move
contents to TARGET_DIR/<dir-hash>.

    """
    if not token:
        token = (f"{generate_random_n_string(6)}-"
                 f"{generate_random_n_string(6)}")
    tar_target_loc = os.path.join(
        target_dir,
        token,
        secure_filename(gzipped_file.filename))
    try:
        if not os.path.exists(os.path.join(target_dir, token)):
            os.mkdir(os.path.join(target_dir, token))
        gzipped_file.save(tar_target_loc)
        # Extract to "tar_target_loc/token"
        tar = tarfile.open(tar_target_loc)
        tar.extractall(path=tar_target_loc)
        tar.close()
    # pylint: disable=W0703
    except Exception:
        return {"status": 128, "error": "gzip failed to unpack file"}
    return {"status": 0, "token": token}
