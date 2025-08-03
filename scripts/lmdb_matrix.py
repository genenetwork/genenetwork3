"""This scripts reads and store genotype files to an LMDB store.
Similarly, it can be use to read this data.

Example:

guix shell python-click python-lmdb python-wrapper python-numpy -- \
     python lmdb_matrix.py import-genotype \
     <path-to-genotype-file> <path-to-lmdb-store>

guix shell python-click python-lmdb python-wrapper python-numpy -- \
     python lmdb_matrix.py print-current-matrix \
     <path-to-lmdb-store>

"""
from dataclasses import dataclass
from pathlib import Path
from subprocess import check_output

import json
import click
import lmdb
import numpy as np


@dataclass
class GenotypeMatrix:
    """Store the actual Genotype Matrix"""
    matrix: np.ndarray
    metadata: dict
    file_info: dict


def count_trailing_newlines(file_path):
    """Count trailing newlines in a file"""
    with open(file_path, 'rb', encoding="utf-8") as stream:
        stream.seek(0, 2)  # Move to the end of the file
        file_size = stream.tell()
        if file_size == 0:
            return 0
        chunk_size = 1024  # Read in small chunks
        empty_lines = 0
        _buffer = b""

        # Read chunks from the end backward
        while stream.tell() > 0:
            # Don't read beyond start
            chunk_size = min(chunk_size, stream.tell())
            stream.seek(-chunk_size, 1)  # Move backward
            chunk = stream.read(chunk_size) + _buffer
            stream.seek(-chunk_size, 1)  # Move back to start of chunk
            # Decode chunk to text
            try:
                chunk_text = chunk.decode('utf-8', errors='ignore')
            except UnicodeDecodeError:
                # If decoding fails, keep some bytes for the next
                # chunk Keep last 16 bytes to avoid splitting
                # characters
                _buffer = chunk[-16:]
                continue

            # Split into lines from the end
            lines = chunk_text.splitlines()

            # Count empty lines from the end
            for line in reversed(lines):
                if line.strip() != "":
                    return empty_lines
                empty_lines += 1
            if stream.tell() == 0:
                return empty_lines
        return empty_lines


def wc(filename):
    """Get total file count of a file"""
    return int(check_output(["wc", "-l", filename]).split()[0]) - \
        count_trailing_newlines(filename)


def get_genotype_metadata(genotype_file: str) -> tuple[dict, dict]:
    """Parse metadata from a genotype file, separating '@'-prefixed
    and '#'-prefixed entries.

    This function reads a genotype file and extracts two types of metadata:
    - '@'-prefixed metadata (e.g., '@name:BXD'), stored as key-value
      pairs for dataset attributes.
    - '#'-prefixed metadata (e.g., '# File name: BXD_Geno...'), stored
      as key-value pairs for file information.  Lines starting with
      '#' without a colon are skipped as comments. Parsing stops at
      the first non-metadata line.

    Args:
        genotype_file (str): Path to the genotype file to be parsed.

    Returns:
        tuple[dict, dict]: A tuple containing two dictionaries:
            - First dict: '@'-prefixed metadata (e.g., {'name': 'BXD',
              'type': 'riset'}).
            - Second dict: '#'-prefixed metadata with colons (e.g.,
              {'File name': 'BXD_Geno...', 'Citation': '...'}).

    Example:
        >>> meta, file_info = get_genotype_metadata("BXD.small.geno")
        >>> print(meta)
        {'name': 'BXD', 'type': 'riset', 'mat': 'B', 'pat': 'D',
        'het': 'H', 'unk': 'U'}
        >>> print(file_info)
        {'File name': 'BXD_Geno-19Jan2017b_forGN.xls', 'Metadata':
        'Please retain...'}

    """
    metadata = {}
    file_metadata = {}
    with open(genotype_file, "r", encoding="utf-8") as stream:
        while True:
            line = stream.readline().strip()
            match line:
                case meta if line.startswith("#"):
                    if ":" in meta:
                        key, value = meta[2:].split(":", 1)
                        file_metadata[key] = value
                case meta if line.startswith("#"):
                    continue
                case meta if line.startswith("@") and ":" in line:
                    key, value = meta[1:].split(":", 1)
                    if value:
                        metadata[key] = value.strip()
                case _:
                    break
    return metadata, file_metadata


def get_genotype_dimensions(genotype_file: str) -> tuple[int, int]:
    """Calculate the dimensions of the data section in a genotype
    file.

    This function determines the number of data rows and columns in a
    genotype file.  It skips metadata lines (starting with '#' or '@')
    and uses the first non-metadata line as the header to count
    columns. The total number of lines is counted in binary mode to
    efficiently handle large files, and the number of data rows is
    calculated by subtracting metadata and header lines. Accounts for
    a potential trailing newline.

    Args:
        genotype_file (str): Path to the genotype file to be analyzed.

    Returns:
        tuple[int, int]: A tuple containing:
            - First int: Number of data rows (excluding metadata and
              header).
            - Second int: Number of columns (based on the header row).

    Example:
        >>> rows, cols = get_genotype_dimensions("BXD.small.geno")
        >>> print(rows, cols)
        2, 202  # Example: 2 data rows, 202 columns (from header)

    Note:
        Assumes the first non-metadata line is the header row, split
        by whitespace.  A trailing newline may be included in the line
        count but is accounted for in the returned row count.

    """
    counter = 0
    rows = []

    with open(genotype_file, "r", encoding="utf-8") as stream:
        while True:
            line = stream.readline()
            counter += 1
            match line:
                case "" | _ if line.startswith(("#", "@", "\n")):
                    continue
                case _:
                    rows = line.split()
                    break
    return wc(genotype_file) - counter, len(rows)


