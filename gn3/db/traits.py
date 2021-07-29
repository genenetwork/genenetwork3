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

def retrieve_trait_dataset_name(
        trait_type: str, threshold: int, name: str, connection: Any):
    """
    Retrieve the name of a trait given the trait's name

    This is extracted from the `webqtlDataset.retrieveName` function as is
    implemented at
    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/base/webqtlDataset.py#L140-L169
    """
    columns = "Id, Name, FullName, ShortName{}".format(
        ", DataScale" if trait_type == "ProbeSet" else "")
    query = (
        "SELECT {columns} "
        "FROM {trait_type}Freeze "
        "WHERE "
        "public > %(threshold)s "
        "AND "
        "(Name = %(name)s OR FullName = %(name)s OR ShortName = %(name)s)").format(
            columns=columns, trait_type=trait_type)
    with connection.cursor() as cursor:
        cursor.execute(query, {"threshold": threshold, "name": name})
        return cursor.fetchone()

PUBLISH_TRAIT_INFO_QUERY = (
    "SELECT "
    "PublishXRef.Id, Publication.PubMed_ID, "
    "Phenotype.Pre_publication_description, "
    "Phenotype.Post_publication_description, "
    "Phenotype.Original_description, "
    "Phenotype.Pre_publication_abbreviation, "
    "Phenotype.Post_publication_abbreviation, "
    "Phenotype.Lab_code, Phenotype.Submitter, Phenotype.Owner, "
    "Phenotype.Authorized_Users, CAST(Publication.Authors AS BINARY), "
    "Publication.Title, Publication.Abstract, Publication.Journal, "
    "Publication.Volume, Publication.Pages, Publication.Month, "
    "Publication.Year, PublishXRef.Sequence, Phenotype.Units, "
    "PublishXRef.comments "
    "FROM "
    "PublishXRef, Publication, Phenotype, PublishFreeze "
    "WHERE "
    "PublishXRef.Id = %(trait_name)s AND "
    "Phenotype.Id = PublishXRef.PhenotypeId AND "
    "Publication.Id = PublishXRef.PublicationId AND "
    "PublishXRef.InbredSetId = PublishFreeze.InbredSetId AND "
    "PublishFreeze.Id =%(trait_dataset_id)s")

def retrieve_publish_trait_info(trait_data_source: Dict[str, Any], conn: Any):
    """Retrieve trait information for type `Publish` traits.

    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/base/webqtlTrait.py#L399-L421"""
    with conn.cursor() as cursor:
        cursor.execute(
            PUBLISH_TRAIT_INFO_QUERY,
            {
                k:v for k, v in trait_data_source.items()
                if k in ["trait_name", "trait_dataset_id"]
            })
        return cursor.fetchone()

PROBESET_TRAIT_INFO_QUERY = (
    "SELECT "
    "ProbeSet.name, ProbeSet.symbol, ProbeSet.description, "
    "ProbeSet.probe_target_description, ProbeSet.chr, ProbeSet.mb, "
    "ProbeSet.alias, ProbeSet.geneid, ProbeSet.genbankid, ProbeSet.unigeneid, "
    "ProbeSet.omim, ProbeSet.refseq_transcriptid, ProbeSet.blatseq, "
    "ProbeSet.targetseq, ProbeSet.chipid, ProbeSet.comments, "
    "ProbeSet.strand_probe, ProbeSet.strand_gene, "
    "ProbeSet.probe_set_target_region, ProbeSet.proteinid, "
    "ProbeSet.probe_set_specificity, ProbeSet.probe_set_blat_score, "
    "ProbeSet.probe_set_blat_mb_start, ProbeSet.probe_set_blat_mb_end, "
    "ProbeSet.probe_set_strand, ProbeSet.probe_set_note_by_rw, "
    "ProbeSet.flag "
    "FROM "
    "ProbeSet, ProbeSetFreeze, ProbeSetXRef "
    "WHERE "
    "ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND "
    "ProbeSetXRef.ProbeSetId = ProbeSet.Id AND "
    "ProbeSetFreeze.Name = %(trait_dataset_name)s AND "
    "ProbeSet.Name = %(trait_name)s")

def retrieve_probeset_trait_info(trait_data_source: Dict[str, Any], conn: Any):
    """Retrieve trait information for type `ProbeSet` traits.

    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/base/webqtlTrait.py#L424-L435"""
    with conn.cursor() as cursor:
        cursor.execute(
            PROBESET_TRAIT_INFO_QUERY,
            {
                k:v for k, v in trait_data_source.items()
                if k in ["trait_name", "trait_dataset_name"]
            })
        return cursor.fetchone()

GENO_TRAIT_INFO_QUERY = (
    "SELECT "
    "Geno.name, Geno.chr, Geno.mb, Geno.source2, Geno.sequence "
    "FROM "
    "Geno, GenoFreeze, GenoXRef "
    "WHERE "
    "GenoXRef.GenoFreezeId = GenoFreeze.Id AND GenoXRef.GenoId = Geno.Id AND "
    "GenoFreeze.Name = %(trait_dataset_name)s AND Geno.Name = %(trait_name)s")

def retrieve_geno_trait_info(trait_data_source: Dict[str, Any], conn: Any):
    """Retrieve trait information for type `Geno` traits.

    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/base/webqtlTrait.py#L438-L449"""
    with conn.cursor() as cursor:
        cursor.execute(
            GENO_TRAIT_INFO_QUERY,
            {
                k:v for k, v in trait_data_source.items()
                if k in ["trait_name", "trait_dataset_name"]
            })
        return cursor.fetchone()

TEMP_TRAIT_INFO_QUERY = (
    "SELECT name, description FROM Temp "
    "WHERE Name = %(trait_name)s")

def retrieve_temp_trait_info(trait_data_source: Dict[str, Any], conn: Any):
    """Retrieve trait information for type `Temp` traits.

    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/base/webqtlTrait.py#L450-452"""
    with conn.cursor() as cursor:
        cursor.execute(
            TEMP_TRAIT_INFO_QUERY,
            {
                k:v for k, v in trait_data_source.items()
                if k in ["trait_name"]
            })
        return cursor.fetchone()

def retrieve_trait_info(
        trait_type: str, trait_name: str, trait_dataset_id: int,
        trait_dataset_name: str, conn: Any):
    """Retrieves the trait information.

    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/base/webqtlTrait.py#L397-L456

    This function, or the dependent functions, might be incomplete as they are
    currently."""
    trait_info_function_table = {
        "Publish": retrieve_publish_trait_info,
        "ProbeSet": retrieve_probeset_trait_info,
        "Geno": retrieve_geno_trait_info,
        "Temp": retrieve_temp_trait_info
    }
    return trait_info_function_table[trait_type](
        {
            "trait_name": trait_name,
            "trait_dataset_id": trait_dataset_id,
            "trait_dataset_name":trait_dataset_name
        },
        conn)
