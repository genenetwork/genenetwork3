"""Tests for gn3/db/traits.py"""
from unittest import mock, TestCase
import pytest
from gn3.db.traits import (
    build_trait_name,
    export_trait_data,
    export_informative,
    set_haveinfo_field,
    update_sample_data,
    retrieve_trait_info,
    set_confidential_field,
    set_homologene_id_field,
    retrieve_geno_trait_info,
    retrieve_temp_trait_info,
    retrieve_publish_trait_info,
    retrieve_probeset_trait_info)

samplelist = ["B6cC3-1", "BXD1", "BXD12", "BXD16", "BXD19", "BXD2"]
trait_data = {
    "mysqlid": 36688172,
    "data": {
        "B6cC3-1": {"sample_name": "B6cC3-1", "value": 7.51879, "variance": None, "ndata": None},
        "BXD1": {"sample_name": "BXD1", "value": 7.77141, "variance": None, "ndata": None},
        "BXD12": {"sample_name": "BXD12", "value": 8.39265, "variance": None, "ndata": None},
        "BXD16": {"sample_name": "BXD16", "value": 8.17443, "variance": None, "ndata": None},
        "BXD19": {"sample_name": "BXD19", "value": 8.30401, "variance": None, "ndata": None},
        "BXD2": {"sample_name": "BXD2", "value": 7.80944, "variance": None, "ndata": None},
        "BXD21": {"sample_name": "BXD21", "value": 8.93809, "variance": None, "ndata": None},
        "BXD24": {"sample_name": "BXD24", "value": 7.99415, "variance": None, "ndata": None},
        "BXD27": {"sample_name": "BXD27", "value": 8.12177, "variance": None, "ndata": None},
        "BXD28": {"sample_name": "BXD28", "value": 7.67688, "variance": None, "ndata": None},
        "BXD32": {"sample_name": "BXD32", "value": 7.79062, "variance": None, "ndata": None},
        "BXD39": {"sample_name": "BXD39", "value": 8.27641, "variance": None, "ndata": None},
        "BXD40": {"sample_name": "BXD40", "value": 8.18012, "variance": None, "ndata": None},
        "BXD42": {"sample_name": "BXD42", "value": 7.82433, "variance": None, "ndata": None},
        "BXD6": {"sample_name": "BXD6", "value": 8.09718, "variance": None, "ndata": None},
        "BXH14": {"sample_name": "BXH14", "value": 7.97475, "variance": None, "ndata": None},
        "BXH19": {"sample_name": "BXH19", "value": 7.67223, "variance": None, "ndata": None},
        "BXH2": {"sample_name": "BXH2", "value": 7.93622, "variance": None, "ndata": None},
        "BXH22": {"sample_name": "BXH22", "value": 7.43692, "variance": None, "ndata": None},
        "BXH4": {"sample_name": "BXH4", "value": 7.96336, "variance": None, "ndata": None},
        "BXH6": {"sample_name": "BXH6", "value": 7.75132, "variance": None, "ndata": None},
        "BXH7": {"sample_name": "BXH7", "value": 8.12927, "variance": None, "ndata": None},
        "BXH8": {"sample_name": "BXH8", "value": 6.77338, "variance": None, "ndata": None},
        "BXH9": {"sample_name": "BXH9", "value": 8.03836, "variance": None, "ndata": None},
        "C3H/HeJ": {"sample_name": "C3H/HeJ", "value": 7.42795, "variance": None, "ndata": None},
        "C57BL/6J": {"sample_name": "C57BL/6J", "value": 7.50606, "variance": None, "ndata": None},
        "DBA/2J": {"sample_name": "DBA/2J", "value": 7.72588, "variance": None, "ndata": None}}}

