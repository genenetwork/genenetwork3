"""This contains all the necessary functions that are required to add traits
to the published database"""
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Riset:
    """Class for keeping track of riset. A riset is a group e.g. rat HSNIH-Palmer,
BXD

    """
    name: Optional[str]
    r_id: Optional[int]


@dataclass(frozen=True)
class WebqtlCaseData:
    """Class for keeping track of one case data in one trait"""
    value: Optional[float] = None
    variance: Optional[float] = None
    count: Optional[int] = None  # Number of Individuals

    def __str__(self):
        _str = ""
        if self.value:
            _str += f"value={self.value:.3f}"
        if self.variance:
            _str += f" variance={self.variance:.3f}"
        if self.count:
            _str += " n_data={self.count}"
        return _str


def lookup_webqtldataset_name(riset_name: str, conn: Any):
    """Given a group name(riset), return it's name e.g. BXDPublish,
HLCPublish."""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT PublishFreeze.Name FROM "
            "PublishFreeze, InbredSet WHERE "
            "PublishFreeze.InbredSetId = InbredSet.Id "
            "AND InbredSet.Name = '%s'" % riset_name)
        _result, *_ = cursor.fetchone()
        return _result


def get_riset(data_type: str, name: str, conn: Any):
    """Get the groups given the data type and it's PublishFreeze or GenoFreeze
name

    """
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
    return Riset(_name, _id)


def insert_publication(pubmed_id: int, publication: Optional[Dict],
                       conn: Any):
    """Creates a new publication record if it's not available"""
    sql = ("SELECT Id FROM Publication where "
           "PubMed_ID = %d" % pubmed_id)
    _id = None
    with conn.cursor() as cursor:
        cursor.execute(sql)
        _id = cursor.fetchone()
    if not _id and publication:
        # The Publication contains the fields: 'authors', 'title', 'abstract',
        # 'journal','volume','pages','month','year'
        insert_query = ("INSERT into Publication (%s) Values (%s)" %
                        (", ".join(publication.keys()),
                         ", ".join(['%s'] * len(publication))))
        with conn.cursor() as cursor:
            cursor.execute(insert_query, tuple(publication.values()))
