"""Tests for gn3.db.sample_data"""
import pytest
import gn3

from gn3.db.sample_data import __extract_actions
from gn3.db.sample_data import delete_sample_data
from gn3.db.sample_data import insert_sample_data
from gn3.db.sample_data import update_sample_data


@pytest.mark.unit_test
def test_insert_sample_data(mocker):
    """Test that inserts work properly"""
    mock_conn = mocker.MagicMock()
    strain_id, data_id, inbredset_id = 1, 17373, 20
    with mock_conn.cursor() as cursor:
        cursor.fetchone.side_effect = (
            0,
            [
                19,
            ],
            0,
            0,
        )
        mocker.patch(
            "gn3.db.sample_data.get_sample_data_ids",
            return_value=(strain_id, data_id, inbredset_id),
        )
        insert_sample_data(
            conn=mock_conn,
            trait_name=35,
            data="BXD1,18,3,0,Red,M",
            csv_header="Strain Name,Value,SE,Count,Color,Sex (13)",
            phenotype_id=10007,
        )
        calls = [
            mocker.call(
                "SELECT Id FROM PublishData where Id = %s AND StrainId = %s",
                (17373, 1),
            ),
            mocker.call(
                "INSERT INTO PublishData (StrainId, Id, value) "
                "VALUES (%s, %s, %s)",
                (1, 17373, "18"),
            ),
            mocker.call(
                "INSERT INTO PublishSE (StrainId, DataId, error) VALUES "
                "(%s, %s, %s)",
                (1, 17373, "3"),
            ),
            mocker.call(
                "INSERT INTO NStrain (StrainId, DataId, count) VALUES "
                "(%s, %s, %s)",
                (1, 17373, "0"),
            ),
            mocker.call(
                "SELECT Id FROM CaseAttribute WHERE Name = %s", ("Color",)
            ),
            mocker.call(
                "SELECT StrainId FROM CaseAttributeXRefNew WHERE "
                "StrainId = %s AND CaseAttributeId = %s AND InbredSetId = %s",
                (1, 19, 20),
            ),
            mocker.call(
                "INSERT INTO CaseAttributeXRefNew (StrainId, "
                "CaseAttributeId, Value, InbredSetId) VALUES "
                "(%s, %s, %s, %s)",
                (1, 19, "Red", 20),
            ),
            mocker.call(
                "SELECT StrainId FROM CaseAttributeXRefNew WHERE "
                "StrainId = %s AND CaseAttributeId = %s AND "
                "InbredSetId = %s",
                (1, "13", 20),
            ),
            mocker.call(
                "INSERT INTO CaseAttributeXRefNew (StrainId, "
                "CaseAttributeId, Value, InbredSetId) VALUES "
                "(%s, %s, %s, %s)",
                (1, "13", "M", 20),
            ),
        ]
        cursor.execute.assert_has_calls(calls, any_order=False)


@pytest.mark.unit_test
def test_delete_sample_data(mocker):
    """Test that deletes work properly"""
    mock_conn = mocker.MagicMock()
    strain_id, data_id, inbredset_id = 1, 17373, 20
    with mock_conn.cursor() as cursor:
        mocker.patch(
            "gn3.db.sample_data.get_sample_data_ids",
            return_value=(strain_id, data_id, inbredset_id),
        )
        delete_sample_data(
            conn=mock_conn,
            trait_name=35,
            data="BXD1,18,3,0,Red,M",
            csv_header="Strain Name,Value,SE,Count,Color,Sex (17)",
            phenotype_id=10007,
        )
        calls = [
            mocker.call(
                "DELETE FROM PublishData WHERE StrainId = %s AND Id = %s",
                (strain_id, data_id),
            ),
            mocker.call(
                "DELETE FROM PublishSE WHERE StrainId = %s AND DataId = %s",
                (strain_id, data_id),
            ),
            mocker.call(
                "DELETE FROM NStrain WHERE StrainId = %s AND DataId = %s",
                (strain_id, data_id),
            ),
            mocker.call(
                "DELETE FROM CaseAttributeXRefNew WHERE "
                "StrainId = %s AND CaseAttributeId = "
                "(SELECT CaseAttributeId FROM "
                "CaseAttribute WHERE Name = %s) "
                "AND InbredSetId = %s",
                (strain_id, "Color", inbredset_id),
            ),
            mocker.call(
                "DELETE FROM CaseAttributeXRefNew WHERE "
                "StrainId = %s AND CaseAttributeId = %s "
                "AND InbredSetId = %s",
                (strain_id, "17", inbredset_id),
            ),
        ]
        cursor.execute.assert_has_calls(calls, any_order=False)


