"""module contains Bunch class a dictionary like with object notation """

from pprint import pformat as pf


class Bunch:
    """Like a dictionary but using object notation"""

    def __init__(self, **kw):
        self.__dict__ = kw

    def __repr__(self):
        return pf(self.__dict__)

    def __str__(self):
        return self.__class__.__name__
