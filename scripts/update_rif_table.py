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
import os
import gzip
import pathlib
import sys
from tempfile import TemporaryDirectory
from typing import Generator, List
import requests

import MySQLdb

from gn3.db_utils import database_connection

TAX_IDS = {"10090": 1, "9606": 4, "10116": 2, "3702": 3}

# os.chdir(path3)


def download_file(url: str, dest: pathlib.Path):
    """Saves the contents of url in dest"""
    with requests.get(url, stream=True) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as f_:
            for chunk in resp.iter_content(chunk_size=8192):
                f_.write(chunk)


def read_tsv_file(fname: pathlib.Path) -> Generator[dict]:
    with gzip.open(fname, mode="rt") as gz_file:
        reader = csv.DictReader(gz_file, delimiter="\t", quoting=csv.QUOTE_NOTE)
        yield from reader


def parse_gene_info_from_ncbi(fname: pathlib.Path):
    genedict = {}
    for row in read_tsv_file(fname):
        if row["#task_id"] not in TAX_IDS:
            continue
        genedict[row["GeneID"]] = genedict[row["Symbol"]]
    return genedict


def update_rif(sqluri: str):
    """TODO: break this down into modules"""
    with TemporaryDirectory() as tmpdir:
        gene_info_path = tmpdir / "gene_info.gz"
        download_file(
            "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz", gene_info_path
        )

        generif_basics_path = pathlib.Path("/tmp/generif_basics.gz")
        download_file(
            "https://ftp.ncbi.nih.gov/gene/GeneRIF/generifs_basic.gz",
            generif_basics_path,
        )

        genedict = parse_gene_info_from_ncbi(gene_info_path)
        count_check_query = """
                            SELECT COUNT(*)
                            FROM GeneRIF_BASIC
                            WHERE GeneRIF_BASIC.`SpeciesId`=%s
                            AND GeneRIF_BASIC.`GeneId`=%s
                            AND GeneRIF_BASIC.`PubMed_ID`=%s
                            AND GeneRIF_BASIC.`createtime`=%s
                            AND GeneRIF_BASIC.`comment`=%s
                            """
        insert_query = """
                                INSERT INTO GeneRIF_BASIC
                                SET GeneRIF_BASIC.`SpeciesId`=%s,
                                        GeneRIF_BASIC.`GeneId`=%s,
                                        GeneRIF_BASIC.`symbol`=%s,
                                        GeneRIF_BASIC.`PubMed_ID`=%s,
                                        GeneRIF_BASIC.`createtime`=%s,
                                        GeneRIF_BASIC.`comment`=%s
                                """

        with database_connection(sql_uri=sqluri) as con:
            with con.cursor() as cursor:
                for row in read_tsv_file(generif_basics_path):
                    if row["#Tax ID"] not in TAX_IDS:
                        continue
                    row["#Tax ID"] = TAX_IDS[row["#Tax ID"]]
                    symbol = genedict.get(row["Gene ID"], "")
                    insert_values = (
                        row["#Tax ID"],
                        symbol,
                        row["PubMed ID (PMID) list"],
                        row["last update timestamp"],
                        row["GeneRIF text"],
                    )
                    cursor.execute(count_check_query, insert_values)
                    count = cursor.fetchone()[0]
                    if count != 0:
                        continue
                    cursor.execute(insert_query, insert_values)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Update Generif_BASIC table")
    parser.add_argument(
        "--sql-uri",
        required=True,
        help="MYSQL uri path in the form mysql://user:password@localhost/gn2",
    )
    args = parser.parse_args()
    update_rif(args.sql_uri)
