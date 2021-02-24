"""Procedures related gemma computations"""
import random
import string

from base64 import b64encode
from hashlib import md5

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
                            values: str,
                            tmpdir: str = "/tmp") -> str:
    """Given VALUES, and TMPDIR, generate a valide traits file"""
    trait_filename += f"_{generate_random_n_string(6)}"
    with open(f"{tmpdir}/gn2/{trait_filename}", "w") as _file:
        for value in values:
            if value == "x":
                _file.write("NA\n")
            else:
                _file.write(f"{value}\n")
    return f"{tmpdir}/gn2/{trait_filename}"
