from unittest import mock, TestCase

class TestDatasetsDBFunctions(TestCase):

    def test_retrieve_trait_dataset_name(self):
        """Test that the function is called correctly."""
        for trait_type, thresh, trait_dataset_name, columns, table in [
                ["ProbeSet", 9, "testName",
                 "Id, Name, FullName, ShortName, DataScale", "ProbeSetFreeze"],
                ["Geno", 3, "genoTraitName", "Id, Name, FullName, ShortName",
                 "GenoFreeze"],
                ["Publish", 6, "publishTraitName",
                 "Id, Name, FullName, ShortName", "PublishFreeze"],
                ["Temp", 4, "tempTraitName", "Id, Name, FullName, ShortName",
                 "TempFreeze"]]:
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
                        "SELECT %(columns)s "
                        "FROM %(table)s "
                        "WHERE public > %(threshold)s AND "
                        "(Name = %(name)s OR FullName = %(name)s OR ShortName = %(name)s)".format(
                            cols=columns, ttype=trait_type),
                        {"threshold": thresh, "name": trait_dataset_name,
                         "table": table, "columns": columns})

    def test_set_probeset_riset_fields(self):
        """
        Test that the `riset` and `riset_id` fields are retrieved appropriately
        for the 'ProbeSet' trait type.
        """
        for trait_name, expected in [
                ["testProbeSetName", ()]]:
            db_mock = mock.MagicMock()
            with self.subTest(trait_name=trait_name, expected=expected):
                with db_mock.cursor() as cursor:
                    cursor.execute.return_value = ()
                    self.assertEqual(
                        set_probeset_riset_fields(trait_name, db_mock), expected)
                    cursor.execute.assert_called_once_with(
                        (
                            "SELECT InbredSet.Name, InbredSet.Id"
                            " FROM InbredSet, ProbeSetFreeze, ProbeFreeze"
                            " WHERE ProbeFreeze.InbredSetId = InbredSet.Id"
                            " AND ProbeFreeze.Id = ProbeSetFreeze.ProbeFreezeId"
                            " AND ProbeSetFreeze.Name = %(name)s"),
                        {"name": trait_name})

    def test_set_riset_fields(self):
        """
        Test that the riset fields are set up correctly for the different trait
        types.
        """
        for trait_info, expected in [
                [{}, {}],
                [{"haveinfo": 0, "type": "Publish"},
                 {"haveinfo": 0, "type": "Publish"}],
                [{"haveinfo": 0, "type": "ProbeSet"},
                 {"haveinfo": 0, "type": "ProbeSet"}],
                [{"haveinfo": 0, "type": "Geno"},
                 {"haveinfo": 0, "type": "Geno"}],
                [{"haveinfo": 0, "type": "Temp"},
                 {"haveinfo": 0, "type": "Temp"}],
                [{"haveinfo": 1, "type": "Publish", "name": "test"},
                 {"haveinfo": 1, "type": "Publish", "name": "test",
                  "riset": "riset_name", "risetid": 0}],
                [{"haveinfo": 1, "type": "ProbeSet", "name": "test"},
                 {"haveinfo": 1, "type": "ProbeSet", "name": "test",
                  "riset": "riset_name", "risetid": 0}],
                [{"haveinfo": 1, "type": "Geno", "name": "test"},
                 {"haveinfo": 1, "type": "Geno", "name": "test",
                  "riset": "riset_name", "risetid": 0}],
                [{"haveinfo": 1, "type": "Temp", "name": "test"},
                 {"haveinfo": 1, "type": "Temp", "name": "test", "riset": None,
                  "risetid": None}]
        ]:
            db_mock = mock.MagicMock()
            with self.subTest(trait_info=trait_info, expected=expected):
                with db_mock.cursor() as cursor:
                    cursor.execute.return_value = ("riset_name", 0)
                    self.assertEqual(
                        set_riset_fields(trait_info, db_mock), expected)

    def test_set_publish_riset_fields(self):
        """
        Test that the `riset` and `riset_id` fields are retrieved appropriately
        for the 'Publish' trait type.
        """
        for trait_name, expected in [
                ["testPublishName", ()]]:
            db_mock = mock.MagicMock()
            with self.subTest(trait_name=trait_name, expected=expected):
                with db_mock.cursor() as cursor:
                    cursor.execute.return_value = ()
                    self.assertEqual(
                        set_publish_riset_fields(trait_name, db_mock), expected)
                    cursor.execute.assert_called_once_with(
                        (
                            "SELECT InbredSet.Name, InbredSet.Id"
                            " FROM InbredSet, PublishFreeze"
                            " WHERE PublishFreeze.InbredSetId = InbredSet.Id"
                            " AND PublishFreeze.Name = %(name)s"),
                        {"name": trait_name})

    def test_set_geno_riset_fields(self):
        """
        Test that the `riset` and `riset_id` fields are retrieved appropriately
        for the 'Geno' trait type.
        """
        for trait_name, expected in [
                ["testGenoName", ()]]:
            db_mock = mock.MagicMock()
            with self.subTest(trait_name=trait_name, expected=expected):
                with db_mock.cursor() as cursor:
                    cursor.execute.return_value = ()
                    self.assertEqual(
                        set_geno_riset_fields(trait_name, db_mock), expected)
                    cursor.execute.assert_called_once_with(
                        (
                            "SELECT InbredSet.Name, InbredSet.Id"
                            " FROM InbredSet, GenoFreeze"
                            " WHERE GenoFreeze.InbredSetId = InbredSet.Id"
                            " AND GenoFreeze.Name = %(name)s"),
                        {"name": trait_name})
