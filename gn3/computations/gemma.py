"""Procedures related gemma computations"""
import os
import random
import string

from base64 import b64encode
from hashlib import md5
from typing import List
from typing import ValuesView

def generate_random_n_string(n_length: int) -> str:
    """Generate a random string that is N chars long"""
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for _ in range(n_length))


def generate_hash_of_string(unhashed_str: str) -> str:
    """Given an UNHASHED_STRING, generate it's md5 hash while removing the '==' at
the end"""
    hashed_str = md5(unhashed_str.encode("utf-8")).digest()
    return b64encode(hashed_str).decode("utf-8").replace("==", "")


def generate_pheno_txt_file(trait_filename: str,
                            values: List,
                            tmpdir: str = "/tmp") -> str:
    """Given VALUES, and TMPDIR, generate a valid traits file"""
    if not os.path.isdir(f"{tmpdir}/gn2/"):
        os.mkdir(f"{tmpdir}/gn2/")
    ext = trait_filename.partition(".")[-1]
    if ext:
        trait_filename = trait_filename.replace(f".{ext}", "")
        ext = f".{ext}"
    trait_filename += f"_{generate_hash_of_string(''.join(values))}{ext}"
    # Early return if this already exists!
    if os.path.isfile(f"{tmpdir}/gn2/{trait_filename}"):
        return f"{tmpdir}/gn2/{trait_filename}"
    with open(f"{tmpdir}/gn2/{trait_filename}", "w") as _file:
        for value in values:
            if value == "x":
                _file.write("NA\n")
            else:
                _file.write(f"{value}\n")
    return f"{tmpdir}/gn2/{trait_filename}"


def do_paths_exist(paths: ValuesView) -> bool:
    """Given a list of PATHS, return False if any of them do not exist."""
    for path in paths:
        if not os.path.isfile(path):
            return False
    return True
