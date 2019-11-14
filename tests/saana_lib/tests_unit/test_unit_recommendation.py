from datetime import timedelta, datetime

import pytest

from tests.conftest import assert_equal_objects, obj_id
from saana_lib.recommendation import MinimizeRecommendation, \
    AvoidRecommendation, PrioritizeRecommendation, RecipeRecommendation

patient_id = obj_id
recipe_id = obj_id


@pytest.fixture
def tags_find_patch(mocker):
    tags_mock = mocker.patch(
        'saana_lib.connectMongo.db.tags'
    )
    tags_mock.find.return_value = [{
        '_id': 'b09779e',
        'minimize': {},
        'name': 'hypertension',
        'avoid': [],
        'prior': {},
        'type': 'comorbitities',
        },{
        '_id': '5cab57647',
        'minimize': {},
        'name': 'dry mouth',
        'avoid': [],
        'prior': {},
        'type': 'symptoms',
    }]
    return tags_mock


@pytest.fixture
def recommendation_save_mock(mocker):
    met = mocker.patch('saana_lib.recommendation.Recommendation.save')
    return met


@pytest.mark.usefixtures("datetime_mock")
class TestCaseRecommendation(object):
    """
    The method being called in the first two tests is the same,
    so tests are meant to cover two different aspects (not to
    be repetitive)
    """

    def test_minimize_recommendation(self, mocker):
        """Verify that the proper recommendation class is used
        (in this case MinimizeIngredients)
        """
        all_prop = mocker.patch(
            'saana_lib.recommendation.MinimizeIngredients.all',
            new_callable=mocker.PropertyMock,
            return_value={"onion": 0, "flax": 2}
        )
        _ = MinimizeRecommendation(patient_id()).as_list()
        all_prop.assert_called_once_with()

    def test_prioritize_recommendation(self, mocker):
        """Verify the content of the list being returned"""
        mocker.patch(
            'saana_lib.recommendation.PrioritizeIngredients.all',
            new_callable=mocker.PropertyMock,
            return_value={"onion": 0, "flax": 2}
        )
        get_ingr_mock = mocker.patch(
            'saana_lib.recommendation.Recommendation.get_or_create_ingredient'
        )
        _ = PrioritizeRecommendation(patient_id()).as_list()

        assert_equal_objects(
            [arg[0][0] for arg in get_ingr_mock.call_args_list],
            ["onion", "flax"]
        )

    def test_avoid_recommendation_values(self, mocker, datetime_mock):
        """
        This test verifies both, that the correct property is called,
        and check the content values being returned
        """
        all_prop = mocker.patch(
            'saana_lib.patient.AvoidIngredients.all',
            new_callable=mocker.PropertyMock,
            return_value={"onion", "flax"}
        )
        get_ingr_mock = mocker.patch(
            'saana_lib.recommendation.Recommendation.get_or_create_ingredient'
        )
        _ = AvoidRecommendation(patient_id()).as_list()

        assert_equal_objects(
            [arg[0][0] for arg in get_ingr_mock.call_args_list],
            ["onion", "flax"]
        )
        all_prop.assert_called_once_with()
        assert datetime_mock.now.call_count == 4


class TestCaseRecipeRecommendation:
    klass = RecipeRecommendation(
        recipe=None,
        patient_id=patient_id(),
        recipe_id=recipe_id()
    )

    def test_recommendations_in_time_frame(self, mocker):
        m = mocker.patch(
            'saana_lib.recommendation.db.patient_recipe_recommendation',
        )
        start = datetime.now()
        end = start - timedelta(days=1)
        _ = self.klass.recommendations_in_time_frame(start, end)
        m.find.assert_called_once_with({
            'patient_id': obj_id(),
            'created_at': {'$lte': start, "$gte": end}},
            {'recipe_id': 1, '_id': 0}

        )

    def test_recommendations_in_time_frame_default_end(self, mocker):
        m = mocker.patch(
            'saana_lib.recommendation.db.patient_recipe_recommendation',
        )
        start = datetime.now()
        _ = self.klass.recommendations_in_time_frame(start)
        m.find.assert_called_once_with({
            'patient_id': obj_id(),
            'created_at': {'$lte': start, "$gte": start - timedelta(days=7)}},
            {'recipe_id': 1, '_id': 0}
        )

    def test_recommendations_in_time_frame_values(self, mocker):
        m = mocker.patch(
            'saana_lib.recommendation.db.patient_recipe_recommendation',
        )
        m.find.return_value=[{'recipe_id': obj_id()}]
        start = datetime.now()
        assert_equal_objects(
            self.klass.recommendations_in_time_frame(start),
            [obj_id()]
        )

    def test_repetition_deduct_gt_threshold(self):
        current = datetime.now()
        last_time = current - timedelta(days=21 + current.weekday() + 1)
        assert self.klass.repetition_deduct_points(last_time) == 0

    def test_repetition_deduct_points(self):
        current = datetime.now()
        last_time = current - timedelta(days=14)
        assert self.klass.repetition_deduct_points(last_time) == 20


