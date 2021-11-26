"""
This module will hold functions that are used in the (partial) correlations
feature to access the database to retrieve data needed for computations.
"""

from functools import reduce
from typing import Any, Dict, Tuple, Union

from gn3.random import random_string
from gn3.data_helpers import partition_all
from gn3.db.species import translate_to_mouse_gene_id

from gn3.computations.partial_correlations import correlations_of_all_tissue_traits

def get_filename(conn: Any, target_db_name: str, text_files_dir: str) -> Union[
        str, bool]:
    """
    Retrieve the name of the reference database file with which correlations are
    computed.

    This is a migration of the
    `web.webqtl.correlation.CorrelationPage.getFileName` function in
    GeneNetwork1.
    """
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT Id, FullName from ProbeSetFreeze WHERE Name=%s",
            (target_db_name,))
        result = cursor.fetchone()
        if result:
            return "ProbeSetFreezeId_{tid}_FullName_{fname}.txt".format(
                tid=result[0],
                fname=result[1].replace(' ', '_').replace('/', '_'))

    return ""

def build_temporary_literature_table(
        conn: Any, species: str, gene_id: int, return_number: int) -> str:
    """
    Build and populate a temporary table to hold the literature correlation data
    to be used in computations.

    "This is a migration of the
    `web.webqtl.correlation.CorrelationPage.getTempLiteratureTable` function in
    GeneNetwork1.
    """
    def __translated_species_id(row, cursor):
        if species == "mouse":
            return row[1]
        query = {
            "rat": "SELECT rat FROM GeneIDXRef WHERE mouse=%s",
            "human": "SELECT human FROM GeneIDXRef WHERE mouse=%d"}
        if species in query.keys():
            cursor.execute(query[species], row[1])
            record = cursor.fetchone()
            if record:
                return record[0]
            return None
        return None

    temp_table_name = f"TOPLITERATURE{random_string(8)}"
    with conn.cursor as cursor:
        mouse_geneid = translate_to_mouse_gene_id(species, gene_id, conn)
        data_query = (
            "SELECT GeneId1, GeneId2, value FROM LCorrRamin3 "
            "WHERE GeneId1 = %(mouse_gene_id)s "
            "UNION ALL "
            "SELECT GeneId2, GeneId1, value FROM LCorrRamin3 "
            "WHERE GeneId2 = %(mouse_gene_id)s "
            "AND GeneId1 != %(mouse_gene_id)s")
        cursor.execute(
            (f"CREATE TEMPORARY TABLE {temp_table_name} ("
             "GeneId1 int(12) unsigned, "
             "GeneId2 int(12) unsigned PRIMARY KEY, "
             "value double)"))
        cursor.execute(data_query, mouse_gene_id=mouse_geneid)
        literature_data = [
            {"GeneId1": row[0], "GeneId2": row[1], "value": row[2]}
            for row in cursor.fetchall()
            if __translated_species_id(row, cursor)]

        cursor.execute(
            (f"INSERT INTO {temp_table_name} "
             "VALUES (%(GeneId1)s, %(GeneId2)s, %(value)s)"),
            literature_data[0:(2 * return_number)])

    return temp_table_name

def fetch_geno_literature_correlations(temp_table: str) -> str:
    """
    Helper function for `fetch_literature_correlations` below, to build query
    for `Geno*` tables.
    """
    return (
        f"SELECT Geno.Name, {temp_table}.value "
        "FROM Geno, GenoXRef, GenoFreeze "
        f"LEFT JOIN {temp_table} ON {temp_table}.GeneId2=ProbeSet.GeneId "
        "WHERE ProbeSet.GeneId IS NOT NULL "
        f"AND {temp_table}.value IS NOT NULL "
        "AND GenoXRef.GenoFreezeId = GenoFreeze.Id "
        "AND GenoFreeze.Name = %(db_name)s "
        "AND Geno.Id=GenoXRef.GenoId "
        "ORDER BY Geno.Id")

def fetch_probeset_literature_correlations(temp_table: str) -> str:
    """
    Helper function for `fetch_literature_correlations` below, to build query
    for `ProbeSet*` tables.
    """
    return (
        f"SELECT ProbeSet.Name, {temp_table}.value "
        "FROM ProbeSet, ProbeSetXRef, ProbeSetFreeze "
        "LEFT JOIN {temp_table} ON {temp_table}.GeneId2=ProbeSet.GeneId "
        "WHERE ProbeSet.GeneId IS NOT NULL "
        "AND {temp_table}.value IS NOT NULL "
        "AND ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id "
        "AND ProbeSetFreeze.Name = %(db_name)s "
        "AND ProbeSet.Id=ProbeSetXRef.ProbeSetId "
        "ORDER BY ProbeSet.Id")

