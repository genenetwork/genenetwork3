"""Tests for db/traits.py"""
from unittest import TestCase
from unittest import mock

from gn3.db.traits import update_sample_data


class TestTraitsSqlMethods(TestCase):
    """Test cases for sql operations that affect traits"""
    def test_update_sample_data(self):
        """Test that the SQL queries when calling update_sample_data are called with
        the right calls.

        """
        db_mock = mock.MagicMock()

        STRAIN_ID_SQL: str = "UPDATE Strain SET Name = '%s' WHERE Id = %s"
        PUBLISH_DATA_SQL: str = ("UPDATE PublishData SET value = %s "
                                 "WHERE StrainId = %s AND DataId = %s")
        PUBLISH_SE_SQL: str = ("UPDATE PublishSE SET error = %s "
                               "WHERE StrainId = %s AND DataId = %s")
        N_STRAIN_SQL: str = ("UPDATE NStrain SET count = '%s' "
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
