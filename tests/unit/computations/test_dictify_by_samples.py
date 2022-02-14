from math import isnan
import pytest
from collections.abc import Sequence
from hypothesis import given, strategies as st
from gn3.computations.partial_correlations import dictify_by_samples


def check_keys(samples, the_dict):
    """Check that all the keys in `the_dict` are strings in `samples.`"""
    return all(
        (key in samples) for key in the_dict.keys())


def same(val1, val2):
    """
    Check that values are similar.

    In Python3 `float('nan') == float('nan')` always returns False. This
    function thus, compares similarity rather than direct equality for NaN
    values.

    `Math.isnan(None)` would throw an error, thus this function takes advantage
    of the `or` operation's short-circuit to avoid this failure in the case
    where both values are NoneType values.
    """
    return (
        (val1 is None and val2 is None) or
        (isnan(val1) and isnan(val2)) or
        (val1 == val2))

def check_dict_keys_and_values(sample, value, variance, the_dict):
    """
    Check the following properties for each dict:
    - has only `sample_name`, `value` and `variance` as the keys
    - The values in the dict are the same ones in `sample`, `value` and
      `variance`.
    """
    return (
        all((key in ("sample_name", "value", "variance"))
            for key in the_dict.keys()) and
        the_dict["sample_name"] == sample and
        same(the_dict["value"], value) and
        same(the_dict["variance"], variance))

def check_values(samples, values, variances, row):
    """
    Check that the values in each dict in `row` are made up from the values in
    the `samples`, `values`, and `variances` sequences, skipping all values in
    the `row` for which the sample name is an empty string.
    """
    return all(
        check_dict_keys_and_values(smp, val, var, row[smp])
        for smp, val, var in zip(samples, values, variances)
        if smp != "")

non_empty_samples = st.lists(
    st.text(min_size=1, max_size=15).map(
        lambda s: s.strip()))
empty_samples = st.text(
    alphabet=" \t\n\r\f\v", min_size=1, max_size=15).filter(
        lambda s: len(s.strip()) == 0)
values = st.lists(st.floats())
variances = st.lists(st.one_of(st.none(), st.floats()))
other = st.lists(st.integers())

@pytest.mark.unit_test
@given(svv=st.tuples(
    st.lists(non_empty_samples),
    st.lists(values),
    st.lists(variances),
    st.lists(other)))
def test_dictifify_by_samples_with_nonempty_samples_strings(svv):
    """
    Test for `dictify_by_samples`.

    Given a sequence of sequences of sequences

    Check for the following properties:
    - Returns a sequence of dicts
    - Each dicts keys correspond to its index in the zeroth sequence in the
      top-level sequence
    """
    res = dictify_by_samples(svv)
    assert (
        isinstance(res, Sequence)
        and all((isinstance(elt, dict) for elt in res))
        and all(
            check_keys(svv[0][idx], row)
            for idx, row in enumerate(res))
        and all(
            check_values(svv[0][idx], svv[1][idx], svv[2][idx], row)
            for idx, row in enumerate(res)))

@pytest.mark.unit_test
@given(svv=st.tuples(
    st.lists(
        st.lists(empty_samples,min_size=1),
        min_size=1),
    st.lists(st.lists(st.floats(), min_size=1), min_size=1),
    st.lists(
        st.lists(st.one_of(st.none(), st.floats()), min_size=1), min_size=1),
    st.lists(st.lists(st.integers(), min_size=1), min_size=1)))
def test_dictify_by_samples_with_empty_samples_strings(svv):
    """
    Test that `dictify_by_samples` warns the user about providing sample names
    that are just empty strings.
    """
    with pytest.warns(RuntimeWarning):
        dictify_by_samples(svv)
