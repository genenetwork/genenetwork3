import pytest
from gn3.api.rqtl2 import fibonacci

def test_fibonacci_zero():
    assert fibonacci(0) == 0

def test_fibonacci_one():
    assert fibonacci(1) == 1

def test_fibonacci_ten():
    assert fibonacci(10) == 55

def test_fibonacci_negative():
    with pytest.raises(ValueError) as excinfo:
        fibonacci(-1)
    assert "non-negative integer" in str(excinfo.value)

def test_fibonacci_non_integer():
    with pytest.raises(ValueError) as excinfo:
        fibonacci(5.5)
    assert "non-negative integer" in str(excinfo.value)

def test_fibonacci_large():
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
    assert fibonacci(n) == expected
