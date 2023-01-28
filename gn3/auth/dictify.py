"""Module for dictifying objects"""

from typing import Any, Protocol

class Dictifiable(Protocol):# pylint: disable=[too-few-public-methods]
    """Type annotation for generic object with a `dictify` method."""
    def dictify(self):
        """Convert the object to a dict"""

def dictify(obj: Dictifiable) -> dict[str, Any]:
    """Turn `obj` to a dict representation."""
    return obj.dictify()
