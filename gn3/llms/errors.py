""" Error handlers for Fahamu Api"""
import json
from requests import HTTPError


class UnprocessableEntity(HTTPError):
    """Error for  HTTP 422 Unprocessable Entity
    https://help.helpjuice.com/en_US/api-v3/api-v3#errors
    """

    def __init__(self, request, response):
        """UnprocessableEntity constructor.

        Parses out error information from the error object and passes on to the
        :obj:`HTTPError` constructor.

        Args:
            exc (:obj:`HTTPError`): Original exception.
        """
        rq_json = next(iter(json.loads(request.body.decode()).values()))
        errors = response.json()

        for field, error in errors.items():
            rq_field = rq_json.get(field, None)
            if not rq_field:
                continue

            if isinstance(error, list):
                error = error.insert(0, rq_field)
            elif isinstance(error, str):
                error = f"{rq_field} {error}"

        msg = json.dumps(errors)
        super(HTTPError, self).__init__(
            msg, request=request, response=response)


class LLMError(Exception):
    """custom exception for LLMErrorMIxins"""
