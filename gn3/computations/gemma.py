"""Procedures related gemma computations"""


def generate_pheno_txt_file(trait_filename: str,
                            values: str,
                            tmpdir: str = "/tmp") -> str:
    """Given VALUES, and TMPDIR, generate a valide traits file"""
    with open(f"{tmpdir}/gn2/{trait_filename}", "w") as _file:
        for value in values:
            if value == "x":
                _file.write("NA\n")
            else:
                _file.write(f"{value}\n")
    return f"{tmpdir}/gn2/{trait_filename}"
