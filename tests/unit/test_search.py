"""Test that the search feature works as expected"""
from hypothesis import given, strategies as st
from pymonad.maybe import Just, Nothing
import pytest

from gn3.api.search import apply_si_suffix, parse_range, parse_position

@pytest.mark.unit_test
@given(st.decimals(places=3, allow_nan=False, allow_infinity=False),
       st.sampled_from(["k", "K"]))
def test_apply_si_suffix_kilo(mantissa, suffix):
    """
    GIVEN: A string of a decimal value with up to 9 decimal places and a suffix 'K'
      e.g. 45.240K - where '45.240' is the decimal values
    WHEN: We apply the suffix
    THEN: We get the integer value that is closest to the decimal value
      multiplied by 1000
    """
    assert apply_si_suffix(f"{mantissa}{suffix}") == int(mantissa * 10**3)

@pytest.mark.unit_test
@given(st.decimals(places=6, allow_nan=False, allow_infinity=False),
       st.sampled_from(["m", "M"]))
def test_apply_si_suffix_mega(mantissa, suffix):
    """
    GIVEN: A string of a decimal value with up to 9 decimal places and a suffix 'M'
      e.g. 45.240M - where '45.240' is the decimal values
    WHEN: We apply the suffix
    THEN: We get the integer value that is closest to the decimal value
      multiplied by 1000000
    """
    assert apply_si_suffix(f"{mantissa}{suffix}") == int(mantissa * 10**6)

@pytest.mark.unit_test
@given(st.decimals(places=9, allow_nan=False, allow_infinity=False),
       st.sampled_from(["g", "G"]))
def test_apply_si_suffix_giga(mantissa, suffix):
    """
    GIVEN: A string of a decimal value with up to 9 decimal places and a suffix 'G'
      e.g. 45.240G - where '45.240' is the decimal values
    WHEN: We apply the suffix
    THEN: We get the integer value that is closest to the decimal value
      multiplied by 1000000000
    """
    assert apply_si_suffix(f"{mantissa}{suffix}") == int(mantissa * 10**9)

@pytest.mark.unit_test
def test_parse_range_closed_interval():
    """
    GIVEN: An closed range as a string, with both the beginning and the ending
      e.g. "foo..bar"
    WHEN: we parse the range
    THEN: we get both values for the beginning (Just("foo")) and the ending
      (Just("bar")).
    """
    assert parse_range("foo..bar") == (Just("foo"), Just("bar"))

@pytest.mark.unit_test
def test_parse_range_left_open_interval():
    """
    GIVEN: An open range as a string, with only the ending e.g. "foo.."
    WHEN: we parse the range
    THEN: we get no value (Nothing) for the beginning and an actual value
      (Just("bar")) for the ending
    """
    assert parse_range("..bar") == (Nothing, Just("bar"))

@pytest.mark.unit_test
def test_parse_range_right_open_interval():
    """
    GIVEN: An open range as a string, with only the beginning e.g. "foo.."
    WHEN: we parse the range
    THEN: we get an actual value for the beginning of the range (Just("foo"))
      and no value (Nothing) for the ending of the range
    """
    assert parse_range("foo..") == (Just("foo"), Nothing)

@pytest.mark.unit_test
def test_parse_position_close_to_zero_location():
    """
    GIVEN: A point location close to zero
    WHEN: we parse the range
    THEN: set the lower limit to zero, not a negative number
    """
    assert parse_position("25K")[0] == Just(0)