def fetch_literature_correlations(
        species: str, gene_id: int, dataset: dict, return_number: int,
        conn: Any) -> dict:
    """
    Gather the literature correlation data and pair it with trait id string(s).

    This is a migration of the
    `web.webqtl.correlation.CorrelationPage.fetchLitCorrelations` function in
    GeneNetwork1.
    """
    temp_table = build_temporary_literature_table(
        conn, species, gene_id, return_number)
    query_fns = {
        "Geno": fetch_geno_literature_correlations,
        # "Temp": fetch_temp_literature_correlations,
        # "Publish": fetch_publish_literature_correlations,
        "ProbeSet": fetch_probeset_literature_correlations}
    with conn.cursor as cursor:
        cursor.execute(
            query_fns[dataset["dataset_type"]](temp_table),
            db_name=dataset["dataset_name"])
        results = cursor.fetchall()
        cursor.execute("DROP TEMPORARY TABLE %s", temp_table)
        return dict(results)

def fetch_symbol_value_pair_dict(
        symbol_list: Tuple[str, ...], data_id_dict: dict,
        conn: Any) -> Dict[str, Tuple[float, ...]]:
    """
    Map each gene symbols to the corresponding tissue expression data.

    This is a migration of the
    `web.webqtl.correlation.correlationFunction.getSymbolValuePairDict` function
    in GeneNetwork1.
    """
    data_ids = {
        symbol: data_id_dict.get(symbol) for symbol in symbol_list
        if data_id_dict.get(symbol) is not None
    }
    query = "SELECT Id, value FROM TissueProbeSetData WHERE Id IN %(data_ids)s"
    with conn.cursor() as cursor:
        cursor.execute(
            query,
            data_ids=tuple(data_ids.values()))
        value_results = cursor.fetchall()
        return {
            key: tuple(row[1] for row in value_results if row[0] == key)
            for key in data_ids.keys()
        }

    return {}

def fetch_gene_symbol_tissue_value_dict(
        symbol_list: Tuple[str, ...], data_id_dict: dict, conn: Any,
        limit_num: int = 1000) -> dict:#getGeneSymbolTissueValueDict
    """
    Wrapper function for `gn3.db.correlations.fetch_symbol_value_pair_dict`.

    This is a migrations of the
    `web.webqtl.correlation.correlationFunction.getGeneSymbolTissueValueDict` in
    GeneNetwork1.
    """
    count = len(symbol_list)
    if count != 0 and count <= limit_num:
        return fetch_symbol_value_pair_dict(symbol_list, data_id_dict, conn)

    if count > limit_num:
        return {
            key: value for dct in [
                fetch_symbol_value_pair_dict(sl, data_id_dict, conn)
                for sl in partition_all(limit_num, symbol_list)]
            for key, value in dct.items()
        }

    return {}

def fetch_tissue_probeset_xref_info(
        gene_name_list: Tuple[str, ...], probeset_freeze_id: int,
        conn: Any) -> Tuple[tuple, dict, dict, dict, dict, dict, dict]:
    """
    Retrieve the ProbeSet XRef information for tissues.

    This is a migration of the
    `web.webqtl.correlation.correlationFunction.getTissueProbeSetXRefInfo`
    function in GeneNetwork1."""
    with conn.cursor() as cursor:
        if len(gene_name_list) == 0:
            query = (
                "SELECT t.Symbol, t.GeneId, t.DataId, t.Chr, t.Mb, "
                "t.description, t.Probe_Target_Description "
                "FROM "
                "("
                "  SELECT Symbol, max(Mean) AS maxmean "
                "  FROM TissueProbeSetXRef "
                "  WHERE TissueProbeSetFreezeId=%(probeset_freeze_id)s "
                "  AND Symbol != '' "
                "  AND Symbol IS NOT NULL "
                "  GROUP BY Symbol"
                ") AS x "
                "INNER JOIN TissueProbeSetXRef AS t ON t.Symbol = x.Symbol "
                "AND t.Mean = x.maxmean")
            cursor.execute(query, probeset_freeze_id=probeset_freeze_id)
        else:
            query = (
                "SELECT t.Symbol, t.GeneId, t.DataId, t.Chr, t.Mb, "
                "t.description, t.Probe_Target_Description "
                "FROM "
                "("
                "  SELECT Symbol, max(Mean) AS maxmean "
                "  FROM TissueProbeSetXRef "
                "  WHERE TissueProbeSetFreezeId=%(probeset_freeze_id)s "
                "  AND Symbol in %(symbols)s "
                "  GROUP BY Symbol"
                ") AS x "
                "INNER JOIN TissueProbeSetXRef AS t ON t.Symbol = x.Symbol "
                "AND t.Mean = x.maxmean")
            cursor.execute(
                query, probeset_freeze_id=probeset_freeze_id,
                symbols=tuple(gene_name_list))

        results = cursor.fetchall()

    return reduce(
        lambda acc, item: (
            acc[0] + (item[0],),
            {**acc[1], item[0].lower(): item[1]},
            {**acc[1], item[0].lower(): item[2]},
            {**acc[1], item[0].lower(): item[3]},
            {**acc[1], item[0].lower(): item[4]},
            {**acc[1], item[0].lower(): item[5]},
            {**acc[1], item[0].lower(): item[6]}),
        results or tuple(),
        (tuple(), {}, {}, {}, {}, {}, {}))

