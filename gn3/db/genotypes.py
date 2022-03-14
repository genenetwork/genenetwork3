"""Genotype utilities"""

import os
import gzip

from gn3.settings import GENOTYPE_FILES

def build_genotype_file(
        geno_name: str, base_dir: str = GENOTYPE_FILES,
        extension: str = "geno"):
    """Build the absolute path for the genotype file."""
    return f"{os.path.abspath(base_dir)}/{geno_name}.{extension}"

def load_genotype_samples(genotype_filename: str, file_type: str = "geno"):
    """
    Load sample of samples from genotype files.

    DESCRIPTION:
    Traits can contain a varied number of samples, some of which do not exist in
    certain genotypes. In order to compute QTLs, GEMMAs, etc, we need to ensure
    to pick only those samples that exist in the genotype under consideration
    for the traits used in the computation.

    This function loads a list of samples from the genotype files for use in
    filtering out unusable samples.


    PARAMETERS:
    genotype_filename: The absolute path to the genotype file to load the
        samples from.
    file_type: The type of file. Currently supported values are 'geno' and
        'plink'.
    """
    file_type_fns = {
        "geno": __load_genotype_samples_from_geno,
        "plink": __load_genotype_samples_from_plink
    }
    return file_type_fns[file_type](genotype_filename)

def __load_genotype_samples_from_geno(genotype_filename: str):
    """
    Helper function for `load_genotype_samples` function.

    Loads samples from '.geno' files.
    """
    def __remove_comments_and_empty_lines__(rows):
        return(
            line for line in rows
            if line and not line.startswith(("#", "@")))

    gzipped_filename = f"{genotype_filename}.gz"
    if os.path.isfile(gzipped_filename):
        with gzip.open(gzipped_filename) as gz_genofile:
            rows = __remove_comments_and_empty_lines__(gz_genofile.readlines())
    else:
        with open(genotype_filename, encoding="utf8") as genofile:
            rows = __remove_comments_and_empty_lines__(genofile.readlines())

    headers = next(rows).split() # type: ignore[arg-type]
    if headers[3] == "Mb":
        return tuple(headers[4:])
    return tuple(headers[3:])

def __load_genotype_samples_from_plink(genotype_filename: str):
    """
    Helper function for `load_genotype_samples` function.

    Loads samples from '.plink' files.
    """
    with open(genotype_filename, encoding="utf8") as genofile:
        return tuple(line.split()[1] for line in genofile)

def parse_genotype_labels(lines: list):
    """
    Parse label lines into usable genotype values

    DESCRIPTION:
    Reworks
    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/utility/gen_geno_ob.py#L75-L93
    """
    acceptable_labels = ["name", "filler", "type", "mat", "pat", "het", "unk"]
    def __parse_label(line):
        label, value = [l.strip() for l in line[1:].split(":")]
        if label not in acceptable_labels:
            return None
        if label == "name":
            return ("group", value)
        return (label, value)
    return tuple(
        item for item in (__parse_label(line) for line in lines)
        if item is not None)

def parse_genotype_header(line: str, parlist: tuple = tuple()):
    """
    Parse the genotype file header line

    DESCRIPTION:
    Reworks
    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/utility/gen_geno_ob.py#L94-L114
    """
    items = [item.strip() for item in line.split("\t")]
    mbmap = "Mb" in items
    prgy = ((parlist + tuple(items[4:])) if mbmap
            else (parlist + tuple(items[3:])))
    return (
        ("Mbmap", mbmap),
        ("cm_column", items.index("cM")),
        ("mb_column", None if not mbmap else items.index("Mb")),
        ("prgy", prgy),
        ("nprgy", len(prgy)))

def parse_genotype_marker(line: str, geno_obj: dict, parlist: tuple):
    """
    Parse a data line in a genotype file

    DESCRIPTION:
    Reworks
    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/utility/gen_geno_ob.py#L143-L190
    """
    # pylint: disable=W0702
    marker_row = [item.strip() for item in line.split("\t")]
    geno_table = {
        geno_obj["mat"]: -1, geno_obj["pat"]: 1, geno_obj["het"]: 0,
        geno_obj["unk"]: "U"
    }
    start_pos = 4 if geno_obj["Mbmap"] else 3
    if len(parlist) > 0:
        start_pos = start_pos + 2

    alleles = marker_row[start_pos:]
    genotype = tuple(
        (geno_table[allele] if allele in geno_table else "U")
        for allele in alleles)
    if len(parlist) > 0:
        genotype = (-1, 1) + genotype
    try:
        cm_val = float(geno_obj["cm_column"])
    except:
        if geno_obj["Mbmap"]:
            cm_val = float(geno_obj["mb_column"])
        else:
            cm_val = 0
    return (
        ("chr", marker_row[0]),
        ("name", marker_row[1]),
        ("cM", cm_val),
        ("Mb", float(geno_obj["mb_column"]) if geno_obj["Mbmap"] else None),
        ("genotype", genotype))

def build_genotype_chromosomes(geno_obj, markers):
    """
    Build up the chromosomes from the given markers and partially built geno
    object
    """
    mrks = [dict(marker) for marker in markers]
    chr_names = {marker["chr"] for marker in mrks}
    return tuple((
        ("name", chr_name), ("mb_exists", geno_obj["Mbmap"]), ("cm_column", 2),
        ("mb_column", geno_obj["mb_column"]),
        ("loci", tuple(marker for marker in mrks if marker["chr"] == chr_name)))
                 for chr_name in sorted(chr_names))

def parse_genotype_file(filename: str, parlist: tuple = tuple()):
    """
    Parse the provided genotype file into a usable pytho3 data structure.
    """
    with open(filename, "r", encoding="utf8") as infile:
        contents = infile.readlines()

    lines = tuple(line for line in contents if
                  ((not line.strip().startswith("#")) and
                   (not line.strip() == "")))
    labels = parse_genotype_labels(
        [line for line in lines if line.startswith("@")])
    data_lines = tuple(line for line in lines if not line.startswith("@"))
    header = parse_genotype_header(data_lines[0], parlist)
    geno_obj = dict(labels + header)
    markers = (
        parse_genotype_marker(line, geno_obj, parlist)
        for line in data_lines[1:])
    chromosomes = tuple(
        dict(chromosome) for chromosome in
        build_genotype_chromosomes(geno_obj, tuple(markers)))
    return {**geno_obj, "chromosomes": chromosomes}
