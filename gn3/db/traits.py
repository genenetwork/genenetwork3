"""This contains all the necessary functions that are required to add traits
to the published database"""
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class riset:
    """Class for keeping track of riset. A riset is a group e.g. rat HSNIH-Palmer,
BXD

    """
    name: str
    r_id: int


def get_riset(data_type: str, name: str, conn: Any):
    query, _name, _id = None, None, None
    if data_type == "Publish":
        query = ("SELECT InbredSet.Name, InbredSet.Id FROM InbredSet, "
                 "PublishFreeze WHERE PublishFreeze.InbredSetId = "
                 "InbredSet.Id AND PublishFreeze.Name = '%s'" % name)
    elif data_type == "Geno":
        query = ("SELECT InbredSet.Name, InbredSet.Id FROM InbredSet, "
                 "GenoFreeze WHERE GenoFreeze.InbredSetId = "
                 "InbredSet.Id AND GenoFreeze.Name = '%s'" % name)
    elif data_type == "ProbeSet":
        query = ("SELECT InbredSet.Name, InbredSet.Id FROM "
                 "InbredSet, ProbeSetFreeze, ProbeFreeze WHERE "
                 "ProbeFreeze.InbredSetId = InbredSet.Id AND "
                 "ProbeFreeze.Id = ProbeSetFreeze.ProbeFreezeId AND "
                 "ProbeSetFreeze.Name = '%s'" % name)
    if query:
        with conn.cursor() as cursor:
            _name, _id = cursor.fetchone()
            if _name == "BXD300":
                _name = "BXD"
    return riset(_name, _id)


def insert_publication(pubmed_id: int, publication: Optional[Dict],
                       conn: Any):
    """Creates a new publication record if it's not available"""
    sql = ("SELECT Id FROM Publication where "
           "PubMed_ID = %d" % pubmed_id)
    _id = None
    with conn.cursor() as cursor:
        cursor.execute(sql)
        _id = cursor.fetchone()
    if not _id:
        # The Publication contains the fields: 'authors', 'title', 'abstract',
        # 'journal','volume','pages','month','year'
        insert_query = ("INSERT into Publication (%s) Values (%s)" %
                        (", ".join(publication.keys()),
                         ", ".join(['%s'] * len(publication))))
        with conn.cursor() as cursor:
            cursor.execute(insert_query, tuple(publication.values()))


def insert_phenotype(phenotype: Optional[Dict], conn: Any):
    insert_query = ("INSERT into Phenotype (%s) Values (%s)" %
                    (", ".join(phenotype.keys()),
                     ", ".join(['%s'] * len(phenotype))))
    with conn.cursor() as cursor:
        cursor.execute(insert_query, tuple(phenotype.values()))