def fetch_gene_symbol_tissue_value_dict_for_trait(
        gene_name_list: Tuple[str, ...], probeset_freeze_id: int,
        conn: Any) -> dict:
    """
    Fetches a map of the gene symbols to the tissue values.

    This is a migration of the
    `web.webqtl.correlation.correlationFunction.getGeneSymbolTissueValueDictForTrait`
    function in GeneNetwork1.
    """
    xref_info = fetch_tissue_probeset_xref_info(
        gene_name_list, probeset_freeze_id, conn)
    if xref_info[0]:
        return fetch_gene_symbol_tissue_value_dict(xref_info[0], xref_info[2], conn)
    return {}

def build_temporary_tissue_correlations_table(
        conn: Any, trait_symbol: str, probeset_freeze_id: int, method: str,
        return_number: int) -> str:
    """
    Build a temporary table to hold the tissue correlations data.

    This is a migration of the
    `web.webqtl.correlation.CorrelationPage.getTempTissueCorrTable` function in
    GeneNetwork1."""
    # We should probably pass the `correlations_of_all_tissue_traits` function
    # as an argument to this function and get rid of the one call immediately
    # following this comment.
    symbol_corr_dict, symbol_p_value_dict = correlations_of_all_tissue_traits(
        fetch_gene_symbol_tissue_value_dict_for_trait(
            (trait_symbol,), probeset_freeze_id, conn),
        fetch_gene_symbol_tissue_value_dict_for_trait(
            tuple(), probeset_freeze_id, conn),
        method)

    symbol_corr_list = sorted(
        symbol_corr_dict.items(), key=lambda key_val: key_val[1])

    temp_table_name = f"TOPTISSUE{random_string(8)}"
    create_query = (
        "CREATE TEMPORARY TABLE {temp_table_name}"
        "(Symbol varchar(100) PRIMARY KEY, Correlation float, PValue float)")
    insert_query = (
        f"INSERT INTO {temp_table_name}(Symbol, Correlation, PValue) "
        " VALUES (%(symbol)s, %(correlation)s, %(pvalue)s)")

    with conn.cursor() as cursor:
        cursor.execute(create_query)
        cursor.execute(
            insert_query,
            tuple({
                "symbol": symbol,
                "correlation": corr,
                "pvalue": symbol_p_value_dict[symbol]
            } for symbol, corr in symbol_corr_list[0: 2 * return_number]))

    return temp_table_name

def fetch_tissue_correlations(# pylint: disable=R0913
        dataset: dict, trait_symbol: str, probeset_freeze_id: int, method: str,
        return_number: int, conn: Any) -> dict:
    """
    Pair tissue correlations data with a trait id string.

    This is a migration of the
    `web.webqtl.correlation.CorrelationPage.fetchTissueCorrelations` function in
    GeneNetwork1.
    """
    temp_table = build_temporary_tissue_correlations_table(
        conn, trait_symbol, probeset_freeze_id, method, return_number)
    with conn.cursor() as cursor:
        cursor.execute(
            (
                f"SELECT ProbeSet.Name, {temp_table}.Correlation, "
                f"{temp_table}.PValue "
                "FROM (ProbeSet, ProbeSetXRef, ProbeSetFreeze) "
                "LEFT JOIN {temp_table} ON {temp_table}.Symbol=ProbeSet.Symbol "
                "WHERE ProbeSetFreeze.Name = %(db_name) "
                "AND ProbeSetFreeze.Id=ProbeSetXRef.ProbeSetFreezeId "
                "AND ProbeSet.Id = ProbeSetXRef.ProbeSetId "
                "AND ProbeSet.Symbol IS NOT NULL "
                "AND %s.Correlation IS NOT NULL"),
            db_name=dataset["dataset_name"])
        results = cursor.fetchall()
        cursor.execute("DROP TEMPORARY TABLE %s", temp_table)
        return {
            trait_name: (tiss_corr, tiss_p_val)
            for trait_name, tiss_corr, tiss_p_val in results}

