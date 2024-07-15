# Copyright (C) University of Tennessee Health Science Center, Memphis, TN.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# This program is available from Source Forge: at GeneNetwork Project
# (sourceforge.net/projects/genenetwork/).
#
# Contact Drs. Robert W. Williams and Xiaodong Zhou (2010)
# at rwilliams@uthsc.edu and xzhou15@uthsc.edu
#
#
#
# This module is used by GeneNetwork project (www.genenetwork.org)
#
# Created by GeneNetwork Core Team 2010/08/10
# Updated on Lei Yan 2011/02/08
# created by Lei Yan 02/08/2011

"""
Script responsible for updating the GenerRIF_BASIC table
"""

import argparse
import csv
import gzip
import pathlib
from tempfile import TemporaryDirectory
from typing import Dict, Generator
import requests

from gn3.db_utils import database_connection

TAX_IDS = {"10090": 1, "9606": 4, "10116": 2, "3702": 3}

GENE_INFO_URL = "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz"
GENERIFS_BASIC_URL = "https://ftp.ncbi.nih.gov/gene/GeneRIF/generifs_basic.gz"

# TODO: Set this to a version that isn't already in use in the RIF database
VERSION_ID = 4


def download_file(url: str, dest: pathlib.Path):
    """Saves the contents of url in dest"""
    with requests.get(url, stream=True) as resp:
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


def update_rif(sqluri: str):
    """Update GeneRIF_BASIC table"""
    with TemporaryDirectory() as _tmpdir:
        tmpdir = pathlib.Path(_tmpdir)
        gene_info_path = tmpdir / "gene_info.gz"
        download_file(GENE_INFO_URL, gene_info_path)

        generif_basics_path = tmpdir / "generif_basics.gz"
        download_file(
            GENERIFS_BASIC_URL,
            generif_basics_path,
        )
        genedict = parse_gene_info_from_ncbi(gene_info_path)
        insert_query = """
                                INSERT IGNORE INTO GeneRIF_BASIC
                                SET GeneRIF_BASIC.`SpeciesId`=%s,
                                        GeneRIF_BASIC.`GeneId`=%s,
                                        GeneRIF_BASIC.`symbol`=%s,
                                        GeneRIF_BASIC.`PubMed_ID`=%s,
                                        GeneRIF_BASIC.`createtime`=%s,
                                        GeneRIF_BASIC.`comment`=%s,
                                        GeneRIF_BASIC.`TaxID`=%s,
                                        VersionId=%s
                                """

        with database_connection(sql_uri=sqluri) as con:
            with con.cursor() as cursor:
                for row in read_tsv_file(generif_basics_path):
                    if row["#Tax ID"] not in TAX_IDS:
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
                    cursor.execute(insert_query, insert_values)
        print(
            f"Generif_BASIC table updated. In case of error, you can do use VersionID={VERSION_ID} to find rows inserted with this script"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Update Generif_BASIC table")
    parser.add_argument(
        "--sql-uri",
        required=True,
        help="MYSQL uri path in the form mysql://user:password@localhost/gn2",
    )
    args = parser.parse_args()
    update_rif(args.sql_uri)
