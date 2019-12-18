import pytest

from exceptions import DatabaseConfException
from main import run
from tests.conftest import obj_id


def test_database_settings(monkeypatch):
    import conf
    monkeypatch.setattr(conf, 'DATABASE_USER', '')
    with pytest.raises(DatabaseConfException):
        run()


def tests_cmd_line_arguments(mocker):
    args_mock = mocker.MagicMock()
    args_mock.patient_id = obj_id()
    mocker.patch('argparse.ArgumentParser.parse_args', return_value=args_mock)
    rank_class = mocker.patch('main.RankingToDatabase')
    _ = run()
    rank_class.assert_called_once_with(patient_id=obj_id())
    assert tuple(rank_class.mock_calls[1])[0] == '().store'
