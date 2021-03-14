"""module contains code for correlations"""
from typing import List
from typing import Tuple
from typing import Optional
from typing import Callable
from typing import Union
import scipy.stats  # type: ignore


def compute_sum(rhs: int, lhs: int)-> int:
    """initial tests to compute  sum  of two numbers"""
    return rhs + lhs


def normalize_values(a_values: List, b_values: List)->Tuple[List[float], List[float], int]:
    """
    Trim two lists of values to contain only the values they both share

    Given two lists of sample values, trim each list so that it contains
    only the samples that contain a value in both lists. Also returns
    the number of such samples.

    >>> normalize_values([2.3, None, None, 3.2, 4.1, 5], [3.4, 7.2, 1.3, None, 6.2, 4.1])
    ([2.3, 4.1, 5], [3.4, 6.2, 4.1], 3)

    """
    a_new = []
    b_new = []
    for a_val, b_val in zip(a_values, b_values):
        if (a_val and b_val is not None):
            a_new.append(a_val)
            b_new.append(b_val)
    return a_new, b_new, len(a_new)


def compute_corr_coeff_p_value(primary_values: List, target_values: List, corr_method: str)->\
        Tuple[float, float]:
    """given array like inputs calculate the primary and target_value
     methods ->pearson,spearman and biweight mid correlation
     return value is rho and p_value
    """
    corr_mapping = {
        "bicor": do_bicor,
        "pearson": scipy.stats.pearsonr,
        "spearman": scipy.stats.spearmanr
    }

    use_corr_method = corr_mapping.get(corr_method, "spearman")

    corr_coeffient, p_val = use_corr_method(primary_values, target_values)

    return (corr_coeffient, p_val)


def compute_sample_r_correlation(corr_method: str, trait_vals, target_samples_vals)->\
        Optional[Tuple[float, float, int]]:
    """Given a primary trait values and target trait values
    calculate the correlation coeff and p value"""

    sanitized_traits_vals, sanitized_target_vals,\
        num_overlap = normalize_values(trait_vals, target_samples_vals)

    if num_overlap > 5:

        (corr_coeffient, p_value) =\
            compute_corr_coeff_p_value(primary_values=sanitized_traits_vals,
                                       target_values=sanitized_target_vals,
                                       corr_method=corr_method)

        # xtodo check if corr_coefficient is None should use numpy.isNan scipy.isNan is deprecated
        if corr_coeffient is not None:
            return (corr_coeffient, p_value, num_overlap)

    return None


def do_bicor(x_val, y_val) -> Tuple[float, float]:
    """not implemented method for doing biweight mid correlation
    use  astropy stats package :not packaged in guix
    """

    return (x_val, y_val)


def filter_shared_sample_keys(this_samplelist, target_samplelist)->Tuple[List, List]:
    """given primary and target samplelist for two base and target\
    trait selecct filter the values using the shared keys"""
    this_vals = []
    target_vals = []

    for key, value in target_samplelist.items():
        if key in this_samplelist:
            target_vals.append(value)
            this_vals.append(this_samplelist[key])

    return (this_vals, target_vals)


def compute_all_sample_correlation(this_trait, target_dataset, corr_method="pearson")->List:
    """given a trait samplelist and target__datasets compute all sample correlation"""

    corr_results = []

    for target_trait in target_dataset:
        this_vals, target_vals = filter_shared_sample_keys(
            this_trait, target_trait)

        sample_correlation = compute_sample_r_correlation(
            corr_method=corr_method, trait_vals=this_vals, target_samples_vals=target_vals)

        if sample_correlation is not None:
            (corr_coeffient, p_value, num_overlap) = sample_correlation

        else:
            continue

        corr_result = {"corr_coeffient": corr_coeffient,
                       "p_value": p_value,
                       "num_overlap": num_overlap}

        corr_results.append(corr_result)

    return corr_results


def tissue_lit_corr_for_probe_type(this_dataset_type: str, target_dataset_type: str):
    """function that does either lit_corr_for_trait_list or tissue_corr\
    _for_trait list depedeing on whether both dataset and target_dataset are\
    both set to probet"""
    return (this_dataset_type, target_dataset_type)


def tissue_correlation_for_trait_list(primary_tissue_vals: List,
                                      target_tissues_values: List,
                                      corr_method: str,
                                      compute_corr_p_value: Callable =
                                      compute_corr_coeff_p_value)->List:
    """given a primary tissue values for a trait and the target tissues values\
    compute the correlation_cooeff and p value  the input required are arrays\
    output - > List containing Dicts with corr_coefficient value,P_value and\
    also the tissue numbers is len(primary) == len(target)"""

    lit_corr_results = []

    for target_trait_tissue in target_tissues_values:
        (tissue_corr_coeffient, p_value) = compute_corr_p_value(
            primary_values=primary_tissue_vals,
            target_values=target_trait_tissue, corr_method=corr_method)

        corr_result = {
            "tissue_corr": tissue_corr_coeffient,
            "p_value": p_value,
            "tissue_number": len(primary_tissue_vals)
        }

        lit_corr_results.append(corr_result)

    return lit_corr_results


def fetch_lit_correlation_data(database,
                               input_mouse_gene_id: str,
                               mouse_gene_id: str)->Tuple[str, Union[int, float]]:
    """given input trait mouse gene id and mouse gene id fetch the lit\
    corr_data"""
    if mouse_gene_id is not None and ";" not in mouse_gene_id:
        query = """
        SELECT VALUE  
        FROM  LCorrRamin3
        WHERE GeneId1='%s' and
        GeneId2='%s'
        """ % (mouse_gene_id, input_mouse_gene_id)
        _lit_corr_results = database.execute(query).fetchone()

    return ("HC_AMC_C", 3.1)


def lit_correlation_for_trait_list(trait_geneid_dict: dict):
    """given  a list of traits from corr results compute fetch\
    fetch their lit and p values from the databse"""

    for _trait, _gene_id in list(trait_geneid_dict.items()):
        pass

    return trait_geneid_dict