class TestTraitsDBFunctions(TestCase):
    "Test cases for traits functions"

    @pytest.mark.unit_test
    def test_retrieve_publish_trait_info(self):
        """Test retrieval of type `Publish` traits."""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchone.return_value = tuple()
            trait_source = {
                "trait_name": "PublishTraitName", "trait_dataset_id": 1}
            self.assertEqual(
                retrieve_publish_trait_info(trait_source, db_mock), {})
            cursor.execute.assert_called_once_with(
                ("SELECT "
                 "PublishXRef.Id, Publication.PubMed_ID,"
                 " Phenotype.Pre_publication_description,"
                 " Phenotype.Post_publication_description,"
                 " Phenotype.Original_description,"
                 " Phenotype.Pre_publication_abbreviation,"
                 " Phenotype.Post_publication_abbreviation,"
                 " Phenotype.Lab_code, Phenotype.Submitter, Phenotype.Owner,"
                 " Phenotype.Authorized_Users,"
                 " CAST(Publication.Authors AS BINARY),"
                 " Publication.Title, Publication.Abstract,"
                 " Publication.Journal,"
                 " Publication.Volume, Publication.Pages, Publication.Month,"
                 " Publication.Year, PublishXRef.Sequence, Phenotype.Units,"
                 " PublishXRef.comments"
                 " FROM"
                 " PublishXRef, Publication, Phenotype"
                 " WHERE"
                 " PublishXRef.Id = %(trait_name)s"
                 " AND Phenotype.Id = PublishXRef.PhenotypeId"
                 " AND Publication.Id = PublishXRef.PublicationId"
                 " AND PublishXRef.InbredSetId = %(trait_dataset_id)s"),
                trait_source)

    @pytest.mark.unit_test
    def test_retrieve_probeset_trait_info(self):
        """Test retrieval of type `Probeset` traits."""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchone.return_value = tuple()
            trait_source = {
                "trait_name": "ProbeSetTraitName",
                "trait_dataset_name": "ProbeSetDatasetTraitName"}
            self.assertEqual(
                retrieve_probeset_trait_info(trait_source, db_mock), {})
            cursor.execute.assert_called_once_with(
                (
                    "SELECT "
                    "ProbeSet.name, ProbeSet.symbol, ProbeSet.description, "
                    "ProbeSet.probe_target_description, ProbeSet.chr, "
                    "ProbeSet.mb, ProbeSet.alias, ProbeSet.geneid, "
                    "ProbeSet.genbankid, ProbeSet.unigeneid, ProbeSet.omim, "
                    "ProbeSet.refseq_transcriptid, ProbeSet.blatseq, "
                    "ProbeSet.targetseq, ProbeSet.chipid, ProbeSet.comments, "
                    "ProbeSet.strand_probe, ProbeSet.strand_gene, "
                    "ProbeSet.probe_set_target_region, ProbeSet.proteinid, "
                    "ProbeSet.probe_set_specificity, "
                    "ProbeSet.probe_set_blat_score, "
                    "ProbeSet.probe_set_blat_mb_start, "
                    "ProbeSet.probe_set_blat_mb_end, "
                    "ProbeSet.probe_set_strand, ProbeSet.probe_set_note_by_rw, "
                    "ProbeSet.flag "
                    "FROM "
                    "ProbeSet, ProbeSetFreeze, ProbeSetXRef "
                    "WHERE "
                    "ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id "
                    "AND ProbeSetXRef.ProbeSetId = ProbeSet.Id "
                    "AND ProbeSetFreeze.Name = %(trait_dataset_name)s "
                    "AND ProbeSet.Name = %(trait_name)s"), trait_source)

    @pytest.mark.unit_test
    def test_retrieve_geno_trait_info(self):
        """Test retrieval of type `Geno` traits."""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchone.return_value = tuple()
            trait_source = {
                "trait_name": "GenoTraitName",
                "trait_dataset_name": "GenoDatasetTraitName"}
            self.assertEqual(
                retrieve_geno_trait_info(trait_source, db_mock), {})
            cursor.execute.assert_called_once_with(
                (
                    "SELECT "
                    "Geno.name, Geno.chr, Geno.mb, Geno.source2, Geno.sequence "
                    "FROM "
                    "Geno INNER JOIN GenoXRef ON GenoXRef.GenoId = Geno.Id "
                    "INNER JOIN GenoFreeze ON GenoFreeze.Id = GenoXRef.GenoFreezeId "
                    "WHERE "
                    "GenoFreeze.Name = %(trait_dataset_name)s "
                    "AND Geno.Name = %(trait_name)s"),
                trait_source)

    @pytest.mark.unit_test
    def test_retrieve_temp_trait_info(self):
        """Test retrieval of type `Temp` traits."""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchone.return_value = tuple()
            trait_source = {"trait_name": "TempTraitName"}
            self.assertEqual(
                retrieve_temp_trait_info(trait_source, db_mock), {})
            cursor.execute.assert_called_once_with(
                "SELECT name, description FROM Temp WHERE Name = %(trait_name)s",
                trait_source)

    @pytest.mark.unit_test
    def test_build_trait_name_with_good_fullnames(self):
        """
        Check that the name is built correctly.
        """
        for fullname, expected in [
                ["testdb::testname",
                 {"db": {"dataset_name": "testdb", "dataset_type": "ProbeSet"},
                  "trait_name": "testname", "cellid": "",
                  "trait_fullname": "testdb::testname"}],
                ["testdb::testname::testcell",
                 {"db": {"dataset_name": "testdb", "dataset_type": "ProbeSet"},
                  "trait_name": "testname", "cellid": "testcell",
                  "trait_fullname": "testdb::testname::testcell"}]]:
            with self.subTest(fullname=fullname):
                self.assertEqual(build_trait_name(fullname), expected)

    @pytest.mark.unit_test
    def test_build_trait_name_with_bad_fullnames(self):
        """
        Check that an exception is raised if the full name format is wrong.
        """
        for fullname in ["", "test", "test:test"]:
            with self.subTest(fullname=fullname):
                with self.assertRaises(AssertionError, msg="Name format error"):
                    build_trait_name(fullname)

    @pytest.mark.unit_test
    def test_retrieve_trait_info(self):
        """Test that information on traits is retrieved as appropriate."""
        for threshold, trait_fullname, expected in [
                [9, "pubDb::PublishTraitName::pubCell", {"haveinfo": 0}],
                [5, "prbDb::ProbeSetTraitName::prbCell", {"haveinfo": 0}],
                [12, "genDb::GenoTraitName", {"haveinfo": 0}],
                [6, "tmpDb::TempTraitName", {"haveinfo": 0}]]:
            db_mock = mock.MagicMock()
            with self.subTest(trait_fullname=trait_fullname):
                with db_mock.cursor() as cursor:
                    cursor.fetchone.return_value = tuple()
                    self.assertEqual(
                        retrieve_trait_info(
                            threshold, trait_fullname, db_mock),
                        expected)

    @pytest.mark.unit_test
    def test_update_sample_data(self):
        """Test that the SQL queries when calling update_sample_data are called with
        the right calls.

        """
        # pylint: disable=C0103
        db_mock = mock.MagicMock()
        PUBLISH_DATA_SQL: str = (
            "UPDATE PublishData SET value = %s "
            "WHERE StrainId = %s AND Id = %s")
        PUBLISH_SE_SQL: str = (
            "UPDATE PublishSE SET error = %s "
            "WHERE StrainId = %s AND DataId = %s")
        N_STRAIN_SQL: str = (
            "UPDATE NStrain SET count = %s "
            "WHERE StrainId = %s AND DataId = %s")

        with db_mock.cursor() as cursor:
            type(cursor).rowcount = 1
            mock_fetchone = mock.MagicMock()
            mock_fetchone.return_value = (1, 1)
            type(cursor).fetchone = mock_fetchone
            self.assertEqual(update_sample_data(
                conn=db_mock, strain_name="BXD11",
                trait_name="1",
                phenotype_id=10, value=18.7,
                error=2.3, count=2),
                             (1, 1, 1))
            cursor.execute.assert_has_calls(
                [mock.call(('SELECT Strain.Id, PublishData.Id FROM'
                            ' (PublishData, Strain, PublishXRef, '
                            'PublishFreeze) LEFT JOIN PublishSE ON '
                            '(PublishSE.DataId = PublishData.Id '
                            'AND PublishSE.StrainId = '
                            'PublishData.StrainId) LEFT JOIN NStrain ON '
                            '(NStrain.DataId = PublishData.Id AND '
                            'NStrain.StrainId = PublishData.StrainId) WHERE '
                            'PublishXRef.InbredSetId = '
                            'PublishFreeze.InbredSetId AND PublishData.Id = '
                            'PublishXRef.DataId AND PublishXRef.Id = %s AND '
                            'PublishXRef.PhenotypeId = %s AND '
                            'PublishData.StrainId = Strain.Id AND '
                            'Strain.Name = %s'),
                           ("1", 10, "BXD11")),
                 mock.call(PUBLISH_DATA_SQL, (18.7, 1, 1)),
                 mock.call(PUBLISH_SE_SQL, (2.3, 1, 1)),
                 mock.call(N_STRAIN_SQL, (2, 1, 1))]
            )

    @pytest.mark.unit_test
    def test_set_haveinfo_field(self):
        """Test that the `haveinfo` field is set up correctly"""
        for trait_info, expected in [
                [{}, {"haveinfo": 0}],
                [{"k1": "v1"}, {"k1": "v1", "haveinfo": 1}]]:
            with self.subTest(trait_info=trait_info, expected=expected):
                self.assertEqual(set_haveinfo_field(trait_info), expected)

    @pytest.mark.unit_test
    def test_set_homologene_id_field(self):
        """Test that the `homologene_id` field is set up correctly"""
        for trait_type, trait_info, expected in [
                ["Publish", {}, {"homologeneid": None}],
                ["ProbeSet", {}, {"homologeneid": None}],
                ["Geno", {}, {"homologeneid": None}],
                ["Temp", {}, {"homologeneid": None}]]:
            db_mock = mock.MagicMock()
            with self.subTest(trait_info=trait_info, expected=expected):
                with db_mock.cursor() as cursor:
                    cursor.fetchone.return_value = ()
                    self.assertEqual(
                        set_homologene_id_field(trait_type, trait_info, db_mock), expected)

    @pytest.mark.unit_test
    def test_set_confidential_field(self):
        """Test that the `confidential` field is set up correctly"""
        for trait_type, trait_info, expected in [
                ["Publish", {}, {"confidential": 0}],
                ["ProbeSet", {}, {}],
                ["Geno", {}, {}],
                ["Temp", {}, {}]]:
            with self.subTest(trait_info=trait_info, expected=expected):
                self.assertEqual(
                    set_confidential_field(trait_type, trait_info), expected)

    @pytest.mark.unit_test
    def test_export_trait_data_dtype(self):
        """
        Test `export_trait_data` with different values for the `dtype` keyword
        argument
        """
        for dtype, expected in [
                ["val", (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["var", (None, None, None, None, None, None)],
                ["N", (None, None, None, None, None, None)],
                ["all", (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)]]:
            with self.subTest(dtype=dtype):
                self.assertEqual(
                    export_trait_data(trait_data, samplelist, dtype=dtype),
                    expected)

    @pytest.mark.unit_test
    def test_export_trait_data_dtype_all_flags(self):
        """
        Test `export_trait_data` with different values for the `dtype` keyword
        argument and the different flags set up
        """
        for dtype, vflag, nflag, expected in [
                ["val", False, False,
                 (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["val", False, True,
                 (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["val", True, False,
                 (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["val", True, True,
                 (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["var", False, False, (None, None, None, None, None, None)],
                ["var", False, True, (None, None, None, None, None, None)],
                ["var", True, False, (None, None, None, None, None, None)],
                ["var", True, True, (None, None, None, None, None, None)],
                ["N", False, False, (None, None, None, None, None, None)],
                ["N", False, True, (None, None, None, None, None, None)],
                ["N", True, False, (None, None, None, None, None, None)],
                ["N", True, True, (None, None, None, None, None, None)],
                ["all", False, False,
                 (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["all", False, True,
                 (7.51879, None, 7.77141, None, 8.39265, None, 8.17443, None,
                  8.30401, None, 7.80944, None)],
                ["all", True, False,
                 (7.51879, None, 7.77141, None, 8.39265, None, 8.17443, None,
                  8.30401, None, 7.80944, None)],
                ["all", True, True,
                 (7.51879, None, None, 7.77141, None, None, 8.39265, None, None,
                  8.17443, None, None, 8.30401, None, None, 7.80944, None, None)]
        ]:
            with self.subTest(dtype=dtype, vflag=vflag, nflag=nflag):
                self.assertEqual(
                    export_trait_data(
                        trait_data, samplelist, dtype=dtype, var_exists=vflag,
                        n_exists=nflag),
                    expected)

    @pytest.mark.unit_test
    def test_export_informative(self):
        """Test that the function exports appropriate data."""
        # pylint: disable=W0621
        for trait_data, inc_var, expected in [
                [{"data": {
                    "sample1": {
                        "sample_name": "sample1", "value": 9, "variance": None,
                        "ndata": 13
                    },
                    "sample2": {
                        "sample_name": "sample2", "value": 8, "variance": None,
                        "ndata": 13
                    },
                    "sample3": {
                        "sample_name": "sample3", "value": 7, "variance": None,
                        "ndata": 13
                    },
                    "sample4": {
                        "sample_name": "sample4", "value": 6, "variance": None,
                        "ndata": 13
                    },
                }}, 0, (
                    ("sample1", "sample2", "sample3", "sample4"), (9, 8, 7, 6),
                    (None, None, None, None))],
                [{"data": {
                    "sample1": {
                        "sample_name": "sample1", "value": 9, "variance": None,
                        "ndata": 13
                    },
                    "sample2": {
                        "sample_name": "sample2", "value": 8, "variance": None,
                        "ndata": 13
                    },
                    "sample3": {
                        "sample_name": "sample3", "value": None, "variance": None,
                        "ndata": 13
                    },
                    "sample4": {
                        "sample_name": "sample4", "value": 6, "variance": None,
                        "ndata": 13
                    },
                }}, 0, (
                    ("sample1", "sample2", "sample4"), (9, 8, 6),
                    (None, None, None))],
                [{"data": {
                    "sample1": {
                        "sample_name": "sample1", "value": 9, "variance": None,
                        "ndata": 13
                    },
                    "sample2": {
                        "sample_name": "sample2", "value": 8, "variance": None,
                        "ndata": 13
                    },
                    "sample3": {
                        "sample_name": "sample3", "value": 7, "variance": None,
                        "ndata": 13
                    },
                    "sample4": {
                        "sample_name": "sample4", "value": 6, "variance": None,
                        "ndata": 13
                    },
                }}, True, (tuple(), tuple(), tuple())],
                [{"data": {
                    "sample1": {
                        "sample_name": "sample1", "value": 9, "variance": None,
                        "ndata": 13
                    },
                    "sample2": {
                        "sample_name": "sample2", "value": 8, "variance": 0.657,
                        "ndata": 13
                    },
                    "sample3": {
                        "sample_name": "sample3", "value": 7, "variance": None,
                        "ndata": 13
                    },
                    "sample4": {
                        "sample_name": "sample4", "value": 6, "variance": None,
                        "ndata": 13
                    },
                }}, 0, (
                    ("sample1", "sample2", "sample3", "sample4"), (9, 8, 7, 6),
                    (None, 0.657, None, None))]]:
            with self.subTest(trait_data=trait_data):
                self.assertEqual(
                    export_informative(trait_data, inc_var), expected)
