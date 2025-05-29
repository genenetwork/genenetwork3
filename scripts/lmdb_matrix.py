import lmdb
import hashlib
import os
import struct
import sys
import click
from dataclasses import dataclass

from contextlib import contextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


@dataclass
class GenotypeMatrix:
    """Store the actual Genotype Matrix"""
    matrix: np.ndarray
    metadata: List[Dict[str, str]]


@dataclass
class GenotypeDBMatrix:
    db: lmdb.Environment
    genotype_hash: bytes
    nrows: int
    ncols: int
    row_pointers: np.ndarray
    column_pointers: np.ndarray
    array: Optional[np.ndarray] = None
    transpose: Optional[np.ndarray] = None


def __unpack(db: lmdb.Environment, name, type_) -> list:
    current_hash = genotype_db_current_matrix_hash(db)
    packed = genotype_db_metadata_get(db, current_hash, name)
    if type_ is str:
        offset = 0
        result = []
        while offset < len(packed):
            length = struct.unpack_from("<B", packed, offset)[0]
            offset += 1
            s = packed[offset:offset + length].decode()
            result.append(s)
            offset += length
        return result
    if type_ is int:
        return list(struct.unpack(f"<{len(packed)}B", packed))
    if type_ is float:
        return struct.unpack(f"<{len(packed)//4}f", packed)


def matrix_row(matrix: np.ndarray, n: int) -> np.ndarray:
    """Return the nth row of the matrix."""
    return matrix[n, :]


def matrix_column(matrix: np.ndarray, n: int) -> np.ndarray:
    """Return the nth column of the matrix."""
    return matrix[:, n]


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


def repeat_indexed(function, n: int) -> List[Any]:
    """Run function n times with indices 0 to n-1 and return results as a list."""
    return [function(i) for i in range(n)]


def find_index(function, n: int) -> Optional[int]:
    """Find the first index from 0 to n-1 where function returns True."""
    for i in range(n):
        if function(i):
            return i
    return None


def create_database(db_path: str) -> lmdb.Environment:
    """Create or open an LMDB environment."""
    return lmdb.open(db_path, map_size=100 * 1024 * 1024, create=True)


def genotype_db_get(db: lmdb.Environment, key: bytes) -> Optional[bytes]:
    """Retrieve a value from the database by key."""
    with db.begin() as txn:
        return txn.get(key)


def genotype_db_put(
        db: lmdb.Environment,
        value: bytes,
        metadata: Optional[Dict] = {}
) -> bytes:
    """Store a value in the database with optional metadata and return its hash."""
    metadata = metadata or {}
    hash_obj = hashlib.sha256()

    # Hash the value
    hash_obj.update(struct.pack('<Q', len(value)))
    hash_obj.update(value)
    # Hash metadata
    for key, val in metadata.items():
        key_bytes = key.encode('utf-8')
        hash_obj.update(struct.pack('<Q', len(key_bytes)))
        hash_obj.update(key_bytes)
        if isinstance(val, str):
            val_bytes = val.encode('utf-8')
        elif isinstance(val, int):
            val_bytes = struct.pack('<Q', val)
        else:
            val_bytes = val
        hash_obj.update(struct.pack('<Q', len(val_bytes)))
        hash_obj.update(val_bytes)

    hash_value = hash_obj.digest()
    # Store value and metadata if not already present
    with db.begin(write=True) as txn:
        if not txn.get(hash_value):
            txn.put(hash_value, value)
            for key, val in metadata.items():
                if isinstance(val, str):
                    val_bytes = val.encode('utf-8')
                elif isinstance(val, int):
                    val_bytes = struct.pack('<Q', val)
                else:
                    val_bytes = val
                txn.put(hash_value + b':' + key.encode('utf-8'), val_bytes)

    return hash_value


def genotype_db_metadata_get(db: lmdb.Environment, genotype_hash: bytes, key: str) -> Optional[bytes]:
    """Retrieve metadata for a given hash and key."""
    return genotype_db_get(db, genotype_hash + b':' + key.encode('utf-8'))


def genotype_db_current_matrix_hash(db: lmdb.Environment) -> Optional[bytes]:
    """Get the hash of the current matrix."""
    versions = genotype_db_get(db, b'versions')
    if versions:
        return versions[:hashlib.sha256().digest_size]
    return None


def set_genotype_db_current_matrix_hash(db: lmdb.Environment, genotype_hash: bytes):
    """Set the hash of the current matrix."""
    versions = genotype_db_get(db, b'versions') or b''
    with db.begin(write=True) as txn:
        txn.put(b'versions', genotype_hash + versions)

    # Create read-optimized copy
    matrix = genotype_db_matrix(db, genotype_hash)
    output = bytearray()
    for i in range(matrix.nrows):
        output.extend(genotype_db_matrix_row_ref(matrix, i))
    for i in range(matrix.ncols):
        output.extend(genotype_db_matrix_column_ref(matrix, i))
    current_db = genotype_db_put(db, bytes(output), {"matrix": genotype_hash})
    with db.begin(write=True) as txn:
        txn.put(b'current', current_db)