def check_for_literature_info(conn: Any, geneid: int) -> bool:
    """
    Checks the database to find out whether the trait with `geneid` has any
    associated literature.

    This is a migration of the
    `web.webqtl.correlation.CorrelationPage.checkForLitInfo` function in
    GeneNetwork1.
    """
    query = "SELECT 1 FROM LCorrRamin3 WHERE GeneId1=%s LIMIT 1"
    with conn.cursor() as cursor:
        cursor.execute(query, geneid)
        result = cursor.fetchone()
        if result:
            return True

    return False

def check_symbol_for_tissue_correlation(
        conn: Any, tissue_probeset_freeze_id: int, symbol: str = "") -> bool:
    """
    Checks whether a symbol has any associated tissue correlations.

    This is a migration of the
    `web.webqtl.correlation.CorrelationPage.checkSymbolForTissueCorr` function
    in GeneNetwork1.
    """
    query = (
        "SELECT 1 FROM  TissueProbeSetXRef "
        "WHERE TissueProbeSetFreezeId=%(probeset_freeze_id)s "
        "AND Symbol=%(symbol)s LIMIT 1")
    with conn.cursor() as cursor:
        cursor.execute(
            query, probeset_freeze_id=tissue_probeset_freeze_id, symbol=symbol)
        result = cursor.fetchone()
        if result:
            return True

    return False

def fetch_sample_ids(
        conn: Any, sample_names: Tuple[str, ...], species_name: str) -> Tuple[
            int, ...]:
    """
    Given a sequence of sample names, and a species name, return the sample ids
    that correspond to both.

    This is a partial migration of the
    `web.webqtl.correlation.CorrelationPage.fetchAllDatabaseData` function in
    GeneNetwork1.
    """
    query = (
        "SELECT Strain.Id FROM Strain, Species "
        "WHERE Strain.Name IN %(samples_names)s "
        "AND Strain.SpeciesId=Species.Id "
        "AND Species.name=%(species_name)s")
    with conn.cursor() as cursor:
        cursor.execute(
            query,
            {
                "samples_names": tuple(sample_names),
                "species_name": species_name
            })
        return tuple(row[0] for row in cursor.fetchall())

def build_query_sgo_lit_corr(
        db_type: str, temp_table: str, sample_id_columns: str,
        joins: Tuple[str, ...]) -> str:
    """
    Build query for `SGO Literature Correlation` data, when querying the given
    `temp_table` temporary table.

    This is a partial migration of the
    `web.webqtl.correlation.CorrelationPage.fetchAllDatabaseData` function in
    GeneNetwork1.
    """
    return (
        (f"SELECT {db_type}.Name, {temp_table}.value, " +
         sample_id_columns +
         f" FROM ({db_type}, {db_type}XRef, {db_type}Freeze) " +
         f"LEFT JOIN {temp_table} ON {temp_table}.GeneId2=ProbeSet.GeneId " +
         " ".join(joins) +
         " WHERE ProbeSet.GeneId IS NOT NULL " +
         f"AND {temp_table}.value IS NOT NULL " +
         f"AND {db_type}XRef.{db_type}FreezeId = {db_type}Freeze.Id " +
         f"AND {db_type}Freeze.Name = %(db_name)s " +
         f"AND {db_type}.Id = {db_type}XRef.{db_type}Id " +
         f"ORDER BY {db_type}.Id"),
        2)

def build_query_tissue_corr(db_type, temp_table, sample_id_columns, joins):
    """
    Build query for `Tissue Correlation` data, when querying the given
    `temp_table` temporary table.

    This is a partial migration of the
    `web.webqtl.correlation.CorrelationPage.fetchAllDatabaseData` function in
    GeneNetwork1.
    """
    return (
        (f"SELECT {db_type}.Name, {temp_table}.Correlation, " +
         f"{temp_table}.PValue, " +
         sample_id_columns +
         f" FROM ({db_type}, {db_type}XRef, {db_type}Freeze) " +
         f"LEFT JOIN {temp_table} ON {temp_table}.Symbol=ProbeSet.Symbol " +
         " ".join(joins) +
         " WHERE ProbeSet.Symbol IS NOT NULL " +
         f"AND {temp_table}.Correlation IS NOT NULL " +
         f"AND {db_type}XRef.{db_type}FreezeId = {db_type}Freeze.Id " +
         f"AND {db_type}Freeze.Name = %(db_name)s " +
         f"AND {db_type}.Id = {db_type}XRef.{db_type}Id "
         f"ORDER BY {db_type}.Id"),
        3)

