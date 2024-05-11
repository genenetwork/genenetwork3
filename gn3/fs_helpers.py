"""Procedures that operate on files/ directories"""
import errno
import hashlib
import json
import os
import random
import string
import tarfile

from functools import partial
from typing import Dict
from typing import List
from typing import ValuesView
from werkzeug.utils import secure_filename

from flask import current_app

def get_tmpdir() -> str:
    """Get the temp directory from the FLASK tmpdir setting. If it is not set, set it to /tmp. Note
    that the app should check for environment settings to initialize its TMPDIR.
    """
    tmpdir = current_app.config.get("TMPDIR")
    if not tmpdir:
        tmpdir = "/tmp"
    if not os.path.isdir(tmpdir):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), f"TMPDIR {tmpdir} is not a valid directory")

    return tmpdir

def assert_path_exists(path: str, throw_error: bool = True) -> bool:
    """Throw error if any of them do not exist."""
    if not os.path.isfile(path):
        if throw_error:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)
        else:
            return False
    return True

def assert_paths_exist(paths: ValuesView, throw_error: bool = True) -> bool:
    """Given a list of PATHS, throw error if any of them do not exist."""
    for path in paths:
        assert_path_exists(path,throw_error)
    return True

def get_hash_of_files(files: List[str]) -> str:
    """Given a list of valid of FILES, return their hash as a string"""
    md5hash = hashlib.md5()
    for file_path in sorted(files):
        if not os.path.exists(file_path):
            raise FileNotFoundError
        with open(file_path, "rb") as file_:
            for buf in iter(partial(file_.read, 4096), b''):
                md5hash.update(bytearray(
                    hashlib.md5(buf).hexdigest(), "utf-8"))
    return md5hash.hexdigest()


def get_dir_hash(directory: str) -> str:
    """Return the hash of a DIRECTORY"""
    if not os.path.exists(directory):
        raise FileNotFoundError
    all_files = [
        os.path.join(root, names) for root, _, files in os.walk(directory)
        for names in sorted(files)
    ]
    return get_hash_of_files(all_files)


def jsonfile_to_dict(json_file: str) -> Dict:
    """Give a JSON_FILE, return a python dict"""
    with open(json_file, encoding="utf-8") as _file:
        data = json.load(_file)
        return data
    raise FileNotFoundError


def generate_random_n_string(n_length: int) -> str:
    """Generate a random string that is N chars long"""
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for _ in range(n_length))


def extract_uploaded_file(gzipped_file,
                          target_dir: str,
                          token: str = "") -> Dict:
    """Get the (directory) hash of extracted contents of GZIPPED_FILE; and move
contents to TARGET_DIR/<dir-hash>.

    """
    if not token:
        token = (f"{generate_random_n_string(6)}-"
                 f"{generate_random_n_string(6)}")
    tar_target_loc = os.path.join(target_dir, token,
                                  secure_filename(gzipped_file.filename))
    try:
        if not os.path.exists(os.path.join(target_dir, token)):
            os.mkdir(os.path.join(target_dir, token))
        gzipped_file.save(tar_target_loc)
        # Extract to "tar_target_loc/token"
        with tarfile.open(tar_target_loc) as tar:
            tar.extractall(path=os.path.join(target_dir, token))
    # pylint: disable=W0703
    except Exception:
        return {"status": 128, "error": "gzip failed to unpack file"}
    return {"status": 0, "token": token}


# pylint: disable=unused-argument
def cache_ipfs_file(ipfs_file: str,
                    cache_dir: str,
                    ipfs_addr: str = "/ip4/127.0.0.1/tcp/5001") -> str:
    """Check if a file exists in cache; if it doesn't, cache it.  Return the
    cached file location

    """
    # IPFS httpclient doesn't work in Python3
    return ""
