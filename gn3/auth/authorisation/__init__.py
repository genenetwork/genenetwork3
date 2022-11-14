"""The authorisation module."""
from typing import Union

def authorised_p(success_message: Union[str, bool] = False, error_message: Union[str, bool] = False):
    """Authorisation decorator."""
    def __authoriser__(*args, **kwargs):
        return {
            "status": "error",
            "message": error_message or "unauthorised"
        }

    return __authoriser__