def genotype_db_all_matrices(db: lmdb.Environment) -> List['GenotypeDBMatrix']:
    """Return a list of all matrices in the database, newest first."""
    versions = genotype_db_get(db, b'versions') or b''
    hash_length = hashlib.sha256().digest_size
    return [genotype_db_matrix(db, versions[i:i + hash_length])
            for i in range(0, len(versions), hash_length)]


def genotype_db_matrix(db: lmdb.Environment, genotype_hash: bytes) -> 'GenotypeDBMatrix':
    """Retrieve a matrix by its hash."""
    hash_length = hashlib.sha256().digest_size
    nrows = struct.unpack('<Q', genotype_db_metadata_get(
        db, genotype_hash, 'nrows'))[0]
    ncols = struct.unpack('<Q', genotype_db_metadata_get(
        db, genotype_hash, 'ncols'))[0]
    data = genotype_db_get(db, genotype_hash)
    row_pointers = np.frombuffer(data[:nrows * hash_length], dtype=np.uint8)
    column_pointers = np.frombuffer(data[nrows * hash_length:], dtype=np.uint8)
    return GenotypeDBMatrix(db, genotype_hash, nrows, ncols, row_pointers, column_pointers)


def genotype_db_matrix_put(db: lmdb.Environment, matrix: GenotypeMatrix) -> bytes:
    """Store a genotype matrix in the database and return its hash."""
    mat = matrix.matrix
    nrows, ncols = mat.shape
    output = bytearray()

    # Store rows
    for i in range(nrows):
        row = mat[i, :].tobytes()
        output.extend(genotype_db_put(db, row))

    # Store columns
    for j in range(ncols):
        col = mat[:, j].tobytes()
        output.extend(genotype_db_put(db, col))

    return genotype_db_put(
        db, bytes(output),
        {
            "nrows": nrows,
            "ncols": ncols
        } | matrix.metadata
    )


def genotype_db_current_matrix(db: lmdb.Environment) -> 'GenotypeDBMatrix':
    """Return the latest version of the matrix."""
    read_optimized = genotype_db_get(db, genotype_db_get(db, b'current'))
    current_hash = genotype_db_current_matrix_hash(db)
    nrows = struct.unpack('<Q', genotype_db_metadata_get(
        db, current_hash, 'nrows'))[0]
    ncols = struct.unpack('<Q', genotype_db_metadata_get(
        db, current_hash, 'ncols'))[0]

    array = np.frombuffer(
        read_optimized[:nrows * ncols], dtype=np.uint8).reshape(nrows, ncols)
    transpose = np.frombuffer(
        read_optimized[nrows * ncols:], dtype=np.uint8).reshape(ncols, nrows)

    return GenotypeDBMatrix(db, current_hash, nrows, ncols, None, None, array, transpose)


def genotype_db_matrix_ref(matrix: GenotypeDBMatrix) -> np.ndarray:
    """Return the matrix as a 2D NumPy array."""
    if matrix.array is not None:
        return matrix.array
    array = np.zeros((matrix.nrows, matrix.ncols), dtype=np.uint8)
    for i in range(matrix.nrows):
        row = genotype_db_matrix_row_ref(matrix, i)
        for j in range(matrix.ncols):
            array[i, j] = row[j]
    return array


def genotype_db_matrix_row_ref(matrix: GenotypeDBMatrix, i: int) -> np.ndarray:
    """Return the ith row of the matrix."""
    if matrix.array is not None:
        return matrix_row(matrix.array, i)
    hash_length = hashlib.sha256().digest_size
    row_hash = matrix.row_pointers[i *
                                   hash_length:(i + 1) * hash_length].tobytes()
    return np.frombuffer(genotype_db_get(matrix.db, row_hash), dtype=np.uint8)


def genotype_db_matrix_column_ref(matrix: GenotypeDBMatrix, j: int) -> np.ndarray:
    """Return the jth column of the matrix."""
    if matrix.transpose is not None:
        return matrix_row(matrix.transpose, j)
    hash_length = hashlib.sha256().digest_size
    col_hash = matrix.column_pointers[j *
                                      hash_length:(j + 1) * hash_length].tobytes()
    return np.frombuffer(genotype_db_get(matrix.db, col_hash), dtype=np.uint8)

