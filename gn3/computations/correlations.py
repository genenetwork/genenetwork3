"""module contains code for correlations"""
from typing import List
from typing import Tuple
from typing import Optional

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


def compute_corr_coeff_p_value(primary_values: List, target_values: List, corr_method: str):
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
    use  astropy package :not packaged in guix
    """

    return (x_val, y_val)
