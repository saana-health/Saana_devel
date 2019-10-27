import pytest

from pymongo.collection import ObjectId

from tests.conftest import assert_equal_objects
from saana_lib.ingredient_recommendation import Recommendation,\
    MinimizeRecommendation, AvoidRecommendation, PrioritizeRecommendation


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
    met = mocker.patch('saana_lib.ingredient_recommendation.Recommendation.save')
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
            'saana_lib.ingredient_recommendation.MinimizeIngredients.all',
            new_callable=mocker.PropertyMock,
            return_value={"onion": 0, "flax": 2}
        )
        _ = MinimizeRecommendation('5cab584074e88f0cb0977a08').as_list()
        all_prop.assert_called_once_with()

    def test_prioritize_recommendation(self, mocker):
        """Verify the content of the list being returned"""
        mocker.patch(
            'saana_lib.ingredient_recommendation.PrioritizeIngredients.all',
            new_callable=mocker.PropertyMock,
            return_value={"onion": 0, "flax": 2}
        )
        get_ingr_mock = mocker.patch(
            'saana_lib.ingredient_recommendation.Recommendation.get_or_create_ingredient'
        )
        _ = PrioritizeRecommendation('5cab584074e88f0cb0977a08').as_list()

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
            'saana_lib.ingredient_recommendation.Recommendation.get_or_create_ingredient'
        )
        _ = AvoidRecommendation('5cab584074e88f0cb0977a08').as_list()

        assert_equal_objects(
            [arg[0][0] for arg in get_ingr_mock.call_args_list],
            ["onion", "flax"]
        )
        all_prop.assert_called_once_with()
        assert datetime_mock.now.call_count == 4


@pytest.mark.skip('')
@pytest.mark.usefixtures("datetime_mock", "recommendation_save_mock")
class TestCaseIngredientAdviceMethod:

    @pytest.fixture
    def other_restrictions_mock(self, mocker):
        m = mocker.patch(
            'saana_lib.ingredient_recommendation.Recommendation.other_restrictions',
            return_value=['green pepper']
        )
        return m

    def test_ingredients_advice_1(self, tags_mock, patient_inputs_mock):
        """assert on method/property calls. Execution does not
        enters the loop
        """
        patient_inputs_mock.return_value = list()

        _ = Recommendation().ingredients_advice('5cabf2ad37c87f3ac00e8701')
        patient_inputs_mock.assert_called_once_with(ObjectId('5cabf2ad37c87f3ac00e8701'))
        assert len(tags_mock.mock_calls) == 0

    def test_ingredients_advice_2(self,
                                  tags_mock,
                                  patient_inputs_mock):
        """assert on method/property calls. One loop iteration
        is performed
        """
        tags_mock.return_value = dict()
        patient_inputs_mock.return_value = [1]
        _ = Recommendation().ingredients_advice('5cabf2ad37c87f3ac00e8701')

        patient_inputs_mock.assert_called_once_with(ObjectId('5cabf2ad37c87f3ac00e8701'))
        assert len(tags_mock.mock_calls) == 1

    def test_ingredients_advice_3(self,
                                  tags_mock,
                                  patient_inputs_mock,
                                  recommendation_save_mock):
        """assert on result"""
        tags_mock.return_value = {'hypertension': {
            'minimize': {'sodium': {}},
            'name': 'hypertension',
            'avoid': ['beets'],
            'prioritize': {'carrot': 0}
        }}

        _ = Recommendation().ingredients_advice('5cabf2ad37c87f3ac00e8701')
        call_args = recommendation_save_mock.call_args[0][0]
        assert_equal_objects(call_args, {
                'is_like': True,
                'created_at': '2019-05-18T15:17:08.132263',
                'minimize': ['sodium'],
                'avoid': ['beets'],
                'prioritize': ['carrot'],
                'patient_id': '5cabf2ad37c87f3ac00e8701',
                'recipe_id': None,
                'ingredient_id': None,
                'type': 'ingredient'
            }
        )
        assert recommendation_save_mock.call_count == 1

    def test_ingredients_advice_4(self,
                                  tags_mock,
                                  patient_inputs_mock,
                                  other_restrictions_mock,
                                  recommendation_save_mock):
        """assert on result"""
        tags_mock.return_value = {'hypertension': {
            'minimize': {'sodium': {}},
            'name': 'hypertension',
            'avoid': ['beets'],
            'prioritize': {'carrot': 0}
        }}

        _ = Recommendation().ingredients_advice('5cabf2ad37c87f3ac00e8701')
        call_args = recommendation_save_mock.call_args[0][0]
        assert_equal_objects(call_args, {
                'is_like': True,
                'created_at': '2019-05-18T15:17:08.132263',
                'minimize': ['sodium'],
                'avoid': ['beets', 'green pepper'],
                'prioritize': ['carrot'],
                'patient_id': '5cabf2ad37c87f3ac00e8701',
                'recipe_id': None,
                'ingredient_id': None,
                'type': 'ingredient'
            }
        )

    def test_ingredients_advice_5(self,
                                  tags_mock,
                                  patient_inputs_mock,
                                  recommendation_save_mock):
        """assert on result"""
        tags_mock.return_value = {'hypertension': {
            'minimize': {'sodium': {}},
            'name': 'hypertension',
            'avoid': ['beets', 'green pepper'],
            'prioritize': {'carrot': 0, 'pepper': 1}
        }}
        _ = Recommendation().ingredients_advice('5cabf2ad37c87f3ac00e8701')
        call_args = recommendation_save_mock.call_args[0][0]
        assert_equal_objects(call_args, {
                'is_like': True,
                'created_at': '2019-05-18T15:17:08.132263',
                'minimize': ['sodium'],
                'avoid': ['beets', 'green pepper'],
                'prioritize': ['carrot'],
                'patient_id': '5cabf2ad37c87f3ac00e8701',
                'recipe_id': None,
                'ingredient_id': None,
                'type': 'ingredient'
            }
        )

    def test_ingredients_advice_6(self,
                                  tags_mock,
                                  patient_inputs_mock,
                                  other_restrictions_mock,
                                  recommendation_save_mock):
        """assert on result"""
        tags_mock.return_value = {'hypertension': {
            'minimize': {'sodium': {}, 'soy': {}},
            'name': 'hypertension',
            'avoid': ['beets', 'green pepper'],
            'prioritize': {'carrot': 0, 'pepper': 1}
        }}
        other_restrictions_mock.return_value = ['green pepper', 'soy']
        _ = Recommendation().ingredients_advice('5cabf2ad37c87f3ac00e8701')
        call_args = recommendation_save_mock.call_args[0][0]
        assert_equal_objects(call_args, {
                'is_like': True,
                'created_at': '2019-05-18T15:17:08.132263',
                'minimize': ['sodium'],
                'avoid': ['beets', 'green pepper', 'soy'],
                'prioritize': ['carrot'],
                'patient_id': '5cabf2ad37c87f3ac00e8701',
                'recipe_id': None,
                'ingredient_id': None,
                'type': 'ingredient'
            }
        )
