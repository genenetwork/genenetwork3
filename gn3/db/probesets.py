"""Functions and utilities to handle ProbeSets from the database."""
from typing import Optional
from dataclasses import dataclass

from MySQLdb.cursors import DictCursor

from gn3.db_utils import Connection as DBConnection

from .query_tools import mapping_to_query_columns

@dataclass(frozen=True)
class Probeset: # pylint: disable=[too-many-instance-attributes]
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
    "id_": "ProbeSet.Id",
    "name": "ProbeSet.Name",
    "symbol": "ProbeSet.symbol",
    "description": "ProbeSet.description",
    "probe_target_description": "ProbeSet.Probe_Target_Description",
    "chr_": "ProbeSet.Chr",
    "mb": "ProbeSet.Mb",
    "alias": "ProbeSet.alias",
    "geneid": "ProbeSet.GeneId",
    "homologeneid": "ProbeSet.HomoloGeneID",
    "unigeneid": "ProbeSet.UniGeneId",
    "omim": "ProbeSet.OMIM",
    "refseq_transcriptid": "ProbeSet.RefSeq_TranscriptId",
    "blatseq": "ProbeSet.BlatSeq",
    "targetseq": "ProbeSet.TargetSeq",
    "strand_probe": "ProbeSet.Strand_Probe",
    "probe_set_target_region": "ProbeSet.Probe_set_target_region",
    "probe_set_specificity": "ProbeSet.Probe_set_specificity",
    "probe_set_blat_score": "ProbeSet.Probe_set_BLAT_score",
    "probe_set_blat_mb_start": "ProbeSet.Probe_set_Blat_Mb_start",
    "probe_set_blat_mb_end": "ProbeSet.Probe_set_Blat_Mb_end",
    "probe_set_strand": "ProbeSet.Probe_set_strand",
    "probe_set_note_by_rw": "ProbeSet.Probe_set_Note_by_RW",
    "flag": "ProbeSet.flag"
}

def fetch_probeset_metadata_by_name(conn: DBConnection, trait_name: str, dataset_name: str) -> dict:
    """Fetch a ProbeSet's metadata by its `name`."""
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cols = ", ".join(mapping_to_query_columns(probeset_mapping))
        cursor.execute((f"SELECT {cols} "
                        "FROM ProbeSetFreeze "
                        "INNER JOIN ProbeSetXRef ON ProbeSetXRef.`ProbeSetFreezeId` = ProbeSetFreeze.`Id` "
                        "INNER JOIN ProbeSet ON ProbeSet.`Id` = ProbeSetXRef.`ProbeSetId` "
                        "WHERE ProbeSet.Name = %(trait_name)s AND ProbeSetFreeze.Name = %(ds_name)s"),
                       {"trait_name": trait_name, "ds_name": dataset_name})
        return cursor.fetchone()

def update_probeset(conn, probeset_id, data:dict) -> int:
    """Update the ProbeSet table with given `data`."""
    cols = ", ".join(f"{probeset_mapping[col]}=%({col})s"
                     for col in data
                     if (col not in ("id_", "id") and
                         col in probeset_mapping))
    if not bool(cols):
        return 0
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            f"UPDATE ProbeSet SET {cols} WHERE Id=%(probeset_id)s",
            {"probeset_id": probeset_id, **data})
        return cursor.rowcount
