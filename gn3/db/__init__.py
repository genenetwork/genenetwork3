# pylint: disable=[R0902, R0903]
"""Module that exposes common db operations"""
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict, astuple
from typing_extensions import Protocol
from MySQLdb import escape_string

from gn3.db.phenotypes import Phenotype
from gn3.db.phenotypes import PublishXRef
from gn3.db.phenotypes import Publication

from gn3.db.phenotypes import phenotype_mapping
from gn3.db.phenotypes import publish_x_ref_mapping
from gn3.db.phenotypes import publication_mapping

TABLEMAP = {
    "Phenotype": phenotype_mapping,
    "PublishXRef": publish_x_ref_mapping,
    "Publication": publication_mapping,
}

DATACLASSMAP = {
    "Phenotype": Phenotype,
    "PublishXRef": PublishXRef,
    "Publication": Publication,
}


class Dataclass(Protocol):
    """Type Definition for a Dataclass"""
    __dataclass_fields__: Dict


def update(conn: Any,
           table: str,
           data: Dataclass,
           where: Dataclass) -> Optional[int]:
    """Run an UPDATE on a table"""
    if not any(astuple(data) + astuple(where)):
        return None
    sql = f"UPDATE {table} SET "
    sql += ", ".join(f"{TABLEMAP[table].get(k)} "
                     f"= '{escape_string(str(v)).decode('utf-8')}'" for
                     k, v in asdict(data).items()
                     if v is not None and k in TABLEMAP[table])
    sql += " WHERE "
    sql += "AND ".join(f"{TABLEMAP[table].get(k)} = "
                       f"'{escape_string(str(v)).decode('utf-8')}'" for
                       k, v in asdict(where).items()
                       if v is not None and k in TABLEMAP[table])
    with conn.cursor() as cursor:
        cursor.execute(sql)
        return cursor.rowcount


def fetchone(conn: Any,
             table: str,
             where: Dataclass) -> Optional[Dataclass]:
    """Run a SELECT on a table. Returns only one result!"""
    if not any(astuple(where)):
        return None
    sql = f"SELECT * FROM {table} "
    sql += "WHERE "
    sql += "AND ".join(f"{TABLEMAP[table].get(k)} = "
                       f"'{escape_string(str(v)).decode('utf-8')}'" for
                       k, v in asdict(where).items()
                       if v is not None and k in TABLEMAP[table])
    with conn.cursor() as cursor:
        cursor.execute(sql)
        return DATACLASSMAP[table](*cursor.fetchone())