# Geno File Parsing


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

        def encode_list_str(str_list):
            pack = b''
            for s in str_list:
                bstr = s.encode()
                pack += struct.pack('<B', len(bstr)) + bstr
            return pack

        individuals = header[len(metadata_columns):]

        # Read data
        nrows = count_lines(stream)
        ncols = len(individuals)
        matrix = np.zeros((nrows, ncols), dtype=np.uint8)
        # matrix = np.memmap("/tmp/data.dat", dtype=np.uint8, mode="w+", (nrows, ncols))
        maternal = file_metadata.get("mat")
        paternal = file_metadata.get("pat")
        heterozygous = file_metadata.get("het")
        unknown = file_metadata.get("unk")

        metadata = {
            "individuals": encode_list_str(individuals),
            "metadata_keys": encode_list_str(metadata_columns + ["individuals"])
        }
        for key in metadata_columns[2:]:
            metadata[key] = []

        locus, chromosomes = b'', []
        for i in range(nrows):
            line = stream.readline().strip().split()
            meta, data = line[:len(metadata_columns)
                              ], line[len(metadata_columns):]
            for j, element in enumerate(data):
                # print(i, j)
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
            locus += struct.pack("<B", len(data.get("Locus").encode())) + locus
            chromosomes.append(int(data.get("Chr")))
            for col in metadata_columns[2:]:
                metadata[col].append(float(data.get(col)))
        metadata["Chr"] = struct.pack(f'{len(chromosomes)}B', *chromosomes)
        for col in metadata_columns[2:]:
            metadata[col] = struct.pack(
                f"<{len(metadata[col])}f", *metadata[col])
        # matrix.flush()
        return GenotypeMatrix(matrix, metadata)


def hash_in_hash_vector(hash_bytes: bytes, hash_vector: bytes) -> bool:
    """Check if hash_bytes is in hash_vector."""
    hash_length = hashlib.sha256().digest_size
    for i in range(0, len(hash_vector), hash_length):
        if hash_vector[i:i + hash_length] == hash_bytes:
            return True
    return False


def live_key_p(db: lmdb.Environment, key: bytes) -> bool:
    """Check if a key is live in the database."""
    if key in (b'current', b'versions'):
        return True
    if key == genotype_db_get(db, b'current'):
        return True
    versions = genotype_db_get(db, b'versions') or b''
    hash_length = hashlib.sha256().digest_size
    key_hash = key[:hash_length]
    if hash_in_hash_vector(key_hash, versions):
        return True
    for i in range(0, len(versions), hash_length):
        matrix_hash = versions[i:i + hash_length]
        matrix_data = genotype_db_get(db, matrix_hash)
        if hash_in_hash_vector(key_hash, matrix_data):
            return True
    return False


def collect_garbage(db: lmdb.Environment):
    """Delete all keys in the database that are not associated with a live hash."""
    with db.begin(write=True) as txn:
        cursor = txn.cursor()
        for key, _ in cursor:
            if not live_key_p(db, key):
                cursor.delete()


@click.command(help="Import the genotype file")
@click.argument("geno_file")
@click.argument("genotype_database")
def import_into_genotype_db(geno_file: str, genotype_database: str):
    """Import a geno file into the genotype database."""
    print("Reading geno file")
    matrix = read_geno_file(geno_file)
    with create_database(genotype_database) as db:
        hash_value = genotype_db_matrix_put(db, matrix)
        db_matrix = genotype_db_matrix(db, hash_value)
        print("Verifying written data")
        # Verify written data
        try:
            current_hash = genotype_db_current_matrix(db).genotype_hash
        except TypeError as excp:
            current_hash = b""
        if current_hash == hash_value:
            print("No change in geno file")
            exit(0)
        for i in range(db_matrix.nrows):
            if not np.array_equal(matrix_row(matrix.matrix, i), genotype_db_matrix_row_ref(db_matrix, i)):
                collect_garbage(db)
                print(
                    f"Rereading and verifying genotype matrix written to {genotype_database} failed.", file=sys.stderr)
                sys.exit(1)
        for i in range(db_matrix.ncols):
            if not np.array_equal(matrix_column(matrix.matrix, i), genotype_db_matrix_column_ref(db_matrix, i)):
                collect_garbage(db)
                print(
                    f"Rereading and verifying genotype matrix written to 3 {genotype_database} failed.", file=sys.stderr)
                sys.exit(1)
        set_genotype_db_current_matrix_hash(db, hash_value)


@click.command(help="Print the genotype db information")
@click.argument("database_directory")
def print_genotype_db_info(database_directory: str):
    """Print information about the genotype database."""
    with create_database(database_directory) as db:
        matrices = genotype_db_all_matrices(db)
        with db.begin() as txn:
            stats = txn.stat()
        print(f"Path: {database_directory}")
        print(f"Versions: {len(matrices)}")
        print(f"Keys: {stats['entries']}")
        print()
        for i, matrix in enumerate(matrices, 1):
            print(f"Version {i}")
            print(f"  Dimensions: {matrix.nrows} × {matrix.ncols}")


@click.command(help="Print the current matrix")
@click.argument("database_directory")
def print_current_matrix(database_directory: str):
    """Print the current matrix in the database."""
    with create_database(database_directory) as db:
        current = genotype_db_current_matrix(db)
        # metadata_keys = __unpack(db, "metadata_keys", str)
        # chromosomes = __unpack(db, "Chr", int)
        # cM = __unpack(db, "cM", float)
        # individuals = __unpack(db, "individuals", str)
        # locus = __unpack(db, "Locus", str)
        print(current)


@click.group()
def cli():
    pass


cli.add_command(print_current_matrix)
cli.add_command(import_into_genotype_db)
cli.add_command(print_genotype_db_info)


if __name__ == "__main__":
    cli()
