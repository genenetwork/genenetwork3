"""Tests for db/phenotypes.py"""
from unittest import TestCase
from unittest import mock

import pytest

from gn3.db import diff_from_dict


class TestCrudMethods(TestCase):
    """Test cases for CRUD methods"""

    @pytest.mark.unit_test
    def test_diff_from_dict(self):
        """Test that a correct diff is generated"""
        self.assertEqual(diff_from_dict({"id": 1, "data": "a"},
                                        {"id": 2, "data": "b"}),
                         {"id": {"old": 1, "new": 2},
                          "data": {"old": "a", "new": "b"}})
