import lmdb
import json
import click
from dataclasses import dataclass

from contextlib import contextmanager
import numpy as np


@dataclass
class GenotypeMatrix:
    """Store the actual Genotype Matrix"""
    matrix: np.ndarray
    transpose: np.ndarray
    metadata: dict


@contextmanager
def save_excursion(stream):
    """Context manager to restore stream position after use."""
    position = stream.tell()
    try:
        yield
    finally:
        stream.seek(position)


def count_lines(stream) -> int:
    """Count the number of lines in the stream from the current
    position."""
    count = 0
    with save_excursion(stream):
        while stream.readline().strip():
            count += 1
    return count


def create_database(db_path: str) -> lmdb.Environment:
    """Create or open an LMDB environment."""
    return lmdb.open(db_path, map_size=100 * 1024 * 1024, create=True)


def genotype_db_put(db: lmdb.Environment, genotype: GenotypeMatrix) -> bool:
    metadata = json.dumps(genotype.metadata).encode("utf-8")
    with db.begin(write=True) as txn:
        txn.put(b"matrix", genotype.matrix.tobytes())
        txn.put(b"transpose", genotype.transpose.tobytes())
        txn.put(b"metadata", metadata)
    return True


def read_geno_file(genotype_file: str) -> GenotypeMatrix:
    """Read a geno file and return a GenotypeMatrix object."""
    with open(genotype_file, 'r') as stream:
        # Read file metadata
        file_metadata = {}
        while True:
            line = stream.readline().strip()
            if not line:
                break
            if line.startswith('#'):
                continue
            if line.startswith('@'):
                key, value = line[1:].split(':', 1)
                file_metadata[key] = value
            else:
                stream.seek(stream.tell() - len(line) - 1)
                break

        # Read header
        header = stream.readline().strip().split()
        metadata_columns = ["Chr", "Locus", "cM",
                            "Mb"] if "Mb" in header else ["Chr", "Locus", "cM"]

        individuals = header[len(metadata_columns):]

        # Read data
        nrows = count_lines(stream)
        ncols = len(individuals)
        matrix = np.zeros((nrows, ncols), dtype=np.uint8)
        maternal = file_metadata.get("mat")
        paternal = file_metadata.get("pat")
        heterozygous = file_metadata.get("het")
        unknown = file_metadata.get("unk")

        metadata = {
            "nrows": nrows,
            "ncols": ncols,
            "individuals": individuals,
            "metadata_keys": metadata_columns + ["individuals"]
        }

        for key in metadata_columns[2:]:
            metadata[key] = []

        locus, chromosomes = [], []
        for i in range(nrows):
            line = stream.readline().strip().split()
            meta, data = line[:len(metadata_columns)
                              ], line[len(metadata_columns):]
            for j, element in enumerate(data):
                if element.isdigit():
                    matrix[i, j] = int(element)
                elif element == maternal:
                    matrix[i, j] = 0
                elif element == paternal:
                    matrix[i, j] = 1
                elif element == heterozygous:
                    matrix[i, j] = 2
                elif element == unknown:
                    matrix[i, j] = 3
            data = dict(zip(metadata_columns, meta))
            locus.append(data.get("Locus"))
            chromosomes.append(data.get("Chr"))
            for col in metadata_columns[2:]:
                metadata[col].append(float(data.get(col)))
        metadata["locus"] = locus
        metadata["chromosomes"] = chromosomes
        genotype_matrix = GenotypeMatrix(matrix, matrix.T, metadata)
        return genotype_matrix


def genotype_db_get(db: lmdb.Environment) -> GenotypeMatrix:
    with db.begin() as txn:
        metadata = json.loads(txn.get(b"metadata").decode("utf-8"))
        nrows, ncols = metadata.get("nrows"), metadata.get("ncols")
        matrix, transpose = txn.get(b"matrix"), txn.get(b"transpose")
        # Double check this
        matrix = np.frombuffer(matrix, dtype=np.uint8).reshape(nrows, ncols)
        transpose = np.frombuffer(transpose, dtype=np.uint8)\
                      .reshape(ncols, nrows)
        return GenotypeMatrix(matrix, transpose, metadata)


@click.command(help="Import the genotype file")
@click.argument("geno_file")
@click.argument("genotype_database")
def import_genotype(geno_file: str, genotype_database: str):
    with create_database(genotype_database) as db:
        genotype_db_put(db, read_geno_file(geno_file))


@click.command(help="Print the current matrix")
@click.argument("database_directory")
def print_current_matrix(database_directory: str):
    """Print the current matrix in the database."""
    with create_database(database_directory) as db:
        current = genotype_db_get(db)
        print(f"Matrix: {current.matrix}")
        print(f"Transpose: {current.transpose}")
        print(f"Metadata: {current.metadata}")


@click.group()
def cli():
    pass


cli.add_command(print_current_matrix)
cli.add_command(import_genotype)


if __name__ == "__main__":
    cli()
