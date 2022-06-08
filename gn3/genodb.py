import lmdb
import numpy as np

class GenotypeDatabase:
    def __init__(self, path):
        self.env = lmdb.open(path, readonly=True, create=False)
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
        return self.txn.get(hash + b':' + metadata.encode())
    def matrix(self):
        hash = self.get(b'current')[0:self.hash_length]
        return Matrix(self, hash)

class Matrix():
    def __init__(self, db, hash):
        self.nrows = int.from_bytes(db.get_metadata(hash, 'nrows'), byteorder='little')
        self.ncols = int.from_bytes(db.get_metadata(hash, 'ncols'), byteorder='little')
        row_column_pointers = db.get(hash)
        self.row_pointers = row_column_pointers[0 : self.nrows*db.hash_length]
        self.column_pointers = row_column_pointers[self.nrows*db.hash_length :]
        self.db = db
    def __vector(self, index, pointers):
        start = index * self.db.hash_length
        end = start + self.db.hash_length
        return np.frombuffer(self.db.get(pointers[start:end]),
                             dtype=np.uint8)
    def row(self, index):
        return self.__vector(index, self.row_pointers)
    def column(self, index):
        return self.__vector(index, self.column_pointers)
