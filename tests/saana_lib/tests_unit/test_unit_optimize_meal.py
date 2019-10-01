from unittest.mock import MagicMock
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
        assert optimizer.meals == dict()

    def test_meals_property_2(self, mocker):
        from tests.conftest import MEAL_DATA

        meal_infos = mocker.patch('saana_lib.connectMongo.db.meal_infos')
        meal_infos.find.return_value = [MEAL_DATA, ]
        assert len(optimizeMealSimple.Optimizer().meals) == 1
        assert meal_infos.find.called

    def test_meals_property_3(self, mocker):
        from tests.conftest import MEAL_DATA

        meal_infos = mocker.patch('saana_lib.connectMongo.db.meal_infos')
        meal_infos.find.return_value = [MEAL_DATA, ]

        get_ingredient_method = mocker.patch(
            'saana_lib.optimizeMealSimple.Optimizer.get_ingredient_name',
        )

        meals_dict = optimizeMealSimple.Optimizer().meals
        assert len(meals_dict) == 1
        assert get_ingredient_method.call_count == len(MEAL_DATA['ingredients'])

    def test_meals_property_4(self, mocker):
        """The ingredient is not found `return None`. Test that is not added
        to the meal list of ingredients
        """
        from tests.conftest import MEAL_DATA

        meal_infos = mocker.patch('saana_lib.connectMongo.db.meal_infos')
        meal_infos.find.return_value = [MEAL_DATA, ]

        get_ingredient_method = mocker.patch(
            'saana_lib.optimizeMealSimple.Optimizer.get_ingredient_name',
            return_value=None
        )
        meals_dict = optimizeMealSimple.Optimizer().meals
        assert len(meals_dict) == 1
        assert get_ingredient_method.call_count == len(MEAL_DATA['ingredients'])
        assert len(meals_dict[MEAL_DATA['_id']].ingredients) == 0


@pytest.fixture
def repeating_meals(mocker):
    m = mocker.patch(
        'saana_lib.optimizeMealSimple.Optimizer.repeating_meals',
        return_value=(list(), list())
    )
    return m


