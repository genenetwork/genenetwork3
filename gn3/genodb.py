'''Genotype database reader

This module is a tiny Python library to read a GeneNetwork genotype
database. It exports the following functions.

* open - Open a genotype database
* matrix - Get current matrix
* row - Get row of matrix
* column - Get column of matrix

Here is a typical invocation to read row 17 and column 13 from a genotype
database at `/tmp/bxd`.

from gn3 import genodb

with genodb.open('/tmp/bxd') as db:
    matrix = genodb.matrix(db)
    print(genodb.row(matrix, 17))
    print(genodb.column(matrix, 13))

'''

from collections import namedtuple
from contextlib import contextmanager
import lmdb
import numpy as np

# pylint: disable=invalid-name,redefined-builtin

GenotypeDatabase = namedtuple('GenotypeDatabase', 'txn hash_length')
Matrix = namedtuple('Matrix', 'db nrows ncols row_pointers column_pointers')

@contextmanager
def open(path):
    '''Open genotype database.'''
    env = lmdb.open(path, readonly=True, create=False)
    txn = env.begin()
    yield GenotypeDatabase(txn, 32) # 32 bytes in a SHA256 hash
    txn.abort()
    env.close()

def get(db, key):
    '''Get value associated with key in genotype database.'''
    return db.txn.get(key)

def get_metadata(db, hash, metadata):
    '''Get metadata associated with hash in genotype database.'''
    return db.txn.get(hash + b':' + metadata.encode())

def matrix(db):
    '''Get current matrix from genotype database.'''
    hash = get(db, b'current')[0:db.hash_length]
    nrows = int.from_bytes(get_metadata(db, hash, 'nrows'), byteorder='little')
    ncols = int.from_bytes(get_metadata(db, hash, 'ncols'), byteorder='little')
    row_column_pointers = get(db, hash)
    return Matrix(db, nrows, ncols,
                  row_column_pointers[0 : nrows*db.hash_length],
                  row_column_pointers[nrows*db.hash_length :])

def vector_ref(db, index, pointers):
    '''Get vector from byte array of pointers.'''
    start = index * db.hash_length
    end = start + db.hash_length
    return np.frombuffer(get(db, pointers[start:end]), dtype=np.uint8)

def row(matrix, index):
    '''Get row of matrix.'''
    # pylint: disable=redefined-outer-name
    return vector_ref(matrix.db, index, matrix.row_pointers)

def column(matrix, index):
    '''Get column of matrix.'''
    # pylint: disable=redefined-outer-name
    return vector_ref(matrix.db, index, matrix.column_pointers)
