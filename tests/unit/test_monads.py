"""Test cases for functions defined in monads.py"""
import pytest

from pymonad.maybe import Just, Nothing
from gn3.monads import MonadicDict


@pytest.mark.unit_test
@pytest.mark.parametrize(
    ("key", "value", "expected"),
    (
        ("foo", Just(1), Just(1)),
        ("bar", Nothing, Nothing),
    ),
)
def test_monadic_dict(key, value, expected):
    """Test basic Monadic Dict operations"""
    _test_dict = MonadicDict()
    _test_dict[key] = value
    _test_dict |= {"test_update": "random"}
    assert _test_dict[key] == expected
    assert _test_dict["test_update"] == Just("random")
    assert _test_dict["non-existent"] == Nothing
