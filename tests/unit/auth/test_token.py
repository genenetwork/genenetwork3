"""Test the OAuth2 authorisation"""

import pytest

from gn3.auth import db

SUCCESS_RESULT = {
    "status_code": 200,
    "result": {
        "access_token": "123456ABCDE",
        "expires_in": 864000,
        "scope": "profile",
        "token_type": "Bearer"}}

USERNAME_PASSWORD_FAIL_RESULT = {
    "status_code": 400,
    "result": {
        'error': 'invalid_request',
        'error_description': 'Invalid "username" or "password" in request.'}}

def gen_token(client, grant_type, user, scope): # pylint: disable=[unused-argument]
    """Generate tokens for tests"""
    return "123456ABCDE"

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "test_data,expected",
    ((("group@lead.er", "password_for_user_001", 0), SUCCESS_RESULT),
     (("group@mem.ber01", "password_for_user_002", 1), SUCCESS_RESULT),
     (("group@mem.ber02", "password_for_user_003", 2), SUCCESS_RESULT),
     (("unaff@iliated.user", "password_for_user_004", 3), SUCCESS_RESULT),
     (("group@lead.er", "brrr", 0), USERNAME_PASSWORD_FAIL_RESULT),
     (("group@mem.ber010", "password_for_user_002", 1), USERNAME_PASSWORD_FAIL_RESULT),
     (("papa", "yada", 2), USERNAME_PASSWORD_FAIL_RESULT),
     # (("unaff@iliated.user", "password_for_user_004", 1), USERNAME_PASSWORD_FAIL_RESULT)
     ))
def test_token(fxtr_app, fxtr_oauth2_clients, test_data, expected):
    """
    GIVEN: a registered oauth2 client, a user
    WHEN: a token is requested via the 'password' grant
    THEN: check that:
      a) when email and password are valid, we get a token back
      b) when either email or password or both are invalid, we get error message
         back
      c) TODO: when user tries to use wrong client, we get error message back
    """
    conn, oa2clients = fxtr_oauth2_clients
    email, password, client_idx = test_data
    data = {
        "grant_type": "password", "scope": "profile nonexistent-scope",
        "client_id": oa2clients[client_idx].client_id,
        "client_secret": oa2clients[client_idx].client_secret,
        "username": email, "password": password}

    with fxtr_app.test_client() as client, db.cursor(conn) as cursor:
        res = client.post("/api/oauth2/token", data=data)
        # cleanup db
        cursor.execute("DELETE FROM oauth2_tokens WHERE access_token=?",
                       (gen_token(None, None, None, None),))
    assert res.status_code == expected["status_code"]
    for key in expected["result"]:
        assert res.json[key] == expected["result"][key]
