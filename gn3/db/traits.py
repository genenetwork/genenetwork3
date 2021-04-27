"""This contains all the necessary functions that are required to add traits
to the published database"""
from dataclasses import dataclass
from itertools import chain
from typing import Optional
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class riset:
    """Class for keeping track of riset. A riset is a group e.g. rat HSNIH-Palmer,
BXD

    """
    name: str
    r_id: int


@dataclass(frozen=True)
class webqtlCaseData:
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


def insert_publication_data(riset_id: int, strains: List, conn: Any):
    species_id = None
    with conn.cursor() as cursor:
        cursor.execute("SELECT SpeciesId from InbredSet where "
                       "Id=%s" % riset_id)
        species_id, *_ = cursor.fetchone()
        cursor.execute(
            "SELECT Id FROM Strain WHERE SpeciesId="
            "%s AND Name in (%s)"
            % (riset_id, ", ".join(f"'{strain}'" for strain in strains)))
        strain_ids = cursor.fetchall()
        data_id, *_ = cursor.execute("SELECT max(Id) "
                                     "from PublishData").fetchone()

        if strain_ids:
            strain_ids = list(chain(*strain_ids))
        for strain, strain_id in zip(strains, strain_ids):
            # TODO: Fetch this values correctly using sql
            value, variance, trait_np = 1, 1, 1
            if value:
                cursor.execute(
                    "INSERT INTO PublishData values (%d, %d, %s)" %
                    (data_id, strain_id, value))
            if variance:
                cursor.execute(
                    "INSERT INTO PublishSE values (%d, %d, %s)" %
                    (data_id, strain_id, variance))
            if trait_np:
                cursor.execute(
                    "INSERT INTO NStrain values (%d, %d, %s)" %
                    (data_id, strain_id, trait_np))
        inbred_set_id = lookup_webqtldataset_name(riset_name="",
                                                  conn=conn)
        cursor.execute(
            "SELECT max(Sequence) FROM PublishXRef where "
            "InbredSetId = %d and PhenotypeId = %d and PublicationId = %d" %
            (inbred_set_id, phenotype_id, publication_id))


def insert_phenotype(phenotype: Optional[Dict], conn: Any):
    insert_query = ("INSERT into Phenotype (%s) Values (%s)" %
                    (", ".join(phenotype.keys()),
                     ", ".join(['%s'] * len(phenotype))))
    with conn.cursor() as cursor:
        cursor.execute(insert_query, tuple(phenotype.values()))
