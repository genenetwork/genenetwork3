import lmdb
import numpy as np

class GenotypeDatabase:
    def __init__(self, path):
        self.env = lmdb.open(path)
        self.txn = self.env.begin()
        # 32 bytes in a SHA256 hash
        self.hash_length = 32
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        self.txn.abort()
        self.env.close()
    def get(self, hash):
        return self.txn.get(hash)
    def get_metadata(self, hash, metadata):
        return self.txn.get(hash + b':' + metadata.encode() + b'\0')
    def matrix(self):
        hash = self.get(b'current\0')
        return Matrix(self, hash)

class Matrix():
    def __init__(self, db, hash):
        # TODO: Decide on endianness.
        self.nrows = int.from_bytes(db.get_metadata(hash, 'nrows'), byteorder='little')
        self.ncols = int.from_bytes(db.get_metadata(hash, 'ncols'), byteorder='little')
        self.row_pointers = db.get(hash)
        self.db = db
    def row(self, index):
        start = index * self.db.hash_length
        end = start + self.db.hash_length
        return np.frombuffer(self.db.get(self.row_pointers[start:end]),
                             dtype=np.uint8)
