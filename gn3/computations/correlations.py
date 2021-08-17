"""module contains code for correlations"""
import math
import multiprocessing

from typing import List
from typing import Tuple
from typing import Optional
from typing import Callable

import scipy.stats
from gn3.computations.biweight import calculate_biweight_corr


def map_shared_keys_to_values(target_sample_keys: List,
                              target_sample_vals: dict) -> List:
    """Function to construct target dataset data items given common shared keys
    and trait sample-list values for example given keys

    >>>>>>>>>> ["BXD1", "BXD2", "BXD5", "BXD6", "BXD8", "BXD9"] and value
    object as "HCMA:_AT": [4.1, 5.6, 3.2, 1.1, 4.4, 2.2],TXD_AT": [6.2, 5.7,
    3.6, 1.5, 4.2, 2.3]} return results should be a list of dicts mapping the
    shared keys to the trait values

    """
    target_dataset_data = []

    for trait_id, sample_values in target_sample_vals.items():
        target_trait_dict = dict(zip(target_sample_keys, sample_values))

        target_trait = {
            "trait_id": trait_id,
            "trait_sample_data": target_trait_dict
        }

        target_dataset_data.append(target_trait)

    return target_dataset_data


def normalize_values(a_values: List,
                     b_values: List) -> Tuple[List[float], List[float], int]:
    """Trim two lists of values to contain only the values they both share Given
    two lists of sample values, trim each list so that it contains only the
    samples that contain a value in both lists. Also returns the number of
    such samples.

    >>> normalize_values([2.3, None, None, 3.2, 4.1, 5],
                         [3.4, 7.2, 1.3, None, 6.2, 4.1])
    ([2.3, 4.1, 5], [3.4, 6.2, 4.1], 3)

    """
    a_new = []
    b_new = []
    for a_val, b_val in zip(a_values, b_values):
        if (a_val and b_val is not None):
            a_new.append(a_val)
            b_new.append(b_val)
    return a_new, b_new, len(a_new)


def compute_corr_coeff_p_value(primary_values: List, target_values: List,
                               corr_method: str) -> Tuple[float, float]:
    """Given array like inputs calculate the primary and target_value methods ->
pearson,spearman and biweight mid correlation return value is rho and p_value

    """
    corr_mapping = {
        "bicor": do_bicor,
        "pearson": scipy.stats.pearsonr,
        "spearman": scipy.stats.spearmanr
    }
    use_corr_method = corr_mapping.get(corr_method, "spearman")
    corr_coefficient, p_val = use_corr_method(primary_values, target_values)
    return (corr_coefficient, p_val)


def compute_sample_r_correlation(trait_name, corr_method, trait_vals,
                                 target_samples_vals) -> Optional[
                                     Tuple[str, float, float, int]]:
    """Given a primary trait values and target trait values calculate the
    correlation coeff and p value

    """
    (sanitized_traits_vals, sanitized_target_vals,
     num_overlap) = normalize_values(trait_vals, target_samples_vals)

    if num_overlap > 5:

        (corr_coefficient, p_value) =\
            compute_corr_coeff_p_value(primary_values=sanitized_traits_vals,
                                       target_values=sanitized_target_vals,
                                       corr_method=corr_method)

        if corr_coefficient is not None and not math.isnan(corr_coefficient):
            return (trait_name, corr_coefficient, p_value, num_overlap)
    return None


def do_bicor(x_val, y_val) -> Tuple[float, float]:
    """Not implemented method for doing biweight mid correlation use astropy stats
package :not packaged in guix

    """

    try:
        results = calculate_biweight_corr(x_val, y_val)
        return results
    except Exception as error:
        raise error


def filter_shared_sample_keys(this_samplelist,
                              target_samplelist) -> Tuple[List, List]:
    """Given primary and target sample-list for two base and target trait select
    filter the values using the shared keys

    """
    this_vals = []
    target_vals = []
    for key, value in target_samplelist.items():
        if key in this_samplelist:
            target_vals.append(value)
            this_vals.append(this_samplelist[key])
    return (this_vals, target_vals)


def speed_compute_all_sample_correlation(this_trait,
                                         target_dataset,
                                         corr_method="pearson") -> List:
    """Given a trait data sample-list and target__datasets compute all sample
    correlation
    this functions uses multiprocessing if not use the normal fun

    """
    # xtodo fix trait_name currently returning single one
    # pylint: disable-msg=too-many-locals
    this_trait_samples = this_trait["trait_sample_data"]
    corr_results = []
    processed_values = []
    for target_trait in target_dataset:
        trait_name = target_trait.get("trait_id")
        target_trait_data = target_trait["trait_sample_data"]
        processed_values.append((trait_name, corr_method, *filter_shared_sample_keys(
            this_trait_samples, target_trait_data)))
    with multiprocessing.Pool(4) as pool:
        results = pool.starmap(compute_sample_r_correlation, processed_values)

        for sample_correlation in results:
            if sample_correlation is not None:
                (trait_name, corr_coefficient, p_value,
                 num_overlap) = sample_correlation
                corr_result = {
                    "corr_coefficient": corr_coefficient,
                    "p_value": p_value,
                    "num_overlap": num_overlap
                }

                corr_results.append({trait_name: corr_result})
    return sorted(
        corr_results,
        key=lambda trait_name: -abs(list(trait_name.values())[0]["corr_coefficient"]))


