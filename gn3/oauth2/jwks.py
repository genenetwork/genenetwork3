"""Utilities dealing with JSON Web Keys (JWK)"""
from urllib.parse import urljoin

import requests
from flask import current_app as app
from authlib.jose.errors import BadSignatureError
from authlib.jose import KeySet, JsonWebKey, JsonWebToken

from gn3.oauth2.errors import TokenValidationError


def fetch_jwks(authserveruri: str, path: str = "auth/public-jwks") -> KeySet:
    """Fetch the JWKs from a particular URI"""
    try:
        response = requests.get(urljoin(authserveruri, path))
        if response.status_code == 200:
            return KeySet([
                JsonWebKey.import_key(key) for key in response.json()["jwks"]])
    except Exception as _exc:
        app.logger.debug("There was an error fetching the JSON Web Keys.",
                         exc_info=True)

    return KeySet([])


def validate_token(token: str, keys: KeySet) -> dict:
    """Validate the token against the given keys."""
    for key in keys.keys:
        kd = key.as_dict()
        try:
            return JsonWebToken(["RS256"]).decode(token, key=key)
        except BadSignatureError as _bse:
            pass

    raise TokenValidationError("No key was found for validation.")
