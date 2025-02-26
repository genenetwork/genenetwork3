"""
Unit tests for the `fibonacci` function in the `gn3.api.rqtl2` module.

This module contains a series of test cases to verify the correctness and robustness
of the Fibonacci number calculation function. It checks for valid inputs, boundary
conditions, and error handling to ensure the function behaves as expected under
various scenarios.
"""

import pytest
from gn3.api.rqtl2 import fibonacci


def test_fibonacci_zero():
    """
    Test that the fibonacci function returns 0 when the input is 0.
    """
    assert fibonacci(0) == 0


def test_fibonacci_one():
    """
    Test that the fibonacci function returns 1 when the input is 1.
    """
    assert fibonacci(1) == 1


def test_fibonacci_ten():
    """
    Test that the fibonacci function returns 55 when the input is 10.
    """
    assert fibonacci(10) == 55


def test_fibonacci_negative():
    """
    Test that the fibonacci function raises a ValueError when the input is negative.
    """
    with pytest.raises(ValueError) as excinfo:
        fibonacci(-1)
    assert "non-negative integer" in str(excinfo.value)


def test_fibonacci_non_integer():
    """
    Test that the fibonacci function raises a ValueError when the input is not an integer.
    """
    with pytest.raises(ValueError) as excinfo:
        fibonacci(5.5)
    assert "non-negative integer" in str(excinfo.value)


def test_fibonacci_large():
    """
    Test that the fibonacci function returns the correct value for a larger input (20).
    """
    assert fibonacci(20) == 6765


@pytest.mark.parametrize("n, expected", [
    (2, 1),
    (3, 2),
    (4, 3),
    (5, 5),
    (6, 8),
    (7, 13),
])
def test_fibonacci_multiple(n, expected):
    """
    Test multiple cases of the fibonacci function using parameterization.

    Args:
        n (int): The position in the Fibonacci sequence.
        expected (int): The expected Fibonacci number at position `n`.
    """
    assert fibonacci(n) == expected