def compute_all_sample_correlation(this_trait,
                                   target_dataset,
                                   corr_method="pearson") -> List:
    """Temp function to benchmark with compute_all_sample_r alternative to
    compute_all_sample_r where we use multiprocessing

    """
    this_trait_samples = this_trait["trait_sample_data"]
    corr_results = []
    for target_trait in target_dataset:
        trait_name = target_trait.get("trait_id")
        target_trait_data = target_trait["trait_sample_data"]
        this_vals, target_vals = filter_shared_sample_keys(
            this_trait_samples, target_trait_data)

        sample_correlation = compute_sample_r_correlation(
            trait_name=trait_name,
            corr_method=corr_method,
            trait_vals=this_vals,
            target_samples_vals=target_vals)
        if sample_correlation is not None:
            (trait_name, corr_coefficient,
             p_value, num_overlap) = sample_correlation
        else:
            continue
        corr_result = {
            "corr_coefficient": corr_coefficient,
            "p_value": p_value,
            "num_overlap": num_overlap
        }
        corr_results.append({trait_name: corr_result})
    return sorted(
        corr_results,
        key=lambda trait_name: -abs(list(trait_name.values())[0]["corr_coefficient"]))


def tissue_correlation_for_trait(
        primary_tissue_vals: List,
        target_tissues_values: List,
        corr_method: str,
        trait_id: str,
        compute_corr_p_value: Callable = compute_corr_coeff_p_value) -> dict:
    """Given a primary tissue values for a trait and the target tissues values
    compute the correlation_cooeff and p value the input required are arrays
    output -> List containing Dicts with corr_coefficient value, P_value and
    also the tissue numbers is len(primary) == len(target)

    """

    # ax :todo assertion that length one one target tissue ==primary_tissue

    (tissue_corr_coefficient,
     p_value) = compute_corr_p_value(primary_values=primary_tissue_vals,
                                     target_values=target_tissues_values,
                                     corr_method=corr_method)

    tiss_corr_result = {trait_id: {
        "tissue_corr": tissue_corr_coefficient,
        "tissue_number": len(primary_tissue_vals),
        "tissue_p_val": p_value}}

    return tiss_corr_result


def fetch_lit_correlation_data(
        conn,
        input_mouse_gene_id: Optional[str],
        gene_id: str,
        mouse_gene_id: Optional[str] = None) -> Tuple[str, float]:
    """Given input trait mouse gene id and mouse gene id fetch the lit
    corr_data

    """
    if mouse_gene_id is not None and ";" not in mouse_gene_id:
        query = """
        SELECT VALUE
        FROM  LCorrRamin3
        WHERE GeneId1='%s' and
        GeneId2='%s'
        """

        query_values = (str(mouse_gene_id), str(input_mouse_gene_id))

        cursor = conn.cursor()

        cursor.execute(query_formatter(query,
                                       *query_values))
        results = cursor.fetchone()
        lit_corr_results = None
        if results is not None:
            lit_corr_results = results
        else:
            cursor = conn.cursor()
            cursor.execute(query_formatter(query,
                                           *tuple(reversed(query_values))))
            lit_corr_results = cursor.fetchone()
        lit_results = (gene_id, lit_corr_results[0])\
            if lit_corr_results else (gene_id, 0)
        return lit_results
    return (gene_id, 0)


def lit_correlation_for_trait(
        conn,
        target_trait_lists: List,
        species: Optional[str] = None,
        trait_gene_id: Optional[str] = None) -> List:
    """given species,base trait gene id fetch the lit corr results from the db\
    output is float for lit corr results """
    fetched_lit_corr_results = []
    this_trait_mouse_gene_id = map_to_mouse_gene_id(conn=conn,
                                                    species=species,
                                                    gene_id=trait_gene_id)
    for (trait_name, target_trait_gene_id) in target_trait_lists:
        corr_results = {}
        if target_trait_gene_id:
            target_mouse_gene_id = map_to_mouse_gene_id(
                conn=conn,
                species=species,
                gene_id=target_trait_gene_id)
            fetched_corr_data = fetch_lit_correlation_data(
                conn=conn,
                input_mouse_gene_id=this_trait_mouse_gene_id,
                gene_id=target_trait_gene_id,
                mouse_gene_id=target_mouse_gene_id)
            dict_results = dict(zip(("gene_id", "lit_corr"),
                                    fetched_corr_data))
            corr_results[trait_name] = dict_results
            fetched_lit_corr_results.append(corr_results)
    return fetched_lit_corr_results


