# pylint: disable=[R0902, R0903]
"""This contains all the necessary functions that access the phenotypes from
the db"""
from dataclasses import dataclass, asdict, astuple

from typing import Any, Dict, Optional
from MySQLdb import escape_string

from typing_extensions import Protocol


class Dataclass(Protocol):
    """Type Definition for a Dataclass"""
    __dataclass_fields__: Dict


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


# Mapping from the PublishXRef dataclass to the actual column names in the
# database
publish_x_ref_mapping = {
    "id_": "Id",
    "inbred_set_id": "InbredSetId",
    "phenotype_id": "PhenotypeId",
    "publication_id": "PublicationId",
    "data_id": "DataId",
    "mean": "mean",
    "locus": "locus",
    "lrs": "lrs",
    "additive": "additive",
    "sequence": "sequence",
    "comments": "comments",
}


@dataclass(frozen=True)
class Publication:
    """Data Type that represents the table Publication"""
    id_: Optional[int] = None
    pubmed_id: Optional[int] = None
    abstract: Optional[str] = None
    authors: Optional[str] = None
    title: Optional[str] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    pages: Optional[str] = None
    month: Optional[str] = None
    year: Optional[str] = None


publication_mapping = {
    "id_": "id",
    "PubMed_ID": "pubmed_id",
    "Abstract": "abstract",
    "Authors": "authors",
    "Title": "title",
    "Journal": "journal",
    "Volume": "volume",
    "Pages": "pages",
    "Month": "month",
    "Year": "year",
}


TABLEMAP = {
    "Phenotype": phenotype_column_mapping,
    "PublishXRef": publish_x_ref_mapping,
}


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
