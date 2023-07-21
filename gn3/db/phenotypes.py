# pylint: disable=[R0902, R0903]
"""This contains all the necessary functions that access the phenotypes from
the db"""
from typing import Optional
from dataclasses import dataclass

from MySQLdb.cursors import DictCursor

from gn3.db_utils import Connection as DBConnection

from .query_tools import mapping_to_query_columns


@dataclass(frozen=True)
class Phenotype:
    """Data Type that represents a Phenotype"""
    id_: Optional[int] = None
    pre_pub_description: Optional[str] = None
    post_pub_description: Optional[str] = None
    original_description: Optional[str] = None
    units: Optional[str] = None
    pre_pub_abbreviation: Optional[str] = None
    post_pub_abbreviation: Optional[str] = None
    lab_code: Optional[str] = None
    submitter: Optional[str] = None
    owner: Optional[str] = None
    authorized_users: Optional[str] = None


# Mapping from the Phenotype dataclass to the actual column names in the
# database
phenotype_mapping = {
    "id_": "id",
    "pre_pub_description": "Pre_publication_description",
    "post_pub_description": "Post_publication_description",
    "original_description": "Original_description",
    "units": "Units",
    "pre_pub_abbreviation": "Pre_publication_abbreviation",
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
    "pubmed_id": "PubMed_ID",
    "abstract": "Abstract",
    "authors": "Authors",
    "title": "Title",
    "journal": "Journal",
    "volume": "Volume",
    "pages": "Pages",
    "month": "Month",
    "year": "Year",
}

def fetch_trait(conn: DBConnection, dataset_id: int, trait_name: str) -> dict:
    """Fetch phenotype 'traits' by `dataset_id` and `trait_name`."""
    query = (
        "SELECT "
        "pxr.Id AS id_, pxr.Id as trait_name, pxr.PhenotypeId AS phenotype_id, "
        "pxr.PublicationId AS publication_id, pxr.DataId AS data_id, "
        "pxr.mean, pxr.locus, pxr.LRS as lrs, pxr.additive, "
        "pxr.Sequence as sequence, pxr.comments "
        "FROM PublishFreeze AS pf INNER JOIN InbredSet AS iset "
        "ON pf.InbredSetId=iset.Id "
        "INNER JOIN PublishXRef AS pxr ON iset.Id=pxr.InbredSetId "
        "WHERE pf.Id=%(dataset_id)s AND pxr.Id=%(trait_name)s")
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            query, {"dataset_id": dataset_id, "trait_name": trait_name})
        return cursor.fetchone()

def fetch_metadata(conn: DBConnection, phenotype_id: int) -> dict:
    """Get the phenotype metadata by ID."""
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cols = ', '.join(mapping_to_query_columns(phenotype_mapping))
        cursor.execute(
            (f"SELECT Id as id, {cols} FROM Phenotype "
             "WHERE Id=%(phenotype_id)s"),
            {"phenotype_id": phenotype_id})
        return cursor.fetchone()

def fetch_publication_by_id(conn: DBConnection, publication_id: int) -> dict:
    """Fetch the publication by its ID."""
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cols = ', '.join(mapping_to_query_columns(publication_mapping))
        cursor.execute(
            (f"SELECT Id as id, {cols} FROM Publication "
             "WHERE Id=%(publication_id)s"),
            {"publication_id": publication_id})
        return cursor.fetchone()

def fetch_publication_by_pubmed_id(conn: DBConnection, pubmed_id: int) -> dict:
    """Fetch the publication by its PUBMED ID."""
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cols = ', '.join(mapping_to_query_columns(publication_mapping))
        cursor.execute(
            (f"SELECT Id as id, {cols} FROM Publication "
             "WHERE PubMed_Id=%(pubmed_id)s"),
            {"pubmed_id": pubmed_id})
        return cursor.fetchone()