def read_genotype_headers(genotype_file: str) -> list[str]:
    """Extract the header row from a genotype file.

    This function reads a genotype file and returns the first
    non-metadata line as a list of column headers. It skips lines
    starting with '#' (comments), '@' (metadata), or empty lines,
    assuming the first non-skipped line contains the header (e.g.,
    'Chr', 'Locus', 'cM', 'Mb', followed by strain names like 'BXD1',
    'BXD2', etc.). The header is split by whitespace to create the
    list of column names.

    Args:
        genotype_file (str): Path to the genotype file to be parsed.

    Returns:
        list[str]: A list of column headers from the first non-metadata line.

    Example:
        >>> headers = read_genotype_headers("BXD.small.geno")
        >>> print(headers)
        ['Chr', 'Locus', 'cM', 'Mb', 'BXD1', 'BXD2', ..., 'BXD220']
    """
    rows = []
    with open(genotype_file, "r", encoding="utf-8") as stream:
        while True:
            line = stream.readline()
            match line:
                case _ if line.startswith("#") or line.startswith("@") or line == "":
                    continue
                case _:
                    rows = line.split()
                    break
    return rows


# pylint: disable=too-many-locals
def read_genotype_file(genotype_file: str) -> GenotypeMatrix:
    """Read a genotype file and construct a GenotypeMatrix object.

    This function parses a genotype file to extract metadata and
    genotype data, creating a numerical matrix of genotype values and
    associated metadata. It processes:
    - '@'-prefixed metadata (e.g., '@mat:B') for dataset attributes
      like maternal/paternal alleles.
    - '#'-prefixed metadata (e.g., '# File name:...') for file
      information.
    - Header row for column names (e.g., 'Chr', 'Locus', BXD strains).
    - Data rows, converting genotype symbols (e.g., 'B', 'D', 'H',
    'U') to numeric values (0, 1, 2, 3) based on metadata mappings.

    The function skips comment lines ('#'), metadata lines ('@'), and
    empty lines, and organizes the data into a GenotypeMatrix with a
    numpy array and metadata dictionaries.

 Args:
    genotype_file (str): Path to the genotype file to be parsed.

 Returns:
    GenotypeMatrix: An object containing:
    - matrix: A numpy array (nrows x ncols) with genotype values (0:
    maternal, 1: paternal, 2: heterozygous, 3: unknown).
    - metadata: A dictionary with '@'-prefixed metadata, row/column
    counts, individuals (BXD strains), metadata columns (e.g., 'Chr',
    'Locus'), and lists of metadata values per row.
    - file_info: A dictionary with '#'-prefixed metadata (e.g., 'File
      name', 'Citation').

 Raises:
    ValueError: If an unrecognized genotype symbol is encountered in
    the data.

 Example:
    >>> geno_matrix = read_genotype_file("BXD.small.geno")
    >>> print(geno_matrix.matrix.shape)
    (2, 198) # Example: 2 rows, 198 BXD strains
    >>> print(geno_matrix.metadata["name"])
    'BXD'
    >>> print(geno_matrix.file_info["File name"])
    'BXD_Geno-19Jan2017b_forGN.xls'
    """
    header = read_genotype_headers(genotype_file)

    counter = 0
    for i, el in enumerate(header):
        if el not in ["Chr", "Locus", "cM", "Mb"]:
            break
        counter = i

    metadata_columns, individuals = header[:counter], header[counter:]
    nrows, ncols = get_genotype_dimensions(genotype_file)
    ncols -= len(metadata_columns)
    matrix = np.zeros((nrows, ncols), dtype=np.uint8)

    metadata, file_metadata = get_genotype_metadata(genotype_file)
    metadata = metadata | {
        "nrows": nrows,
        "ncols": ncols,
        "individuals": individuals,
        "metadata_columns": metadata_columns
    }
    for key in metadata_columns:
        metadata[key] = []

    maternal = metadata.get("mat")
    paternal = metadata.get("pat")
    heterozygous = metadata.get("het")
    unknown = metadata.get("unk")
    i = 0
    sentinel = True
    with open(genotype_file, "r", encoding="utf-8") as stream:
        while True:
            if i == nrows:
                break
            line = stream.readline().split()
            meta, data = [], []
            if line and line[0] in metadata_columns:
                # Skip the metadata column
                line = stream.readline().split()
                sentinel = False
            if len(line) == 0 or (line[0].startswith("#") and sentinel) \
               or line[0].startswith("@"):
                continue
            meta, data = line[:len(metadata_columns)
                              ], line[len(metadata_columns):]
            # KLUDGE: It's not clear whether chromosome rows that
            # start with a '#' should be a comment or not.  For some
            # there's a mismatch between (E.g. B6D2F2_mm8) the size of
            # the data values and ncols.  For now, skip them.
            if len(data) != ncols:
                i += 1
                continue
            for j, el in enumerate(data):
                match el:
                    case _ if el.isdigit():
                        matrix[i, j] = int(el)
                    case _ if maternal == el:
                        matrix[i, j] = 0
                    case _ if paternal == el:
                        matrix[i, j] = 1
                    case _ if heterozygous == el:
                        matrix[i, j] = 2
                    case _ if unknown == el:
                        matrix[i, j] = 3
                    case _:
                        # KLUDGE: It's not clear how to handle float
                        # types in a geno file
                        # E.g. HSNIH-Palmer_true.geno which has float
                        # values such as:  0.997.  Ideally maybe:
                        # raise ValueError
                        continue
            i += 1
            __map = dict(zip(metadata_columns, meta))
            for key in metadata_columns:
                metadata[key].append(__map.get(key))

    genotype_matrix = GenotypeMatrix(
        matrix=matrix,
        metadata=metadata,
        file_info=file_metadata
    )
    return genotype_matrix


