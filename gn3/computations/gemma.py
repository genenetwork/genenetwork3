"""Procedures related gemma computations"""
import os

from base64 import b64encode
from hashlib import md5
from typing import Dict
from typing import List
from typing import Optional
from typing import ValuesView
from gn3.commands import compose_gemma_cmd
from gn3.file_utils import get_hash_of_files


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


def generate_gemma_computation_cmd(
        gemma_cmd: str, gemma_kwargs: Dict[str, str], output_file: str,
        gemma_wrapper_kwargs: Dict[str, str]) -> Optional[str]:
    """Create a computation cmd"""
    geno_filename = gemma_kwargs.get("geno_filename", "")
    trait_filename = gemma_kwargs.get("trait_filename")
    ext, snps_filename = geno_filename.partition(".")[-1], ""
    if geno_filename:
        snps_filename = geno_filename.replace(f".{ext}", "")
        snps_filename += f"_snps.{ext}"
    _kwargs = {"g": geno_filename, "p": trait_filename}
    _kwargs["a"] = snps_filename
    if not do_paths_exist(_kwargs.values()):  # Prevents injection!
        return None
    if _kwargs.get("lmm"):
        _kwargs["lmm"] = gemma_kwargs.get("lmm")
    return compose_gemma_cmd(gemma_wrapper_cmd=gemma_cmd,
                             gemma_wrapper_kwargs=gemma_wrapper_kwargs,
                             gemma_kwargs=_kwargs,
                             gemma_args=["-gk", ">", output_file])


# pylint: disable=R0913
def generate_gemma_cmd(gemma_cmd: str,
                       output_dir: str,
                       token: str,
                       gemma_kwargs: Dict,
                       gemma_wrapper_kwargs: Dict = None,
                       chromosomes: str = None) -> Dict:
    """Compute k values"""
    _hash = get_hash_of_files(
        [v for k, v in gemma_kwargs.items() if k in ["g", "p", "a", "c"]])
    if chromosomes:  # Only reached when calculating k-values
        gemma_wrapper_kwargs = {"loco": f"--input {chromosomes}"}
        _hash += f"-{generate_hash_of_string(chromosomes)[:6]}"
    _output_filename = f"{_hash}-output.json"
    return {
        "output_file":
        _output_filename,
        "gemma_cmd":
        compose_gemma_cmd(gemma_wrapper_cmd=gemma_cmd,
                          gemma_wrapper_kwargs=gemma_wrapper_kwargs,
                          gemma_kwargs=gemma_kwargs,
                          gemma_args=[
                              "-gk", ">",
                              (f"{output_dir}/"
                               f"{token}/{_output_filename}")
                          ])
    }
