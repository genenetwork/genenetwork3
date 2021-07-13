# pylint: disable=[R0902, R0903]
"""This contains all the necessary functions that access the phenotypes from
the db"""
from dataclasses import dataclass

from typing import Optional


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


@dataclass(frozen=True)
class Probeset:
    """Data Type that represents a Probeset"""
    id_: Optional[int] = None
    name: Optional[str] = None
    symbol: Optional[str] = None
    description: Optional[str] = None
    probe_target_description: Optional[str] = None
    chr_: Optional[str] = None
    mb: Optional[float] = None  # pylint: disable=C0103
    alias: Optional[str] = None
    geneid: Optional[str] = None
    homologeneid: Optional[str] = None
    unigeneid: Optional[str] = None
    omim: Optional[str] = None
    refseq_transcriptid: Optional[str] = None
    blatseq: Optional[str] = None
    targetseq: Optional[str] = None
    strand_probe: Optional[str] = None
    probe_set_target_region: Optional[str] = None
    probe_set_specificity: Optional[float] = None
    probe_set_blat_score: Optional[float] = None
    probe_set_blat_mb_start: Optional[float] = None
    probe_set_blat_mb_end: Optional[float] = None
    probe_set_strand: Optional[str] = None
    probe_set_note_by_rw: Optional[str] = None
    flag: Optional[str] = None


# Mapping from the Phenotype dataclass to the actual column names in the
# database
probeset_mapping = {
    "id_": "Id",
    "name": "Name",
    "symbol": "symbol",
    "description": "description",
    "probe_target_description": "Probe_Target_Description",
    "chr_": "Chr",
    "mb": "Mb",
    "alias": "alias",
    "geneid": "GeneId",
    "homologeneid": "HomoloGeneID",
    "unigeneid": "UniGeneId",
    "omim": "OMIM",
    "refseq_transcriptid": "RefSeq_TranscriptId",
    "blatseq": "BlatSeq",
    "targetseq": "TargetSeq",
    "strand_probe": "Strand_Probe",
    "probe_set_target_region": "Probe_set_target_region",
    "probe_set_specificity": "Probe_set_specificity",
    "probe_set_blat_score": "Probe_set_BLAT_score",
    "probe_set_blat_mb_start": "Probe_set_Blat_Mb_start",
    "probe_set_blat_mb_end": "Probe_set_Blat_Mb_end",
    "probe_set_strand": "Probe_set_strand",
    "probe_set_note_by_rw": "Probe_set_Note_by_RW",
    "flag": "flag"
}