def create_database(db_path: str) -> lmdb.Environment:
    """Create or open an LMDB environment."""
    return lmdb.open(db_path, map_size=100 * 1024 * 1024 * 1024, create=True)


def genotype_db_put(db: lmdb.Environment, genotype: GenotypeMatrix) -> bool:
    """Put genotype GENOTYPEMATRIX from DB environment"""
    metadata = json.dumps(genotype.metadata).encode("utf-8")
    file_info = json.dumps(genotype.file_info).encode("utf-8")
    with db.begin(write=True) as txn:
        txn.put(b"matrix", genotype.matrix.tobytes())
        txn.put(b"metadata", metadata)
        # XXXX: KLUDGE: Put this in RDF instead
        txn.put(b"file_info", file_info)
    return True


def genotype_db_get(db: lmdb.Environment) -> GenotypeMatrix:
    """Get genotype GENOTYPEMATRIX from DB environment"""
    with db.begin() as txn:
        metadata = json.loads(txn.get(b"metadata").decode("utf-8"))
        nrows, ncols = metadata.get("nrows"), metadata.get("ncols")
        matrix = np.frombuffer(
            txn.get(b"matrix"), dtype=np.uint8).reshape(nrows, ncols)
        return GenotypeMatrix(
            matrix=matrix,
            metadata=metadata,
            file_info=json.loads(txn.get(b"file_info"))
        )


def get_genotype_files(directory: str) -> list[tuple[str, int]]:
    """Return a list of all the genotype files from a given
    directory."""
    geno_files = [
        (_file.as_posix(), _file.stat().st_size)
        for _file in Path(directory).glob("*.geno") if _file.is_file()]
    return sorted(geno_files, key=lambda x: x[1])


def __import_directory(directory: str, lmdb_path: str):
    """Import all the genotype files from a given directory into
    LMDB."""
    for genofile, file_size in get_genotype_files(directory):
        genofile = Path(genofile)
        size_mb = file_size / (1024 ** 2)
        lmdb_store = (Path(lmdb_path) / genofile.stem).as_posix()
        print(f"Processing file: {genofile.name}")
        with create_database(lmdb_store) as db:
            genotype_db_put(
                db=db, genotype=read_genotype_file(genofile.as_posix()))
        print(f"\nSuccessfuly created: [{size_mb:.2f} MB] {genofile.stem}")


@click.command(help="Import the genotype directory")
@click.argument("genotype_directory")
@click.argument("lmdb_path")
def import_directory(genotype_directory: str, lmdb_path: str):
    "Import a genotype directory into genotype_database path"
    __import_directory(directory=genotype_directory, lmdb_path=lmdb_path)


@click.command(help="Import the genotype file")
@click.argument("geno_file")
@click.argument("genotype_database")
def import_genotype(geno_file: str, genotype_database: str):
    "Import a genotype file into genotype_database path"
    with create_database(genotype_database) as db:
        genotype_db_put(db=db, genotype=read_genotype_file(geno_file))


@click.command(help="Print the current matrix")
@click.argument("database_directory")
def print_current_matrix(database_directory: str):
    """Print the current matrix in the database."""
    with create_database(database_directory) as db:
        current = genotype_db_get(db)
        print(f"Matrix: {current.matrix}")
        print(f"Metadata: {current.metadata}")
        print(f"File Info: {current.file_info}")


# pylint: disable=missing-function-docstring
@click.group()
def cli():
    pass


cli.add_command(print_current_matrix)
cli.add_command(import_genotype)
cli.add_command(import_directory)

if __name__ == "__main__":
    cli()
