from hypothesis import given, strategies as st
from pymonad.maybe import Just, Nothing
import pytest

from gn3.api.search import apply_si_suffix, parse_range

@pytest.mark.unit_test
@given(st.decimals(places=3, allow_nan=False, allow_infinity=False),
       st.sampled_from(["k", "K"]))
def test_apply_si_suffix_kilo(mantissa, suffix):
    assert apply_si_suffix(f"{mantissa}{suffix}") == int(mantissa * 10**3)

@pytest.mark.unit_test
@given(st.decimals(places=6, allow_nan=False, allow_infinity=False),
       st.sampled_from(["m", "M"]))
def test_apply_si_suffix_mega(mantissa, suffix):
    assert apply_si_suffix(f"{mantissa}{suffix}") == int(mantissa * 10**6)

@pytest.mark.unit_test
@given(st.decimals(places=9, allow_nan=False, allow_infinity=False),
       st.sampled_from(["g", "G"]))
def test_apply_si_suffix_giga(mantissa, suffix):
    assert apply_si_suffix(f"{mantissa}{suffix}") == int(mantissa * 10**9)

@pytest.mark.unit_test
def test_parse_range_closed_interval():
    assert parse_range("foo..bar") == (Just("foo"), Just("bar"))

@pytest.mark.unit_test
def test_parse_range_left_open_interval():
    assert parse_range("..bar") == (Nothing, Just("bar"))

@pytest.mark.unit_test
def test_parse_range_right_open_interval():
    assert parse_range("foo..") == (Just("foo"), Nothing)
