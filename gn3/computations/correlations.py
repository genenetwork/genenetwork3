

def compute_sum(a: int, b: int):
    return a+b


def normalize_values(a_values, b_values):
    """
    Trim two lists of values to contain only the values they both share

    Given two lists of sample values, trim each list so that it contains
    only the samples that contain a value in both lists. Also returns
    the number of such samples.

    >>> normalize_values([2.3, None, None, 3.2, 4.1, 5], [3.4, 7.2, 1.3, None, 6.2, 4.1])
    ([2.3, 4.1, 5], [3.4, 6.2, 4.1], 3)

    """

    min_length = min(len(a_values), len(b_values))
    a_new = []
    b_new = []
    for a, b in zip(a_values, b_values):
        if not (a == None or b == None):
            a_new.append(a)
            b_new.append(b)
    return a_new, b_new, len(a_new)


def get_sample_r_and_p_values(source_primary_vals, source_target_vals):

    trait_vals, target_vals, num_overlap = normalize_values(
        source_primary_vals, source_target_vals)

    _corr_mapping = {
     "bicor":do_bicor,
     "pearson":scipy.stats.pearsonr,
     "spearman":scipy.stats.spearman
    }

    if num_overlap > 5:

        use_method = corr_mapping[corr_method] 

        sample_r ,sample_p = use_method(x=trait_vals,y=target_vals)


