import pytest

from pymongo.collection import ObjectId

from saana_lib.score import MinimizedScore, PrioritizedScore, \
    IngredientScore, NutrientScore
from tests.conftest import obj_id


class TestCaseRecipeMinimizeScore:

    def test_worsen_ingredients_called_only_once(self, mocker):
        worsen = mocker.patch(
            'saana_lib.patient.SymptomsProgress.worsen',
            new_callable=mocker.PropertyMock,
            return_value=list()
        )
        klass = MinimizedScore(obj_id(), obj_id())
        for i in range(3):
            _ = klass.worsen_ingredients
        worsen.assert_called_once_with()

    def test_one_minimize_ingredients_in_recipe(self, mocker):
        m = mocker.patch(
            'saana_lib.recipe.Recipe.ingredients_id_quantity',
            new_callable=mocker.PropertyMock,
            return_value={'a3dw': 20, 'o93f': 3}
        )
        minimize_all = mocker.patch(
            'saana_lib.recommendation.MinimizeIngredients.all',
            new_callable=mocker.PropertyMock,
            return_value={'t5bv': {'min1': 0, 'min2': 2}, 'o93f': 2},
        )

        res = list(MinimizedScore(obj_id(), obj_id()).ingredient_set)
        assert res == [('o93f', 3, 2)]
        assert m.call_count == 1
        minimize_all.assert_called_once_with()

    def test_ingredient_score_value(self, mocker):
        sorted_symptoms = mocker.patch(
            'saana_lib.patient.SymptomsProgress.worsen',
            new_callable=mocker.PropertyMock,
            return_value={'t5bv': [1, 2], 'a3dw': [7, 3]}
        )

        worsen_ingredients = MinimizedScore(obj_id(), obj_id()).worsen_ingredients
        assert len(worsen_ingredients) == 2
        assert 't5bv' in worsen_ingredients
        sorted_symptoms.assert_called_once_with()


class TestCasePrioritizeScore:
    klass = PrioritizedScore(obj_id(), obj_id())

    def test_ingredient_set(self, mocker):
        m = mocker.patch(
            'saana_lib.recipe.Recipe.ingredients_name_quantity',
            new_callable=mocker.PropertyMock,
        )
        _all = mocker.patch(
            'saana_lib.recommendation.PrioritizeIngredients.all',
            new_callable=mocker.PropertyMock,
        )
        _ = list(self.klass.ingredient_set)

        _all.assert_called_once_with()
        m.assert_called_once_with()

    def test_prioritize_score_value(self, mocker):
        mocker.patch(
            'saana_lib.recipe.Recipe.ingredients_name_quantity',
            new_callable=mocker.PropertyMock,
            return_value={'dill': 20, 'flax': 3}
        )
        mocker.patch(
            'saana_lib.recommendation.PrioritizeIngredients.all',
            new_callable=mocker.PropertyMock,
            return_value={'wrap': 3, 'dill': 2},
        )

        assert self.klass.value == 10


class TestCaseNutrientScore:
    klass = NutrientScore(obj_id(), obj_id())

    def test_nutrient_set(self, mocker):
        _all = mocker.patch(
            'saana_lib.patient.Nutrients.all',
            new_callable=mocker.PropertyMock,
            return_value={'calcium': 120, 'selenium': 200, 'Glucose': 10}
        )
        nutrients = mocker.patch(
            'saana_lib.recipe.Recipe.nutrients',
            new_callable=mocker.PropertyMock,
            return_value={'selenium': {}, 'Glucose': {}}
        )
        assert len(self.klass.nutrient_set)
        _all.assert_called_once_with()
        nutrients.assert_called_once_with()

    @pytest.fixture
    def get_nutrient_facts_mock(self, mocker):
        return mocker.patch(
            'saana_lib.score.NutrientScore._get_nutrient_facts'
        )

    def test_calories_score_out_range(self, get_nutrient_facts_mock):
        get_nutrient_facts_mock.return_value = (200, {'lower': 100, 'upper': 180})
        assert self.klass.calories_score(obj_id()) == -20

    def test_calories_score_in_range(self, get_nutrient_facts_mock):
        get_nutrient_facts_mock.return_value = (120, {'lower': 100, 'upper': 150})
        assert self.klass.calories_score(obj_id()) == -10

    def test_calories_lt_threshold(self, get_nutrient_facts_mock):
        get_nutrient_facts_mock.return_value = (100, 200)
        assert self.klass.calories_score(obj_id()) == 10

    def test_calories_gt_threshold(self, get_nutrient_facts_mock):
        get_nutrient_facts_mock.return_value = (300, 200)
        assert self.klass.calories_score(obj_id()) == -10

    def test_add_calories_score(self, mocker):
        calories_score = mocker.patch('saana_lib.score.NutrientScore.calories_score')
        m = mocker.patch('saana_lib.score.db.mst_nutrients')
        m.find_one.return_value = obj_id()
        mocker.patch(
            'saana_lib.score.NutrientScore.nutrient_set',
            new_callable=mocker.PropertyMock,
            return_value=[obj_id()]
        )
        _ = self.klass.add_calories_score
        calories_score.assert_called_with(obj_id())


class TestCaseIngredientScore:

    def test_minimize_single_value_score(self):
        isc = IngredientScore(progress_ingredient=True)
        assert isc.single_value_score(12, 5) == -45.0

    def test_minimize_single_value_equals_ref(self):
        isc = IngredientScore(progress_ingredient=True)
        assert isc.single_value_score(12, 12) == 0

    def test_prioritize_single_value_equals_ref(self):
        isc = IngredientScore(progress_ingredient=False)
        assert isc.single_value_score(12, 11) == -30.0

    def test_quantity_in_lower_upper_range(self):
        isc = IngredientScore(progress_ingredient=False)
        assert isc.lower_upper_bound_score(20, {'min1': 2, 'min2': 21}) == -30

    def test_quantity_gr_upper_bound(self):
        isc = IngredientScore(progress_ingredient=True)
        assert isc.lower_upper_bound_score(22, {'min1': 2, 'min2': 21}) == -90




