#!/usr/bin/env python3

"""
Script responsible for updating the GeneRIF_BASIC table
"""

import argparse
import csv
import datetime
import gzip
import logging
import pathlib
import os
from tempfile import TemporaryDirectory
from typing import Dict, Generator

import requests
from MySQLdb.cursors import DictCursor

from gn3.db_utils import database_connection

TAX_IDS = {"10090": 1, "9606": 4, "10116": 2, "3702": 3}

GENE_INFO_URL = "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz"
GENERIFS_BASIC_URL = "https://ftp.ncbi.nih.gov/gene/GeneRIF/generifs_basic.gz"

VERSION_ID = 5


INSERT_QUERY = """ INSERT INTO GeneRIF_BASIC
(SpeciesId, GeneId, symbol, PubMed_Id, createtime, comment, TaxID, VersionId)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""


def download_file(url: str, dest: pathlib.Path):
    """Saves the contents of url in dest"""
    with requests.get(url, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as downloaded_file:
            for chunk in resp.iter_content(chunk_size=8192):
                downloaded_file.write(chunk)


def read_tsv_file(fname: pathlib.Path) -> Generator:
    """Load tsv file from NCBI"""
    with gzip.open(fname, mode="rt") as gz_file:
        reader = csv.DictReader(gz_file, delimiter="\t", quoting=csv.QUOTE_NONE)
        yield from reader


def parse_gene_info_from_ncbi(fname: pathlib.Path) -> Dict[str, str]:
    """Parse gene_info into geneid: symbol pairs"""
    genedict: Dict[str, str] = {}
    for row in read_tsv_file(fname):
        if row["#tax_id"] not in TAX_IDS:
            continue
        gene_id, symbol = row["GeneID"], row["Symbol"]
        genedict[gene_id] = symbol
    return genedict


def build_already_exists_cache(conn) -> dict:
    """
    Build cache for all GeneId, SpeciesID, createtime, PubMed_ID combinations.
    Helps prevent duplicate inserts.
    """
    cache = {}
    query = """SELECT
        COUNT(*) as cnt, GeneId, SpeciesId, createtime, PubMed_ID
        from GeneRIF_BASIC
        GROUP BY GeneId, SpeciesId, createtime, PubMed_Id """

    with conn.cursor(DictCursor) as cursor:
        cursor.execute(query)
        while row := cursor.fetchone():
            key = (
                str(row["GeneId"]),
                str(row["SpeciesId"]),
                row["createtime"],
                str(row["PubMed_ID"]),
            )
            cache[key] = row["cnt"]
    return cache


def should_add_rif_row(row: dict, exists_cache: dict) -> bool:
    """Checks if we can add a rif_row, prevent duplicate errors from Mysql"""
    species_id = str(TAX_IDS[row["#Tax ID"]])
    insert_date = datetime.datetime.fromisoformat(row["last update timestamp"])
    search_key = (
        row["Gene ID"],
        species_id,
        insert_date,
        row["PubMed ID (PMID) list"],
    )
    if search_key not in exists_cache:
        exists_cache[search_key] = 1
        return True
    return False


def update_rif(sqluri: str):
    """Update GeneRIF_BASIC table"""
    with TemporaryDirectory() as _tmpdir:
        tmpdir = pathlib.Path(_tmpdir)
        gene_info_path = tmpdir / "gene_info.gz"
        logging.debug("Fetching gene_info data from: %s", GENE_INFO_URL)
        download_file(GENE_INFO_URL, gene_info_path)

        logging.debug("Fetching gene_rif_basics data from: %s", GENERIFS_BASIC_URL)
        generif_basics_path = tmpdir / "generif_basics.gz"
        download_file(
            GENERIFS_BASIC_URL,
            generif_basics_path,
        )

        logging.debug("Parsing gene_info data")
        genedict = parse_gene_info_from_ncbi(gene_info_path)
        with database_connection(sql_uri=sqluri) as con:
            exists_cache = build_already_exists_cache(con)
            cursor = con.cursor()
            skipped_if_exists, added = 0, 0
            for row in read_tsv_file(generif_basics_path):
                if row["#Tax ID"] not in TAX_IDS:
                    continue
                if not should_add_rif_row(row, exists_cache):
                    skipped_if_exists += 1
                    continue
                species_id = TAX_IDS[row["#Tax ID"]]
                symbol = genedict.get(row["Gene ID"], "")
                insert_values = (
                    species_id,  # SpeciesId
                    row["Gene ID"],  # GeneId
                    symbol,  # symbol
                    row["PubMed ID (PMID) list"],  # PubMed_ID
                    row["last update timestamp"],  # createtime
                    row["GeneRIF text"],  # comment
                    row["#Tax ID"],  # TaxID
                    VERSION_ID,  # VersionId
                )
                cursor.execute(INSERT_QUERY, insert_values)
                added += 1
                if added % 40_000 == 0:
                    logging.debug("Added 40,000 rows to database")
        logging.info(
            "Generif_BASIC table updated. Added %s. Skipped %s because they "
            "already exists. In case of error, you can use VersionID=%s to find "
            "rows inserted with this script", added, skipped_if_exists,
            VERSION_ID
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=os.environ.get("LOGLEVEL", "DEBUG"),
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %Z",
    )
    parser = argparse.ArgumentParser("Update Generif_BASIC table")
    parser.add_argument(
        "--sql-uri",
        required=True,
        help="MYSQL uri path in the form mysql://user:password@localhost/gn2",
    )
    args = parser.parse_args()
    update_rif(args.sql_uri)
