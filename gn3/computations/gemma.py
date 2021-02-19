"""Procedures related gemma computations"""
import random
import string


def generate_random_n_string(n_length):
    """Generate a random string that is N chars long"""
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for _ in range(n_length))


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
