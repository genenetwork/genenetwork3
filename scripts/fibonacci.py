"""
This module provides a function to calculate the nth Fibonacci number using an iterative approach.
"""

def fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number.

    The Fibonacci sequence is a series of numbers where each number is the sum of the two preceding ones.
    Typically starting with 0 and 1.

    Args:
        n (int): The position in the Fibonacci sequence to calculate. Must be a non-negative integer.

    Returns:
        int: The nth Fibonacci number.

    Raises:
        ValueError: If n is not a non-negative integer.
    """
    if not isinstance(n, int):
        raise ValueError("Input must be an integer.")
    if n < 0:
        raise ValueError("Input must be a non-negative integer.")
    if n == 0:
        return 0
    elif n == 1:
        return 1

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

if __name__ == "__main__":
    # Example usage:
    try:
        position = 10
        result = fibonacci(position)
        print(f"The {position}th Fibonacci number is: {result}")
    except ValueError as e:
        print(f"Error: {e}")