def fetch_all_database_data(# pylint: disable=[R0913, R0914]
        conn: Any, species: str, gene_id: int, trait_symbol: str,
        samples: Tuple[str, ...], dataset: dict, method: str,
        return_number: int, probeset_freeze_id: int) -> Tuple[
            Tuple[float], int]:
    """
    This is a migration of the
    `web.webqtl.correlation.CorrelationPage.fetchAllDatabaseData` function in
    GeneNetwork1.
    """
    def __build_query__(sample_ids, temp_table):
        sample_id_columns = ", ".join(f"T{smpl}.value" for smpl in sample_ids)
        if db_type == "Publish":
            joins = tuple(
                ("LEFT JOIN PublishData AS T{item} "
                 "ON T{item}.Id = PublishXRef.DataId "
                 "AND T{item}.StrainId = %(T{item}_sample_id)s")
                for item in sample_ids)
            return (
                ("SELECT PublishXRef.Id, " +
                 sample_id_columns +
                 "FROM (PublishXRef, PublishFreeze) " +
                 " ".join(joins) +
                 " WHERE PublishXRef.InbredSetId = PublishFreeze.InbredSetId "
                 "AND PublishFreeze.Name = %(db_name)s"),
                1)
        if temp_table is not None:
            joins = tuple(
                (f"LEFT JOIN {db_type}Data AS T{item} "
                 f"ON T{item}.Id = {db_type}XRef.DataId "
                 f"AND T{item}.StrainId=%(T{item}_sample_id)s")
                for item in sample_ids)
            if method.lower() == "sgo literature correlation":
                return build_query_sgo_lit_corr(
                    sample_ids, temp_table, sample_id_columns, joins)
            if method.lower() in (
                    "tissue correlation, pearson's r",
                    "tissue correlation, spearman's rho"):
                return build_query_tissue_corr(
                    sample_ids, temp_table, sample_id_columns, joins)
        joins = tuple(
            (f"LEFT JOIN {db_type}Data AS T{item} "
             f"ON T{item}.Id = {db_type}XRef.DataId "
             f"AND T{item}.StrainId = %(T{item}_sample_id)s")
            for item in sample_ids)
        return (
            (
                f"SELECT {db_type}.Name, " +
                sample_id_columns +
                f" FROM ({db_type}, {db_type}XRef, {db_type}Freeze) " +
                " ".join(joins) +
                f" WHERE {db_type}XRef.{db_type}FreezeId = {db_type}Freeze.Id " +
                f"AND {db_type}Freeze.Name = %(db_name)s " +
                f"AND {db_type}.Id = {db_type}XRef.{db_type}Id " +
                f"ORDER BY {db_type}.Id"),
            1)

    def __fetch_data__(sample_ids, temp_table):
        query, data_start_pos = __build_query__(sample_ids, temp_table)
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                {"db_name": db_name,
                 **{f"T{item}_sample_id": item for item in sample_ids}})
            return (cursor.fetchall(), data_start_pos)

    sample_ids = tuple(
        # look into graduating this to an argument and removing the `samples`
        # and `species` argument: function currying and compositions might help
        # with this
        f"{sample_id}" for sample_id in
        fetch_sample_ids(conn, samples, species))

    temp_table = None
    if gene_id and db_type == "probeset":
        if method.lower() == "sgo literature correlation":
            temp_table = build_temporary_literature_table(
                conn, species, gene_id, return_number)
        if method.lower() in (
                "tissue correlation, pearson's r",
                "tissue correlation, spearman's rho"):
            temp_table = build_temporary_tissue_correlations_table(
                conn, trait_symbol, probeset_freeze_id, method, return_number)

    trait_database = tuple(
        item for sublist in
        (__fetch_data__(ssample_ids, temp_table)
         for ssample_ids in partition_all(25, sample_ids))
        for item in sublist)

    if temp_table:
        with conn.cursor() as cursor:
            cursor.execute(f"DROP TEMPORARY TABLE {temp_table}")

    return (tuple(item[0] for item in trait_database), trait_database[0][1])
