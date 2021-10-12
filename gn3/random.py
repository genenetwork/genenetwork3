"""
Functions to generate complex random data.
"""
import random
import string

def random_string(length):
    """Generate a random string of length `length`."""
    return "".join(
        random.choices(
            string.ascii_letters + string.digits, k=length))
