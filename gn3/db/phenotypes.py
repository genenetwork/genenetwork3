# pylint: disable=[R0902]
"""This contains all the necessary functions that access the phenotypes from
the db"""
from dataclasses import dataclass, asdict, astuple

from typing import Any, Optional
from MySQLdb import escape_string


@dataclass(frozen=True)
class Phenotype:
    """Data Type that represents a Phenotype"""
    id_: Optional[int] = None
    pre_pub_description: Optional[str] = None
    post_pub_description: Optional[str] = None
    original_description: Optional[str] = None
    units: Optional[str] = None
    pre_pub_abbrevition: Optional[str] = None
    post_pub_abbreviation: Optional[str] = None
    lab_code: Optional[str] = None
    submitter: Optional[str] = None
    owner: Optional[str] = None
    authorized_users: Optional[str] = None


@dataclass(frozen=True)
class PublishXRef:
    """Data Type that represents the table PublishXRef"""
    id_: Optional[int] = None
    inbred_set_id: Optional[str] = None
    phenotype_id: Optional[int] = None
    publication_id: Optional[str] = None
    data_id: Optional[int] = None
    mean: Optional[float] = None
    locus: Optional[str] = None
    lrs: Optional[float] = None
    additive: Optional[float] = None
    sequence: Optional[int] = None
    comments: Optional[str] = None


# Mapping from the Phenotype dataclass to the actual column names in the
# database
phenotype_column_mapping = {
    "id_": "id",
    "pre_pub_description": "Pre_publication_description",
    "post_pub_description": "Post_publication_description",
    "original_description": "Original_description",
    "units": "Units",
    "pre_pub_abbrevition": "Pre_publication_abbreviation",
    "post_pub_abbreviation": "Post_publication_abbreviation",
    "lab_code": "Lab_code",
    "submitter": "Submitter",
    "owner": "Owner",
    "authorized_users": "Authorized_Users",
}


def update_phenotype(conn: Any,
                     data: Phenotype,
                     where: Phenotype) -> Optional[int]:
    """Update phenotype metadata with DATA that depends on the WHERE clause"""
    if not any(astuple(data) + astuple(where)):
        return None
    sql = "UPDATE Phenotype SET "
    sql += ", ".join(f"{phenotype_column_mapping.get(k)} "
                     f"= '{escape_string(str(v)).decode('utf-8')}'" for
                     k, v in asdict(data).items()
                     if v is not None and k in phenotype_column_mapping)
    sql += " WHERE "
    sql += "AND ".join(f"{phenotype_column_mapping.get(k)} = "
                       f"'{escape_string(str(v)).decode('utf-8')}'" for
                       k, v in asdict(where).items()
                       if v is not None and k in phenotype_column_mapping)
    with conn.cursor() as cursor:
        cursor.execute(sql)
        return cursor.rowcount
