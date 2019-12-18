import pytest

from saana_lib.score import MinimizedScore, PrioritizedScore, \
    IngredientScore, NutrientScore, AvoidScore
from tests.conftest import obj_id


recipe_id = obj_id
patient_id = obj_id
nutrient_id = obj_id


class TestCaseRecipeMinimizeScore:

    def test_worsen_ingredients_called_only_once(self, mocker):
        worsen = mocker.patch(
            'saana_lib.patient.SymptomsProgress.worsen',
            new_callable=mocker.PropertyMock,
            return_value=list()
        )
        klass = MinimizedScore(recipe_id(), patient_id())
        for i in range(3):
            _ = klass.worsen_ingredients
        worsen.assert_called_once_with()

    def test_one_minimize_ingredient_in_recipe(self, mocker):
        minimize_all = mocker.patch(
            'saana_lib.recommendation.MinimizeIngredients.all',
            new_callable=mocker.PropertyMock,
            return_value={'seaweed': {'min1': 0, 'min2': 2}, 'fish': 2}
        )
        ingredients_id_quantity = mocker.patch(
            'saana_lib.recipe.Recipe.ingredients_name_quantity',
            new_callable=mocker.PropertyMock,
            return_value={'cabbage': 20, 'fish': 3}
        )

        res = list(MinimizedScore(obj_id(), obj_id()).ingredient_set)
        assert res == [('fish', 3, 2)]
        assert ingredients_id_quantity.call_count == 1
        minimize_all.assert_called_once_with()

    def test_ingredient_score_value(self, mocker):
        worsened_symptoms = mocker.patch(
            'saana_lib.patient.SymptomsProgress.worsen',
            new_callable=mocker.PropertyMock,
            return_value={'carrot': [1, 2], 'saury fish': [7, 3]}
        )

        worsen_ingredients = MinimizedScore(recipe_id(), patient_id()).worsen_ingredients
        assert len(worsen_ingredients) == 2
        assert 'carrot' in worsen_ingredients
        worsened_symptoms.assert_called_once_with()

    @pytest.fixture
    def worsen_symptom_ingredients(self, mocker):
        mocked_method = mocker.patch(
            'saana_lib.score.MinimizedScore.worsen_ingredients',
            new_callable=mocker.PropertyMock,
            return_value=list()
        )
        return mocked_method, mocker

    def test_minimize_score_value(self, worsen_symptom_ingredients):
        mocked_method, mocker = worsen_symptom_ingredients
        mocker.patch(
            'saana_lib.score.MinimizedScore.ingredient_set',
            new_callable=mocker.PropertyMock,
            return_value=[
                ('t5bv', 2, {'min1': 2, 'min2': 4}),
                ('a3dw', 30, 10)
            ]
        )
        assert MinimizedScore(recipe_id(), patient_id()).value == -60

    def test_score_element_of_worsened_symptom(self, worsen_symptom_ingredients):
        mocked_method, mocker = worsen_symptom_ingredients
        mocked_method.return_value = ['a3dw']
        mocker.patch(
            'saana_lib.score.MinimizedScore.ingredient_set',
            new_callable=mocker.PropertyMock,
            return_value=[
                ('t5bv', 1, {'min1': 2, 'min2': 4}),
                ('a3dw', 30, 10)
            ]
        )
        assert MinimizedScore(recipe_id(), patient_id()).value == -45


class TestCasePrioritizeScore:
    klass = PrioritizedScore(recipe_id(), patient_id())

    def test_prioritize_score_value(self, mocker):
        """This test implicitly assert that both mocks
        are being called
        """
        mocker.patch(
            'saana_lib.recommendation.PrioritizeIngredients.all',
            new_callable=mocker.PropertyMock,
            return_value={'zucchini': 3, 'seaweed': 12},
        )
        mocker.patch(
            'saana_lib.recipe.Recipe.ingredients_name_quantity',
            new_callable=mocker.PropertyMock,
            return_value={'seaweed': 13}
        )
        assert self.klass.value == 10


class TestCaseAvoidScore:
    klass = AvoidScore(recipe_id(), patient_id())

    def test_prioritize_score_value(self, mocker):
        """This test implicitly assert that both mocks
        are being called
        """
        mocker.patch(
            'saana_lib.recommendation.AvoidIngredients.all',
            new_callable=mocker.PropertyMock,
            return_value=['zucchini', 'seaweed'],
        )
        mocker.patch(
            'saana_lib.recipe.Recipe.ingredients_name_quantity',
            new_callable=mocker.PropertyMock,
            return_value={'seaweed': 13}
        )
        assert self.klass.value == -60


class TestCaseNutrientScore:
    klass = NutrientScore(recipe_id(), patient_id())

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
        assert self.klass.calories_score(nutrient_id()) == -20

    def test_calories_score_in_range(self, get_nutrient_facts_mock):
        get_nutrient_facts_mock.return_value = (120, {'lower': 100, 'upper': 150})
        assert self.klass.calories_score(nutrient_id()) == -10

    def test_calories_lt_threshold(self, get_nutrient_facts_mock):
        get_nutrient_facts_mock.return_value = (100, 200)
        assert self.klass.calories_score(nutrient_id()) == 10

    def test_calories_gt_threshold(self, get_nutrient_facts_mock):
        get_nutrient_facts_mock.return_value = (300, 200)
        assert self.klass.calories_score(nutrient_id()) == -10

    def test_add_calories_score(self, mocker):
        calories_score = mocker.patch(
            'saana_lib.score.NutrientScore.calories_score'
        )
        m = mocker.patch('saana_lib.score.db.mst_nutrients')
        m.find_one.return_value = nutrient_id()
        mocker.patch(
            'saana_lib.score.NutrientScore.nutrient_set',
            new_callable=mocker.PropertyMock,
            return_value=[nutrient_id()]
        )
        _ = self.klass.add_calories_score
        calories_score.assert_called_with(nutrient_id())


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