def query_formatter(query_string: str, *query_values):
    """Formatter query string given the unformatted query string and the
    respectibe values.Assumes number of placeholders is equal to the number of
    query values

    """
    # xtodo escape sql queries
    return query_string % (query_values)


def map_to_mouse_gene_id(conn, species: Optional[str],
                         gene_id: Optional[str]) -> Optional[str]:
    """Given a species which is not mouse map the gene_id\
    to respective mouse gene id"""
    if None in (species, gene_id):
        return None
    if species == "mouse":
        return gene_id
    cursor = conn.cursor()
    query = """SELECT mouse
                FROM GeneIDXRef
                WHERE '%s' = '%s'"""
    query_values = (species, gene_id)
    cursor.execute(query_formatter(query,
                                   *query_values))
    results = cursor.fetchone()
    mouse_gene_id = results.mouse if results is not None else None
    return mouse_gene_id


def compute_all_lit_correlation(conn, trait_lists: List,
                                species: str, gene_id):
    """Function that acts as an abstraction for
    lit_correlation_for_trait"""

    lit_results = lit_correlation_for_trait(
        conn=conn,
        target_trait_lists=trait_lists,
        species=species,
        trait_gene_id=gene_id)
    sorted_lit_results = sorted(
        lit_results,
        key=lambda trait_name: -abs(list(trait_name.values())[0]["lit_corr"]))

    return sorted_lit_results


def compute_tissue_correlation(primary_tissue_dict: dict,
                               target_tissues_data: dict,
                               corr_method: str):
    """Function acts as an abstraction for tissue_correlation_for_trait\
    required input are target tissue object and primary tissue trait\
    target tissues data contains the trait_symbol_dict and symbol_tissue_vals
    """
    tissues_results = []
    primary_tissue_vals = primary_tissue_dict["tissue_values"]
    traits_symbol_dict = target_tissues_data["trait_symbol_dict"]
    symbol_tissue_vals_dict = target_tissues_data["symbol_tissue_vals_dict"]
    target_tissues_list = process_trait_symbol_dict(
        traits_symbol_dict, symbol_tissue_vals_dict)
    for target_tissue_obj in target_tissues_list:
        trait_id = target_tissue_obj.get("trait_id")
        target_tissue_vals = target_tissue_obj.get("tissue_values")

        tissue_result = tissue_correlation_for_trait(
            primary_tissue_vals=primary_tissue_vals,
            target_tissues_values=target_tissue_vals,
            trait_id=trait_id,
            corr_method=corr_method)
        tissue_result_dict = {trait_id: tissue_result}
        tissues_results.append(tissue_result_dict)
    return sorted(
        tissues_results,
        key=lambda trait_name: -abs(list(trait_name.values())[0]["tissue_corr"]))


def process_trait_symbol_dict(trait_symbol_dict, symbol_tissue_vals_dict) -> List:
    """Method for processing trait symbol dict given the symbol tissue values

    """
    traits_tissue_vals = []
    for (trait, symbol) in trait_symbol_dict.items():
        if symbol is not None:
            target_symbol = symbol.lower()
            if target_symbol in symbol_tissue_vals_dict:
                trait_tissue_val = symbol_tissue_vals_dict[target_symbol]
                target_tissue_dict = {"trait_id": trait,
                                      "symbol": target_symbol,
                                      "tissue_values": trait_tissue_val}
                traits_tissue_vals.append(target_tissue_dict)
    return traits_tissue_vals


def speed_compute_tissue_correlation(primary_tissue_dict: dict,
                                     target_tissues_data: dict,
                                     corr_method: str):
    """Experimental function that uses multiprocessing for computing tissue
    correlation

    """
    tissues_results = []
    primary_tissue_vals = primary_tissue_dict["tissue_values"]
    traits_symbol_dict = target_tissues_data["trait_symbol_dict"]
    symbol_tissue_vals_dict = target_tissues_data["symbol_tissue_vals_dict"]
    target_tissues_list = process_trait_symbol_dict(
        traits_symbol_dict, symbol_tissue_vals_dict)
    processed_values = []

    for target_tissue_obj in target_tissues_list:
        trait_id = target_tissue_obj.get("trait_id")

        target_tissue_vals = target_tissue_obj.get("tissue_values")
        processed_values.append(
            (primary_tissue_vals, target_tissue_vals, corr_method, trait_id))

    with multiprocessing.Pool(4) as pool:
        results = pool.starmap(
            tissue_correlation_for_trait, processed_values)
        for result in results:
            tissues_results.append(result)

    return sorted(
        tissues_results,
        key=lambda trait_name: -abs(list(trait_name.values())[0]["tissue_corr"]))
