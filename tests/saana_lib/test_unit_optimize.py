import pytest

from saana_lib import optimizeMealSimple, model
from tests.conftest import assert_equal_objects
from constants import constants_wrapper as constants


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


@pytest.mark.usefixtures("manual_input_patch")
class TestCaseGetScoreboard(object):

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
        def manual_input_stub(a):
            return ['s-2', ], list()

        monkeypatch.setattr(
            'saana_lib.optimizeMealSimple.manual_input',
            manual_input_stub
        )

        meal_obj = model.Meal(_id='meal-id', supplierID='s-1')
        monkeypatch.setattr(
            optimizeMealSimple.Optimizer,
            'meals',
            [meal_obj,]
        )
        optimizer = optimizeMealSimple.Optimizer()
        assert optimizer.get_score_board(None, {}, [], {}) == dict()

    def test_get_scoreboard_method_3(self, monkeypatch):

        meal_obj = model.Meal(_id='meal-id', ingredients={'basil': '20'})
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

    def test_get_scoreboard_method_4(self, monkeypatch):
        """
        quantity is in between min1 and min2
        """
        meal_obj = model.Meal(
            _id='meal-id',
            ingredients={
                "sodium": "864.24 mg",
                "vitamin k": "76.45 mcg"
            }
        )
        monkeypatch.setattr(
            optimizeMealSimple.Optimizer,
            'meals',
            [meal_obj,]
        )
        optimizer = optimizeMealSimple.Optimizer()
        assert {70: [{
            'meal': meal_obj,
            'prior': [],
            'minimize': ['sodium', ],
            'avoid': []
        }]} == optimizer.get_score_board(None, {
            "sodium": {
                "min1": "800",
                "min2": "1000"
            }}, [], {})

    def test_get_scoreboard_method_5(self, monkeypatch):
        """
        quantity is greater than minimum2
        """
        meal_obj = model.Meal(
            _id='meal-id',
            ingredients={
                "sodium": "1164.24 mg",
                "vitamin k": "76.45 mcg"
            }
        )
        monkeypatch.setattr(
            optimizeMealSimple.Optimizer,
            'meals',
            [meal_obj,]
        )
        optimizer = optimizeMealSimple.Optimizer()
        assert {40: [{
            'meal': meal_obj,
            'prior': [],
            'minimize': ['sodium', ],
            'avoid': []
        }]} == optimizer.get_score_board(None, {
            "sodium": {
                "min1": "800",
                "min2": "1000"
            }}, [], {})

    def test_get_scoreboard_method_6(self, monkeypatch):
        """
        quantity is less than minimum1
        """
        meal_obj = model.Meal(
            _id='meal-id',
            ingredients={
                "sodium": "564.24 mg",
                "vitamin k": "76.45 mcg"
            }
        )
        monkeypatch.setattr(
            optimizeMealSimple.Optimizer,
            'meals',
            [meal_obj,]
        )
        optimizer = optimizeMealSimple.Optimizer()
        assert {100: [{
            'meal': meal_obj,
            'prior': [],
            'minimize': [],
            'avoid': []
        }]} == optimizer.get_score_board(None, {
            "sodium": {
                "min1": "800",
                "min2": "1000"
            }}, [], {})

    def test_get_scoreboard_method_7(self, monkeypatch):
        """quantity is less than minimum1"""
        meal_obj = model.Meal(
            _id='meal-id',
            ingredients={
                "sodium": "564.24 mg",
                "vitamin k": "76.45 mcg"
            }
        )
        monkeypatch.setattr(
            optimizeMealSimple.Optimizer,
            'meals',
            [meal_obj,]
        )
        optimizer = optimizeMealSimple.Optimizer()
        assert {100: [{
            'meal': meal_obj,
            'prior': [],
            'minimize': [],
            'avoid': []
        }]} == optimizer.get_score_board(None, {
            "sodium": {
                "min1": "800",
                "min2": "1000"
            }}, [], {})

    def test_get_scoreboard_method_8(self, monkeypatch):
        """prioritize ingredients"""
        meal_obj = model.Meal(
            _id='meal-id',
            ingredients={
                "garlic": 3,
                "mushroom": 2,
                "mackerel": 0,
            }
        )
        monkeypatch.setattr(
            optimizeMealSimple.Optimizer,
            'meals',
            [meal_obj,]
        )
        optimizer = optimizeMealSimple.Optimizer()
        assert_equal_objects({120: [{
            'meal': meal_obj,
            'prior': ['garlic', 'mushroom'],
            'minimize': [],
            'avoid': []
        }]}, optimizer.get_score_board(None, {}, [], {
                "garlic": 2,
                "mushroom": 1,
            })
        )

    def test_get_scoreboard_method_9(self, monkeypatch):
        """prioritize nutrients"""
        meal_obj = model.Meal(
            _id='meal-id',
            name='creamy celeriac soup',
            ingredients={
                "soy": 3,
            },
            nutrition={
                "potassium": "1020.13 mg"
            }
        )
        monkeypatch.setattr(
            optimizeMealSimple.Optimizer,
            'meals',
            [meal_obj,]
        )
        optimizer = optimizeMealSimple.Optimizer()
        expected = {120: [{
            'meal': meal_obj,
            'prior': ['potassium', 'soy'],
            'minimize': [],
            'avoid': []
        }]}
        assert_equal_objects(
            expected,
            optimizer.get_score_board(None, {}, [], {
                "soy": 0,
                "turmeric": 0,
                "potassium": 10,
            },)
        )


@pytest.mark.usefixtures("scoreboard_base_patch")
class TestCaseScoreboardToCsv(object):
    base_headers = ['abf3ed', 'score', 'meal', 'minimize', 'prior', 'avoid', 'supplier_id', 'supplier_name']

    @property
    def meal_obj(self):
        return model.Meal(
            _id='meal-id',
            name='creamy celeriac soup',
            ingredients={
                "soy": 3,
            },
            nutrition={
                "potassium": "1020.13 mg"
            },
            supplierID='3b7750fa415d304'
        )

    def test_scoreboard_to_csv_rows_1(self, patients):
        """empty scoreboard, """
        optimizer = optimizeMealSimple.Optimizer()
        assert ('Admin.TestUser', [self.base_headers, ]) == optimizer.scoreboard_to_csv_rows({}, 'abf3ed')

    def test_scoreboard_to_csv_rows_2(self, patients):
        """scoreboard with one meal"""
        optimizer = optimizeMealSimple.Optimizer()
        row = [120, 'creamy celeriac soup', '', 'potassium:soy', '', '3b7750fa415d304', 'Admin']
        assert ('Admin.TestUser', [self.base_headers, row]) == optimizer.scoreboard_to_csv_rows({
            120: [{
                'meal': self.meal_obj,
                'prior': ['potassium', 'soy'],
                'minimize': [],
                'avoid': []
            }]
        }, 'abf3ed')



