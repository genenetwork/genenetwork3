"""Methods for fetching data from the matrix stored in LMDB"""
from typing import Optional
from dataclasses import dataclass

import struct
import json
import lmdb

BLOB_HASH_DIGEST = 32


@dataclass
class Matrix:
    """Store sample data and any other relevant metadata"""

    data: list
    metadata: dict


def get_current_matrix(db_path: str) -> Optional[Matrix]:
    """Get the most recent matrix from DB_PATH.  This is functionally
    equivalent to get_nth_matrix(0, db_path)"""
    env = lmdb.open(db_path)
    with env.begin(write=False) as txn:
        current_hash = txn.get(b"current") or b""
        matrix_hash = txn.get(current_hash + b":matrix") or b""
        row_pointers = txn.get(matrix_hash + b":row-pointers")
        nrows = 0
        if matrix_hash:
            (nrows,) = struct.unpack("<Q", txn.get(matrix_hash + b":nrows"))
            data, metadata = None, None
        if row_pointers:
            return Matrix(
                data=[
                    json.loads(txn.get(row_pointers[i: i + 32]).decode())
                    for i in range(0, nrows * 32, 32)
                ],
                metadata=json.loads(
                    txn.get(matrix_hash + b":metadata")
                    .rstrip(b"\x00")
                    .decode()
                ),
            )
        return None
