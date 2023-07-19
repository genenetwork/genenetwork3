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

def fetch_probeset_metadata_by_name(conn: DBConnection, name: str) -> dict:
    """Fetch a ProbeSet's metadata by its `name`."""
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cols = ", ".join(mapping_to_query_columns(probeset_mapping))
        cursor.execute((f"SELECT Id as id, {cols} "
                        "FROM ProbeSet "
                        "WHERE Name = %(name)s"),
                       {"name": name})
        return cursor.fetchone()