@pytest.mark.usefixtures("manual_input_patch", "repeating_meals")
class TestCaseGetScoreboard(object):

    def test_get_scoreboard_method_1(self, mocker, repeating_meals):
        """Base case: no meals"""
        mocker.patch(
            'saana_lib.optimizeMealSimple.Optimizer.meals',
            return_value=dict
        )
        optimizer = optimizeMealSimple.Optimizer()
        assert optimizer.get_score_board(MagicMock(_id=1), {}, [], {}) == dict()
        assert repeating_meals.call_count == 1

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
        assert optimizer.get_score_board(MagicMock(_id=1), {}, [], {}) == dict()

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
        }]} == optimizer.get_score_board(MagicMock(_id=1), {}, ['basil',], {})

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
        }]} == optimizer.get_score_board(MagicMock(_id=1), {
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
        }]} == optimizer.get_score_board(MagicMock(_id=1), {
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
        }]} == optimizer.get_score_board(MagicMock(_id=1), {
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
        }]} == optimizer.get_score_board(MagicMock(_id=1), {
            "sodium": {
                "min1": "800",
                "min2": "1000"
            }}, [], {})

    def test_get_scoreboard_method_8(self, monkeypatch):
        """minimize element is not of type dict"""
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
        }]} == optimizer.get_score_board(MagicMock(_id=1), {
            "sodium": 0}, [], {})

    def test_get_scoreboard_method_9(self, monkeypatch):
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
        }]}, optimizer.get_score_board(
            MagicMock(_id=1), {}, [], {
                "garlic": 2,
                "mushroom": 1,
            })
        )

    def test_get_scoreboard_method_10(self, monkeypatch):
        """prioritize nutrients"""
        meal_obj = model.Meal(
            _id='meal-id',
            name='creamy celeriac soup',
            ingredients={"soy": 3},
            nutrition={"potassium": "1020.13 mg"}
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
            optimizer.get_score_board(MagicMock(_id=1), {}, [], {
                "soy": 0,
                "turmeric": 0,
                "potassium": 10,
            },)
        )

    def test_get_scoreboard_method_11(self, monkeypatch):
        """prioritize nutrients"""
        meal_obj = model.Meal(
            _id='meal-id',
            name='creamy celeriac soup',
            ingredients={"soy": 3},
            nutrition={'cals': 500}
        )
        monkeypatch.setattr(
            optimizeMealSimple.Optimizer,
            'meals',
            [meal_obj,]
        )
        optimizer = optimizeMealSimple.Optimizer()
        expected = {120: [{
            'meal': meal_obj,
            'prior': ['soy'],
            'minimize': [],
            'avoid': []
        }]}
        assert_equal_objects(
            expected,
            optimizer.get_score_board(MagicMock(_id=1), {}, [], {
                'high calorie content': 500.0,
                'soy': 0
            },)
        )

    def test_get_scoreboard_method_12(self, mocker, repeating_meals):
        """meal is in repeat_one_week meals"""
        meal = MagicMock()
        meal.name = 'creamy celeriac soup'
        meal._id = 'id'
        meal.ingredients = {"soy": 3}
        meal.nutrition = {'cals': 500}
        repeating_meals.return_value = [meal], list()

        meals_mock = mocker.patch(
            'saana_lib.optimizeMealSimple.Optimizer.meals',
            new_callable=mocker.PropertyMock
        )
        meals_mock.return_value = [meal]

        optimizer = optimizeMealSimple.Optimizer()
        expected = {90: [{
            'meal': meal,
            'prior': ['soy'],
            'minimize': [],
            'avoid': []
        }]}
        assert_equal_objects(
            expected,
            optimizer.get_score_board(MagicMock(_id=1), {}, [], {
                'high calorie content': 500.0,
                'soy': 0
            },)
        )

    def test_get_scoreboard_method_13(self, mocker, repeating_meals):
        """meal is in repeat_two_week meals"""
        meal = MagicMock()
        meal.name = 'creamy celeriac soup'
        meal._id = 'id'
        meal.ingredients = {"soy": 3}
        meal.nutrition = {'cals': 500}
        repeating_meals.return_value = list(), [meal,]

        meals_mock = mocker.patch(
            'saana_lib.optimizeMealSimple.Optimizer.meals',
            new_callable=mocker.PropertyMock
        )
        meals_mock.return_value = [meal]
        optimizer = optimizeMealSimple.Optimizer()
        expected = {105: [{
            'meal': meal,
            'prior': ['soy'],
            'minimize': [],
            'avoid': []
        }]}
        assert_equal_objects(
            expected,
            optimizer.get_score_board(MagicMock(_id=1), {}, [], {
                'high calorie content': 500.0,
                'soy': 0
            },)
        )

    def test_adjust_score_according_to_calories_1(self):
        optimizer = optimizeMealSimple.Optimizer()
        assert optimizer.adjust_score_according_to_calories(670, 500.0) == 10

    def test_adjust_score_according_to_calories_2(self):
        optimizer = optimizeMealSimple.Optimizer()
        assert optimizer.adjust_score_according_to_calories(100, 500.0) == -10

    def test_adjust_score_according_to_calories_3(self):
        optimizer = optimizeMealSimple.Optimizer()
        assert optimizer.adjust_score_according_to_calories(450, '400|700') == 10

    def test_patient_has_active_subscription_1(self, mocker):
        m1 = mocker.patch(
            'saana_lib.connectMongo.db.patient_subscriptions',
        )
        m1.find_one.return_value = None
        assert not optimizeMealSimple.Optimizer(test=False).patient_has_active_subscription('id')

    def test_patient_has_active_subscription_2(self, mocker):
        m1 = mocker.patch(
            'saana_lib.connectMongo.db.patient_subscriptions',
        )
        m1.find_one.return_value = {'status': 'inactive'}
        assert not optimizeMealSimple.Optimizer(test=False).patient_has_active_subscription('id')

    def test_patient_has_active_subscription_3(self, mocker):
        m1 = mocker.patch(
            'saana_lib.connectMongo.db.patient_subscriptions',
        )
        m1.find_one.return_value = {'status': 'active', 'subscription_id': 1}

        m2 = mocker.patch(
            'saana_lib.connectMongo.db.mst_subscriptions',
        )
        m2.find_one.return_value = {'interval_count': 1}
        m3 = mocker.patch(
            'saana_lib.connectMongo.db.orders',
        )
        m3.find_one.return_value = 1
        assert optimizeMealSimple.Optimizer(test=False).patient_has_active_subscription('id')
        assert m1.find_one.called
        assert m2.find_one.called
        assert not m3.called

    def test_patient_has_active_subscription_4(self, mocker):
        m1 = mocker.patch(
            'saana_lib.connectMongo.db.patient_subscriptions',
        )
        m1.find_one.return_value = {'status': 'active', 'subscription_id': 1}
        m2 = mocker.patch(
            'saana_lib.connectMongo.db.mst_subscriptions',
        )
        m2.find_one.return_value = {'interval_count': 2}
        m3 = mocker.patch(
            'saana_lib.connectMongo.db.orders',
        )
        m3.find_one.return_value = 1
        assert not optimizeMealSimple.Optimizer(test=False).patient_has_active_subscription('id')
        assert m2.find_one.called
        assert m3.find_one.called


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



