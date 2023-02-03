"""Module for fixtures and test utilities"""
import uuid
import datetime
from contextlib import contextmanager

from gn3.auth.authentication.oauth2.models.oauth2token import OAuth2Token

from .fixtures import * # pylint: disable=[wildcard-import,unused-wildcard-import]

def get_tokeniser(user):
    """Get contextmanager for mocking token acquisition."""
    @contextmanager
    def __token__(*args, **kwargs):# pylint: disable=[unused-argument]
        yield {
            usr.user_id: OAuth2Token(
                token_id=uuid.UUID("d32611e3-07fc-4564-b56c-786c6db6de2b"),
                client=None, token_type="Bearer", access_token="123456ABCDE",
                refresh_token=None, revoked=False, expires_in=864000,
                user=usr, issued_at=int(datetime.datetime.now().timestamp()),
                scope="profile group role resource register-client")
        for usr in TEST_USERS
        }[user.user_id]

    return __token__
