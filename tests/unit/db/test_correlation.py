"""
Tests for the gn3.db.correlations module
"""

from unittest import TestCase

from gn3.db.correlations import (
    build_query_sgo_lit_corr,
    build_query_tissue_corr)

class TestCorrelation(TestCase):
    """Test cases for correlation data fetching functions"""
    maxDiff = None

    def test_build_query_sgo_lit_corr(self):
        """
        Test that the literature correlation query is built correctly.
        """
        self.assertEqual(
            build_query_sgo_lit_corr(
                "Probeset",
                "temp_table_xy45i7wd",
                "T1.value, T2.value, T3.value",
                (("LEFT JOIN ProbesetData AS T1 "
                  "ON T1.Id = ProbesetXRef.DataId "
                  "AND T1.StrainId=%(T1_sample_id)s"),
                 (
                     "LEFT JOIN ProbesetData AS T2 "
                     "ON T2.Id = ProbesetXRef.DataId "
                     "AND T2.StrainId=%(T2_sample_id)s"),
                 (
                     "LEFT JOIN ProbesetData AS T3 "
                     "ON T3.Id = ProbesetXRef.DataId "
                     "AND T3.StrainId=%(T3_sample_id)s"))),
            (("SELECT Probeset.Name, temp_table_xy45i7wd.value, "
              "T1.value, T2.value, T3.value "
              "FROM (Probeset, ProbesetXRef, ProbesetFreeze) "
              "LEFT JOIN temp_table_xy45i7wd ON temp_table_xy45i7wd.GeneId2=ProbeSet.GeneId "
              "LEFT JOIN ProbesetData AS T1 "
              "ON T1.Id = ProbesetXRef.DataId "
              "AND T1.StrainId=%(T1_sample_id)s "
              "LEFT JOIN ProbesetData AS T2 "
              "ON T2.Id = ProbesetXRef.DataId "
              "AND T2.StrainId=%(T2_sample_id)s "
              "LEFT JOIN ProbesetData AS T3 "
              "ON T3.Id = ProbesetXRef.DataId "
              "AND T3.StrainId=%(T3_sample_id)s "
              "WHERE ProbeSet.GeneId IS NOT NULL "
              "AND temp_table_xy45i7wd.value IS NOT NULL "
              "AND ProbesetXRef.ProbesetFreezeId = ProbesetFreeze.Id "
              "AND ProbesetFreeze.Name = %(db_name)s "
              "AND Probeset.Id = ProbesetXRef.ProbesetId "
              "ORDER BY Probeset.Id"),
             2))

    def test_build_query_tissue_corr(self):
        """
        Test that the tissue correlation query is built correctly.
        """
        self.assertEqual(
            build_query_tissue_corr(
                "Probeset",
                "temp_table_xy45i7wd",
                "T1.value, T2.value, T3.value",
                (("LEFT JOIN ProbesetData AS T1 "
                  "ON T1.Id = ProbesetXRef.DataId "
                  "AND T1.StrainId=%(T1_sample_id)s"),
                 (
                     "LEFT JOIN ProbesetData AS T2 "
                     "ON T2.Id = ProbesetXRef.DataId "
                     "AND T2.StrainId=%(T2_sample_id)s"),
                 (
                     "LEFT JOIN ProbesetData AS T3 "
                     "ON T3.Id = ProbesetXRef.DataId "
                     "AND T3.StrainId=%(T3_sample_id)s"))),
            (("SELECT Probeset.Name, temp_table_xy45i7wd.Correlation, "
              "temp_table_xy45i7wd.PValue, "
              "T1.value, T2.value, T3.value "
              "FROM (Probeset, ProbesetXRef, ProbesetFreeze) "
              "LEFT JOIN temp_table_xy45i7wd ON temp_table_xy45i7wd.Symbol=ProbeSet.Symbol "
              "LEFT JOIN ProbesetData AS T1 "
              "ON T1.Id = ProbesetXRef.DataId "
              "AND T1.StrainId=%(T1_sample_id)s "
              "LEFT JOIN ProbesetData AS T2 "
              "ON T2.Id = ProbesetXRef.DataId "
              "AND T2.StrainId=%(T2_sample_id)s "
              "LEFT JOIN ProbesetData AS T3 "
              "ON T3.Id = ProbesetXRef.DataId "
              "AND T3.StrainId=%(T3_sample_id)s "
              "WHERE ProbeSet.Symbol IS NOT NULL "
              "AND temp_table_xy45i7wd.Correlation IS NOT NULL "
              "AND ProbesetXRef.ProbesetFreezeId = ProbesetFreeze.Id "
              "AND ProbesetFreeze.Name = %(db_name)s "
              "AND Probeset.Id = ProbesetXRef.ProbesetId "
              "ORDER BY Probeset.Id"),
             3))
