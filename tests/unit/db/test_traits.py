"""Tests for gn3/db/traits.py"""
from unittest import mock, TestCase
from gn3.db.traits import (
    GENO_TRAIT_INFO_QUERY,
    TEMP_TRAIT_INFO_QUERY,
    PUBLISH_TRAIT_INFO_QUERY,
    PROBESET_TRAIT_INFO_QUERY)
from gn3.db.traits import (
    retrieve_trait_info,
    retrieve_geno_trait_info,
    retrieve_temp_trait_info,
    retrieve_trait_dataset_name,
    retrieve_publish_trait_info,
    retrieve_probeset_trait_info,
    update_sample_data)


class TestTraitsDBFunctions(TestCase):
    "Test cases for traits functions"

    def test_retrieve_trait_dataset_name(self):
        """Test that the function is called correctly."""
        for trait_type, thresh, trait_dataset_name, columns in [
                ["ProbeSet", 9, "testName",
                 "Id, Name, FullName, ShortName, DataScale"],
                ["Geno", 3, "genoTraitName", "Id, Name, FullName, ShortName"],
                ["Publish", 6, "publishTraitName",
                 "Id, Name, FullName, ShortName"],
                ["Temp", 4, "tempTraitName", "Id, Name, FullName, ShortName"]]:
            db_mock = mock.MagicMock()
            with self.subTest(trait_type=trait_type):
                with db_mock.cursor() as cursor:
                    cursor.fetchone.return_value = (
                        "testName", "testNameFull", "testNameShort",
                        "dataScale")
                    self.assertEqual(
                        retrieve_trait_dataset_name(
                            trait_type, thresh, trait_dataset_name, db_mock),
                        ("testName", "testNameFull", "testNameShort",
                         "dataScale"))
                    cursor.execute.assert_called_once_with(
                        "SELECT {cols} "
                        "FROM {ttype}Freeze "
                        "WHERE public > %(threshold)s AND "
                        "(Name = %(name)s OR FullName = %(name)s OR ShortName = %(name)s)".format(
                            cols=columns, ttype=trait_type),
                        {"threshold": thresh, "name": trait_dataset_name})

    def test_retrieve_publish_trait_info(self):
        """Test retrieval of type `Publish` traits."""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchone.return_value = tuple()
            trait_source = {
                "trait_name": "PublishTraitName", "trait_dataset_id": 1}
            self.assertEqual(
                retrieve_publish_trait_info(
                    trait_source,
                    db_mock),
                tuple())
            cursor.execute.assert_called_once_with(
                PUBLISH_TRAIT_INFO_QUERY, trait_source)

    def test_retrieve_probeset_trait_info(self):
        """Test retrieval of type `Probeset` traits."""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchone.return_value = tuple()
            trait_source = {
                "trait_name": "ProbeSetTraitName",
                "trait_dataset_name": "ProbeSetDatasetTraitName"}
            self.assertEqual(
                retrieve_probeset_trait_info(trait_source, db_mock), tuple())
            cursor.execute.assert_called_once_with(
                PROBESET_TRAIT_INFO_QUERY, trait_source)

    def test_retrieve_geno_trait_info(self):
        """Test retrieval of type `Geno` traits."""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchone.return_value = tuple()
            trait_source = {
                "trait_name": "GenoTraitName",
                "trait_dataset_name": "GenoDatasetTraitName"}
            self.assertEqual(
                retrieve_geno_trait_info(trait_source, db_mock), tuple())
            cursor.execute.assert_called_once_with(
                GENO_TRAIT_INFO_QUERY, trait_source)

    def test_retrieve_temp_trait_info(self):
        """Test retrieval of type `Temp` traits."""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchone.return_value = tuple()
            trait_source = {"trait_name": "TempTraitName"}
            self.assertEqual(
                retrieve_temp_trait_info(trait_source, db_mock), tuple())
            cursor.execute.assert_called_once_with(
                TEMP_TRAIT_INFO_QUERY, trait_source)

    def test_retrieve_trait_info(self):
        """Test that information on traits is retrieved as appropriate."""
        for trait_type, trait_name, trait_dataset_id, trait_dataset_name, in [
                ["Publish", "PublishTraitName", 1, "PublishDatasetTraitName"],
                ["ProbeSet", "ProbeSetTraitName", 2, "ProbeSetDatasetTraitName"],
                ["Geno", "GenoTraitName", 3, "GenoDatasetTraitName"],
                ["Temp", "TempTraitName", 4, "TempDatasetTraitName"]]:
            db_mock = mock.MagicMock()
            with self.subTest(trait_type=trait_type):
                with db_mock.cursor() as cursor:
                    cursor.fetchone.return_value = tuple()
                    self.assertEqual(
                        retrieve_trait_info(
                            trait_type, trait_name, trait_dataset_id,
                            trait_dataset_name, db_mock),
                        tuple())

    def test_update_sample_data(self):
        """Test that the SQL queries when calling update_sample_data are called with
        the right calls.

        """
        db_mock = mock.MagicMock()

        STRAIN_ID_SQL: str = "UPDATE Strain SET Name = %s WHERE Id = %s"
        PUBLISH_DATA_SQL: str = ("UPDATE PublishData SET value = %s "
                                 "WHERE StrainId = %s AND Id = %s")
        PUBLISH_SE_SQL: str = ("UPDATE PublishSE SET error = %s "
                               "WHERE StrainId = %s AND DataId = %s")
        N_STRAIN_SQL: str = ("UPDATE NStrain SET count = %s "
                             "WHERE StrainId = %s AND DataId = %s")

        with db_mock.cursor() as cursor:
            type(cursor).rowcount = 1
            self.assertEqual(update_sample_data(
                conn=db_mock, strain_name="BXD11",
                strain_id=10, publish_data_id=8967049,
                value=18.7, error=2.3, count=2),
                             (1, 1, 1, 1))
            cursor.execute.assert_has_calls(
                [mock.call(STRAIN_ID_SQL, ('BXD11', 10)),
                 mock.call(PUBLISH_DATA_SQL, (18.7, 10, 8967049)),
                 mock.call(PUBLISH_SE_SQL, (2.3, 10, 8967049)),
                 mock.call(N_STRAIN_SQL, (2, 10, 8967049))]
            )
