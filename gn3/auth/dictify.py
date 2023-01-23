"""Module for dictifying objects"""

from typing import Any

# TYPE = TypeVar("TYPE")

__dictifiers__ = {}#: dict[TYPE, Callable[[TYPE], dict[str, Any]]] = {}

# def register_dictifier(obj_type: TYPE, dictifier: Callable[[TYPE], dict[str, Any]]):
def register_dictifier(obj_type, dictifier):
    """Register a new dictifier function"""
    global __dictifiers__ # pylint: disable=[global-variable-not-assigned]
    __dictifiers__[obj_type] = dictifier

def dictify(obj: Any) -> dict[str, Any]:
    """Turn `obj` to a dict representation."""
    return __dictifiers__[type(obj)](obj)
