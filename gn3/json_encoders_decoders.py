"""Custom json encoders for various purposes."""
import json
from uuid import UUID
from datetime import datetime

__ENCODERS__ = {
    UUID: lambda obj: {"__type": "UUID", "__value": str(obj)},
    datetime: lambda obj: {"__type": "DATETIME", "__value": obj.isoformat()}
}

class CustomJSONEncoder(json.JSONEncoder):
    """
    A custom JSON encoder to handle cases where the default encoder fails.
    """
    def default(self, obj):# pylint: disable=[arguments-renamed]
        """Return a serializable object for `obj`."""
        if type(obj) in __ENCODERS__:
            return __ENCODERS__[type(obj)](obj)
        return json.JSONEncoder.default(self, obj)


__DECODERS__ = {
    "UUID": UUID,
    "DATETIME": datetime.fromisoformat
}

def custom_json_decoder(obj_dict):
    """Decode custom types"""
    if "__type" in obj_dict:
        return __DECODERS__[obj_dict["__type"]](obj_dict["__value"])
    return obj_dict
