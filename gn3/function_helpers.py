"""
This module will contain helper functions that should assist in maintaining a
mostly functional way of programming.

It will also contain miscellaneous functions that can be used globally, and thus
do not fit well in any other module.

FUNCTIONS:
compose: This function is used to compose multiple functions into a single
    function. It passes the results of calling one function to the other until
    all the functions to be composed are called.
"""
from functools import reduce

def compose(*functions):
    """Compose multiple functions into a single function.

    The utility in this function is not specific to this module, and as such,
    this function can, and probably should, be moved to a more global module.

    DESCRIPTION:
    Given `cfn = compose(f_1, f_2, ... f_(n-1), f_n )`, calling
    `cfn(arg_1, arg_2, ..., arg_m)` should call `f_n` with the arguments passed
    to `cfn` and the results of that should be passed as arguments to `f_(n-1)`
    and so on until `f_1` is called with the results of the cumulative calls and
    that is the result of the entire chain of calls.

    PARAMETERS:
    functions: a variable argument list of function.
    """
    def composed_function(*args, **kwargs):
        return reduce(
            lambda res, fn: fn(res),
            reversed(functions[:-1]),
            functions[-1](*args, **kwargs))
    return composed_function
