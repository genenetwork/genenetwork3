'''Genotype database reader

This module is a tiny Python library to read a GeneNetwork genotype
database. It exports the following functions.

* open - Open a genotype database
* matrix - Get current matrix
* nparray - Get matrix as a 2D numpy array
* row - Get row of matrix
* column - Get column of matrix

Here is a typical invocation to read the entire matrix, row 17 and column 13
from a genotype database at `/tmp/bxd`.

from gn3 import genodb

with genodb.open('/tmp/bxd') as db:
    matrix = genodb.matrix(db)
    print(genodb.nparray(matrix))
    print(genodb.row(matrix, 17))
    print(genodb.column(matrix, 13))
'''

from collections import namedtuple
from contextlib import contextmanager
import lmdb
import numpy as np

# pylint: disable=invalid-name,redefined-builtin

GenotypeDatabase = namedtuple('GenotypeDatabase', 'txn hash_length')
GenotypeMatrix = namedtuple('GenotypeMatrix', 'array transpose')

@contextmanager
def open(path):
    '''Open genotype database.'''
    env = lmdb.open(path, readonly=True, create=False)
    txn = env.begin()
    yield GenotypeDatabase(txn, 32) # 32 bytes in a SHA256 hash
    txn.abort()
    env.close()

def get_metadata(db, hash, metadata):
    '''Get metadata associated with hash in genotype database.'''
    return db.txn.get(hash + b':' + metadata.encode())

def matrix(db):
    '''Get current matrix from genotype database.'''
    hash = db.txn.get(b'versions')[0:db.hash_length]
    read_optimized_blob = db.txn.get(db.txn.get(b'current'))
    nrows = int.from_bytes(get_metadata(db, hash, 'nrows'), byteorder='little')
    ncols = int.from_bytes(get_metadata(db, hash, 'ncols'), byteorder='little')
    return GenotypeMatrix(np.reshape(np.frombuffer(read_optimized_blob[0 : nrows*ncols],
                                                   dtype=np.uint8),
                                     (nrows, ncols)),
                          np.reshape(np.frombuffer(read_optimized_blob[nrows*ncols :],
                                                   dtype=np.uint8),
                                     (ncols, nrows)))

def nparray(matrix):
    '''Get matrix as a 2D numpy array.'''
    # pylint: disable=redefined-outer-name
    return matrix.array

def row(matrix, index):
    '''Get row of matrix.'''
    # pylint: disable=redefined-outer-name
    return matrix.array[index,:]

def column(matrix, index):
    '''Get column of matrix.'''
    # pylint: disable=redefined-outer-name
    return matrix.transpose[index,:]
