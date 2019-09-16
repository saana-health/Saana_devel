from saana_lib import optimizeMealSimple, manual_input
import pytest


@pytest.mark.usefixtures("manual_input_patch")
class TestCaseOptimezer(object):

    def test_patients_property_1(self, empty_patients):
        """Empty patients collections"""

        optimizer = optimizeMealSimple.Optimizer()
        assert optimizer.patients == list()

    def test_patients_property_2(self, patients):
        """No email list is provided, so the only Patient in the DB
        gets returned
        """
        optimizer = optimizeMealSimple.Optimizer()
        assert len(optimizer.patients) == 1

    def test_patients_property_3(self, patients):
        """A user is provided in the supplier file, but differs from
        the patient in the DB
        """
        def patients_emails(f):
            return list(), ['other@saana.co',]

        patients.setattr(
            'saana_lib.optimizeMealSimple.manual_input',
            patients_emails
        )

        optimizer = optimizeMealSimple.Optimizer()
        assert optimizer.patients == list()

    def test_patients_property_4(self, patients, default_user):
        """Verify that the returned Patient is the same one given
        in the supplier.csv file
        """
        def patients_emails(f):
            return list(), [default_user['email'],]

        patients.setattr(
            'saana_lib.optimizeMealSimple.manual_input',
            patients_emails
        )

        optimizer = optimizeMealSimple.Optimizer()
        assert optimizer.patients[0].name == default_user['first_name']

    def test_meals_property_1(self, empty_meals):
        optimizer = optimizeMealSimple.Optimizer()
        assert optimizer.meals == list()

    def test_meals_property_2(self, meals_patch):
        from tests.conftest import MEAL_DATA

        meals_patch.setitem(MEAL_DATA, 'ingredients', [])
        optimizer = optimizeMealSimple.Optimizer()
        assert len(optimizer.meals) == 1

    def test_meals_property_3(self, meals_patch):
        from tests.conftest import MEAL_DATA

        def method_mock(a, b):
            return b.binary

        meals_patch.setattr(
            optimizeMealSimple.Optimizer,
            'get_ingredient_name',
            method_mock
        )

        optimizer = optimizeMealSimple.Optimizer()
        meals_list = optimizer.meals
        assert len(meals_list) == 1
        assert len(meals_list[0].ingredients) == len(MEAL_DATA['ingredients'])

    def test_meals_property_4(self, manual_input_patch):
        """The ingredient is not found `return None`. Test that is not added
        to the meal list of ingredients
        """
        from saana_lib import connectMongo
        from tests import conftest

        class StubClass:
            def find_one(self, *args, **kwargs):
                return None

        manual_input_patch.setattr(connectMongo, 'db', conftest.get_mongo_stub(
            meal_infos=conftest.MealsCollectionMock,
            mst_food_ingredients=StubClass
        ))

        optimizer = optimizeMealSimple.Optimizer()
        meals_list = optimizer.meals
        assert len(meals_list) == 1
        assert len(meals_list[0].ingredients) == 0

    def test_get_scoreboard_method_1(self, manual_input_patch):
        """Base case: no meals"""
        manual_input_patch.setattr(
            optimizeMealSimple.Optimizer,
            'meals',
            list()
        )
        optimizer = optimizeMealSimple.Optimizer()
        assert optimizer.get_score_board(None, {}, [], {}) == dict()

    def test_get_scoreboard_method_2(self, monkeypatch):
        """Base case: Meal's supplier != to the one manually provided
        with the supplier's file
        """
        from saana_lib.model import Meal

        def manual_input_stub(a):
            return ['s-2', ], list()

        monkeypatch.setattr(
            'saana_lib.optimizeMealSimple.manual_input',
            manual_input_stub
        )

        meal_obj = Meal(_id='meal-id', supplierID='s-1')
        monkeypatch.setattr(
            optimizeMealSimple.Optimizer,
            'meals',
            [meal_obj,]
        )
        optimizer = optimizeMealSimple.Optimizer()
        assert optimizer.get_score_board(None, {}, [], {}) == dict()

    def test_get_scoreboard_method_3(self, monkeypatch):
        from saana_lib.model import Meal

        meal_obj = Meal(_id='meal-id', ingredients={'basil': '20'})
        monkeypatch.setattr(
            optimizeMealSimple.Optimizer,
            'meals',
            [meal_obj,]
        )
        optimizer = optimizeMealSimple.Optimizer()
        assert {40: [{
            'meal': meal_obj,
            'prior': [],
            'minimize': [],
            'avoid': ['basil',]
        }]} == optimizer.get_score_board(None, {}, ['basil',], {})




