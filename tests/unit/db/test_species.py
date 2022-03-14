"""Tests for db/species.py"""
from unittest import TestCase
from unittest import mock

import pytest

from gn3.db.species import get_chromosome
from gn3.db.species import get_all_species


class TestChromosomes(TestCase):
    """Test cases for fetching chromosomes"""

    @pytest.mark.unit_test
    def test_get_chromosome_using_species_name(self):
        """Test that the chromosome is fetched using a species name"""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchall.return_value = ()
            self.assertEqual(get_chromosome(name="TestCase",
                                            is_species=True,
                                            conn=db_mock), ())
            cursor.execute.assert_called_once_with(
                "SELECT Chr_Length.Name, Chr_Length.OrderId, "
                "Length FROM Chr_Length, Species WHERE "
                "Chr_Length.SpeciesId = Species.SpeciesId AND "
                "Species.Name = 'TestCase' ORDER BY OrderId"
            )

    @pytest.mark.unit_test
    def test_get_chromosome_using_group_name(self):
        """Test that the chromosome is fetched using a group name"""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchall.return_value = ()
            self.assertEqual(get_chromosome(name="TestCase",
                                            is_species=False,
                                            conn=db_mock), ())
            cursor.execute.assert_called_once_with(
                "SELECT Chr_Length.Name, Chr_Length.OrderId, "
                "Length FROM Chr_Length, InbredSet WHERE "
                "Chr_Length.SpeciesId = InbredSet.SpeciesId AND "
                "InbredSet.Name = 'TestCase' ORDER BY OrderId"
            )

    @pytest.mark.unit_test
    def test_get_all_species(self):
        """Test that species are fetched correctly"""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchall.return_value = ()
            self.assertEqual(get_all_species(db_mock), ())
            cursor.execute.assert_called_once_with(
                "SELECT Name, MenuName FROM Species ORDER BY OrderId"
            )