@pytest.mark.unit_test
def test_extract_actions():
    """Test that extracting the correct dict of 'actions' work properly"""
    assert __extract_actions(
        original_data="BXD1,18,x,0,x",
        updated_data="BXD1,x,2,1,F",
        csv_header="Strain Name,Value,SE,Count,Sex",
    ) == {
        "delete": {"data": "BXD1,18", "csv_header": "Strain Name,Value"},
        "insert": {"data": "BXD1,2,F", "csv_header": "Strain Name,SE,Sex"},
        "update": {"data": "BXD1,1", "csv_header": "Strain Name,Count"},
    }
    assert __extract_actions(
        original_data="BXD1,18,x,0,x",
        updated_data="BXD1,19,2,1,F",
        csv_header="Strain Name,Value,SE,Count,Sex",
    ) == {
        "delete": None,
        "insert": {"data": "BXD1,2,F", "csv_header": "Strain Name,SE,Sex"},
        "update": {
            "data": "BXD1,19,1",
            "csv_header": "Strain Name,Value,Count",
        },
    }


@pytest.mark.unit_test
def test_update_sample_data(mocker):
    """Test that updates work properly"""
    mock_conn = mocker.MagicMock()
    strain_id, data_id, inbredset_id = 1, 17373, 20
    with mock_conn.cursor() as cursor:
        mocker.patch(
            "gn3.db.sample_data.get_sample_data_ids",
            return_value=(strain_id, data_id, inbredset_id),
        )
        mocker.patch("gn3.db.sample_data.insert_sample_data", return_value=1)
        mocker.patch("gn3.db.sample_data.delete_sample_data", return_value=1)
        update_sample_data(
            conn=mock_conn,
            trait_name=35,
            original_data="BXD1,18,x,0,x,M,x,Red",
            updated_data="BXD1,x,2,1,2,F,2,Green",
            csv_header="Strain Name,Value,SE,Count,pH,Sex (13),Age,Color",
            phenotype_id=10007,
        )
        # pylint: disable=[E1101]
        gn3.db.sample_data.insert_sample_data.assert_called_once_with(
            conn=mock_conn,
            trait_name=35,
            data="BXD1,2,2,2",
            csv_header="Strain Name,SE,pH,Age",
            phenotype_id=10007,
        )

        # pylint: disable=[E1101]
        gn3.db.sample_data.delete_sample_data.assert_called_once_with(
            conn=mock_conn,
            trait_name=35,
            data="BXD1,18",
            csv_header="Strain Name,Value",
            phenotype_id=10007,
        )

        cursor.execute.assert_has_calls(
            [
                mocker.call(
                    "UPDATE NStrain SET count = %s "
                    "WHERE StrainId = %s AND DataId = %s",
                    ("1", strain_id, data_id),
                ),
                mocker.call(
                    "UPDATE CaseAttributeXRefNew SET Value = %s "
                    "WHERE StrainId = %s AND CaseAttributeId = %s AND "
                    "InbredSetId = %s",
                    ("F", strain_id, "13", inbredset_id),
                ),
                mocker.call(
                    "UPDATE CaseAttributeXRefNew SET Value = %s "
                    "WHERE StrainId = %s AND CaseAttributeId = "
                    "(SELECT CaseAttributeId FROM "
                    "CaseAttribute WHERE Name = %s) "
                    "AND InbredSetId = %s",
                    ("Green", strain_id, "Color", inbredset_id),
                ),
            ],
            any_order=False,
        )
