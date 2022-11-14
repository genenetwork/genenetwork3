"""Test functions dealing with group management."""
from uuid import UUID

import pytest

from gn3.auth.authorisation.groups import create_group

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "user_id,expected", (
    ("ecb52977-3004-469e-9428-2a1856725c7f", {
        "status": "success",
        "message": "Successfully created group!",
        "group_id": UUID("d32611e3-07fc-4564-b56c-786c6db6de2b")
    }),
    ("21351b66-8aad-475b-84ac-53ce528451e3", {
        "status": "error", "message": "unauthorised"}),
    ("ae9c6245-0966-41a5-9a5e-20885a96bea7", {
        "status": "error", "message": "unauthorised"}),
    ("9a0c7ce5-2f40-4e78-979e-bf3527a59579", {
        "status": "error", "message": "unauthorised"}),
    ("e614247d-84d2-491d-a048-f80b578216cb", {
        "status": "error", "message": "unauthorised"})))
def test_create_group(test_users, user_id, expected):
    assert create_group("a_test_group") == expected
