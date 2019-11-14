from datetime import datetime

import pytest

from tests.conftest import obj_id
from saana_lib.chemo import Chemo


@pytest.fixture
def datetime_mock(mocker):
    mock = mocker.patch('saana_lib.chemo.datetime')
    return mock


patient_id = obj_id


@pytest.mark.usefixtures("scoreboard_base_patch")
class TestCaseChemo:
    klass = Chemo(patient_id())

    def test_chemo_dates_when_is_tuesday(self, datetime_mock):
        datetime_mock.now.return_value = datetime(2019, 10, 15)
        assert self.klass.next_tuesday == datetime(2019, 10, 15)

    def test_chemo_dates_when_is_thursday(self, datetime_mock):
        datetime_mock.now.return_value = datetime(2019, 10, 17)
        assert self.klass.next_tuesday == datetime(2019, 10, 22)

    def test_recipes_when_no_treatment(self, mocker):
        mocker.patch(
            'saana_lib.chemo.Chemo._treatment_dates_ahead',
            new_callable=mocker.PropertyMock,
            return_value=list()
        )
        assert self.klass.recipes({}, [1, 2]) == [1, 2]

    def test_recipe_from_slots(self, mocker):
        mocker.patch(
            'saana_lib.chemo.Chemo._treatment_dates_ahead',
            new_callable=mocker.PropertyMock,
            return_value=True
        )
        scoreboard = mocker.MagicMock(spec=dict)
        fake_recipe = mocker.patch('saana_lib.recipe.Recipe')
        fake_recipe.name = 'vegan soup'
        recipes_list = mocker.MagicMock(spec=list)

        scoreboard.__iter__.side_effect = {100: recipes_list}.__iter__

        slots = [fake_recipe, fake_recipe, fake_recipe]

        _ = self.klass.recipes(scoreboard, slots)
        assert len(scoreboard.mock_calls) == 1
        assert tuple(scoreboard.mock_calls[0])[0] == '__iter__'
        assert len(recipes_list.mock_calls) == 0

    def test_recipes_from_slots_and_scoreboard(self, mocker):
        mocker.patch(
            'saana_lib.chemo.Chemo._treatment_dates_ahead',
            new_callable=mocker.PropertyMock,
            return_value=True
        )

        scoreboard = mocker.MagicMock(spec=dict)
        fake_recipe = mocker.patch('saana_lib.recipe.Recipe')
        fake_recipe.name = 'vegan soup'
        recipes_list = mocker.MagicMock(spec=list)

        scoreboard.__iter__.side_effect = {100: recipes_list}.__iter__
        slots = [fake_recipe, fake_recipe]

        _ = self.klass.recipes(scoreboard, slots)
        assert tuple(scoreboard.mock_calls[0])[0] == '__iter__'
        assert scoreboard.mock_calls[1] == ('__getitem__', (100, ), {})
        assert len(recipes_list.mock_calls) == 0
