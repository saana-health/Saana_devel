from unittest.mock import MagicMock
import pytest

from saana_lib import model
from saana_lib.scoreboard import Scoreboard, ScoreboardPatient, ScoreboardException, ScoreboardPatientException
from tests.conftest import assert_equal_objects, PATIENT_DATA


@pytest.mark.usefixtures("manual_input_mock")
class TestCaseScoreboardPatient(object):

    @property
    def default_patient(self):
        return ScoreboardPatient(PATIENT_DATA, testing_mode=False)

    @pytest.fixture
    def users_mock(self, mocker):
        return mocker.patch('saana_lib.connectMongo.db.users')

    @pytest.fixture
    def patients_mock(self, mocker):
        return mocker.patch('saana_lib.connectMongo.db.patients')

    def test_comorbities_property(self, mocker):
        mock = mocker.patch('saana_lib.connectMongo.db.patient_comorbidities')
        mock.find.return_value=list()
        _ = self.default_patient.comorbidities
        assert mock.find.call_count == 1

    def test_diseases_property(self, mocker):
        mock = mocker.patch('saana_lib.connectMongo.db.patient_diseases')
        mock.find.return_value=list()
        _ = self.default_patient.diseases
        assert mock.find.call_count == 1

    def test_symptoms_property(self, mocker):
        mock = mocker.patch('saana_lib.connectMongo.db.patient_symptoms')
        mock.find.return_value=list()
        _ = self.default_patient.symptoms
        assert mock.find.call_count == 1

    def test_treatment_drugs_property(self, mocker):
        mock = mocker.patch('saana_lib.connectMongo.db.patient_drugs')
        mock.find.return_value=list()
        _ = self.default_patient.treatment_drugs
        assert mock.find.call_count == 1

    def test_user_of_patient_property_1(self, mocker, users_mock):
        users_mock.find_one.return_value = None
        with pytest.raises(ScoreboardPatientException):
            _ = self.default_patient.user_of_patient

    """
    The next three tests check the logic circuit, testing almost each
    possible flow
    """

    def test_has_active_subscription_1(self, mocker):
        mock = mocker.patch(
            'saana_lib.connectMongo.db.patient_subscriptions',
        )
        mock.find_one.return_value = None
        assert not self.default_patient.has_active_subscription

    def test_has_active_subscription_2(self, mocker):
        mock = mocker.patch(
            'saana_lib.connectMongo.db.patient_subscriptions',
        )
        mock.find_one.return_value = {'status': 'inactive'}
        assert not self.default_patient.has_active_subscription

    def test_has_active_subscription_3(self, mocker):
        mock_1 = mocker.patch(
            'saana_lib.connectMongo.db.patient_subscriptions',
        )
        mock_1.find_one.return_value = {'status': 'active', 'subscription_id': 1}

        mock_2 = mocker.patch(
            'saana_lib.connectMongo.db.mst_subscriptions',
        )
        mock_2.find_one.return_value = {'interval_count': 1}
        mock_3 = mocker.patch(
            'saana_lib.connectMongo.db.orders',
        )
        mock_3.find_one.return_value = {}
        assert self.default_patient.has_active_subscription
        assert mock_1.find_one.called
        assert mock_2.find_one.called
        assert not mock_3.called

    def test_has_active_subscription_4(self, mocker):
        mock_1 = mocker.patch(
            'saana_lib.connectMongo.db.patient_subscriptions',
        )
        mock_1.find_one.return_value = {'status': 'active', 'subscription_id': 1}
        mock_2 = mocker.patch(
            'saana_lib.connectMongo.db.mst_subscriptions',
        )
        mock_2.find_one.return_value = {'interval_count': 2}
        mock_3 = mocker.patch(
            'saana_lib.connectMongo.db.orders',
        )
        mock_3.find_one.return_value = 1
        assert not self.default_patient.has_active_subscription
        assert mock_2.find_one.called
        assert mock_2.find_one.called

    def test_patient_tags_1(self, mocker):
        # check that the three properties are checked.
        tags_mock = mocker.patch('saana_lib.connectMongo.db.tags')
        mock_1 = mocker.patch('saana_lib.connectMongo.db.patient_comorbidities')
        mock_2 = mocker.patch('saana_lib.connectMongo.db.patient_diseases')
        mock_3 = mocker.patch('saana_lib.connectMongo.db.patient_drugs')
        mock_4 = mocker.patch('saana_lib.connectMongo.db.patient_symptoms')
        _ = self.default_patient.tags
        assert tags_mock.find.call_count == 1
        mock_1.find.assert_called_once_with({'patient_id': PATIENT_DATA['_id']})
        mock_2.find.assert_called_once_with({'patient_id': PATIENT_DATA['_id']})
        mock_3.find.assert_called_once_with({'patient_id': PATIENT_DATA['_id']})
        mock_4.find.assert_called_once_with({'patient_id': PATIENT_DATA['_id']})

    @pytest.mark.skip('')
    def test_patient_tags_repetitive_calls(self, mocker):
        tags_mock = mocker.patch('saana_lib.connectMongo.db.tags')
        tags_mock.find.return_value = 1
        mocker.patch('saana_lib.connectMongo.db.patient_comorbidities')
        mocker.patch('saana_lib.connectMongo.db.patient_diseases')
        mocker.patch('saana_lib.connectMongo.db.patient_drugs')
        mocker.patch('saana_lib.connectMongo.db.patient_symptoms')
        for i in range(4):
            _ = self.default_patient.tags
        tags_mock.find.assert_called_once_with()

    def test_avoid_property(self, mocker):
        mock = mocker.patch(
            'saana_lib.scoreboard.ScoreboardPatient.tags',
            new_callable=mocker.PropertyMock
        )
        _ = self.default_patient.avoid
        mock.assert_called_once_with()

    def test_minimize_property(self, mocker):
        mock = mocker.patch(
            'saana_lib.scoreboard.ScoreboardPatient.tags',
            new_callable=mocker.PropertyMock
        )
        _ = self.default_patient.minimize
        mock.assert_called_once_with()

    def test_prioritize_property(self, mocker):
        mock = mocker.patch(
            'saana_lib.scoreboard.ScoreboardPatient.tags',
            new_callable=mocker.PropertyMock
        )
        _ = self.default_patient.prioritize
        mock.assert_called_once_with()


@pytest.fixture
def repeating_meals(mocker):
    mock = mocker.patch(
        'saana_lib.scoreboard.Scoreboard.repeating_meals',
        return_value=(list(), list())
    )
    return mock


@pytest.mark.usefixtures("manual_input_mock", "repeating_meals")
class TestCaseScoreboard(object):

    @pytest.fixture
    def patients_mock(self, mocker):
        return mocker.patch(
            'saana_lib.scoreboard.Scoreboard.patients',
            new_callable=mocker.PropertyMock
        )

    @pytest.fixture
    def db_patients_mock(self, mocker):
        mock = mocker.patch('saana_lib.connectMongo.db.patients')
        mock.find.return_value = [PATIENT_DATA]
        return mock

    def test_as_dict_1(self, patients_mock):
        assert Scoreboard().as_dict() == {}
        assert patients_mock.call_count == 1

    def test_all_patients_property_1(self, mocker, db_patients_mock):
        """There is one patient which is valid"""
        mock_1 = mocker.patch('saana_lib.scoreboard.Scoreboard.is_patient_to_skip')
        mock_1.return_value = False
        plist = list(Scoreboard().all_patients)
        assert len(plist) == 1
        assert db_patients_mock.find.call_count == 1

    def test_all_patients_property_2(self, mocker, db_patients_mock):
        """The only patient being present is skipped"""
        mock_1 = mocker.patch('saana_lib.scoreboard.Scoreboard.is_patient_to_skip')
        mock_1.return_value = True
        plist = list(Scoreboard().all_patients)
        assert len(plist) == 0
        assert mock_1.call_count == 1

    def test_is_patient_to_skip_1(self, manual_input_mock, mocker):
        mock_2 = mocker.patch(
            'saana_lib.scoreboard.ScoreboardPatient.has_active_subscription',
            new_callable=mocker.PropertyMock
        )
        mock_2.return_value = False
        assert Scoreboard().is_patient_to_skip(ScoreboardPatient(PATIENT_DATA))
        
    def test_is_patient_to_skip_2(self, manual_input_mock):
        manual_input_mock.return_value = ([], ['email'])
        assert Scoreboard().is_patient_to_skip(
            ScoreboardPatient(PATIENT_DATA)
        )

    def test_patients_property_1(self, mocker):
        mock = mocker.patch(
            'saana_lib.scoreboard.Scoreboard.all_patients',
            new_callable=mocker.PropertyMock
        )
        _ = Scoreboard().patients()
        assert mock.call_count == 1

    def test_patients_property_2(self, mocker, db_patients_mock):
        mock = mocker.patch('saana_lib.connectMongo.db.users')
        _ = Scoreboard().patients(patient_email='email')
        assert mock.find_one.call_count == 1

    def test_patients_property_3(self, mocker, db_patients_mock):
        mocker.patch('saana_lib.connectMongo.db.users')
        db_patients_mock.find_one.return_value = None
        assert Scoreboard().patients(patient_email='email') == list()
        assert db_patients_mock.find_one.call_count == 1

    @pytest.mark.skip('')
    def test_as_dict_2(self, patients_mock, mocker):
        mock = mocker.patch('saana_lib.connectMongo.db.patients')
        mock.find_one.return_value = mocker.Mock(spec=ScoreboardPatient)
        _ = Scoreboard().as_dict(patient_email='email@email')

        assert patients_mock.call_count == 0
        assert mock.find_one.call_count == 1

    @pytest.mark.skip('')
    def test_as_file(self, mocker):
        csv_writer = mocker.patch('saana_lib.utils.csv_writer')
        _ = Scoreboard().as_file()
        assert csv_writer.call_count == 1

    def test_meals_property_1(self, empty_meals):
        optimizer = Scoreboard()
        assert optimizer.meals == dict()

    def test_meals_property_2(self, mocker):
        from tests.conftest import MEAL_DATA

        meal_infos = mocker.patch('saana_lib.connectMongo.db.meal_infos')
        meal_infos.find.return_value = [MEAL_DATA, ]
        assert len(Scoreboard().meals) == 1
        assert meal_infos.find.called

    def test_meals_property_3(self, mocker):
        from tests.conftest import MEAL_DATA

        meal_infos = mocker.patch('saana_lib.connectMongo.db.meal_infos')
        meal_infos.find.return_value = [MEAL_DATA, ]

        get_ingredient_method = mocker.patch(
            'saana_lib.scoreboard.Scoreboard.get_ingredient_name',
        )

        meals_dict = Scoreboard().meals
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
            'saana_lib.scoreboard.Scoreboard.get_ingredient_name',
            return_value=None
        )
        meals_dict = Scoreboard().meals
        assert len(meals_dict) == 1
        assert get_ingredient_method.call_count == len(MEAL_DATA['ingredients'])
        assert len(meals_dict[MEAL_DATA['_id']].ingredients) == 0

    def test_get_scoreboard_method_1(self, mocker, repeating_meals):
        """Base case: no meals"""
        mocker.patch(
            'saana_lib.scoreboard.Scoreboard.meals',
            return_value=dict
        )
        optimizer = Scoreboard()
        assert optimizer.get_score_board(MagicMock(_id=1)) == dict()
        assert repeating_meals.call_count == 1

    @pytest.mark.skip('')
    def test_get_scoreboard_method_2(self, monkeypatch):
        """Base case: Meal's supplier != to the one manually provided
        with the supplier's file
        """
        def manual_input_stub(a):
            return ['s-2', ], list()

        monkeypatch.setattr(
            'saana_lib.scoreboard.manual_input',
            manual_input_stub
        )

        meal_obj = model.Meal(_id='meal-id', supplierID='s-1')
        monkeypatch.setattr(
            ScoreboardPatient,
            'meals',
            [meal_obj,]
        )
        optimizer = Scoreboard()
        assert optimizer.get_score_board(MagicMock(_id=1)) == dict()

    @pytest.mark.skip('')
    def test_get_scoreboard_method_3(self, monkeypatch):

        meal_obj = model.Meal(_id='meal-id', ingredients={'basil': '20'})
        monkeypatch.setattr(
            ScoreboardPatient,
            'meals',
            [meal_obj,]
        )
        optimizer = Scoreboard()
        assert {40: [{
            'meal': meal_obj,
            'prior': [],
            'minimize': [],
            'avoid': ['basil',]
        }]} == optimizer.get_score_board(MagicMock(_id=1), {}, ['basil',], {})

    @pytest.mark.skip('')
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
        monkeypatch.setattr(Scoreboard, 'meals', [meal_obj, ])
        optimizer = Scoreboard()
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

    @pytest.mark.skip('')
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
            ScoreboardPatient,
            'meals',
            [meal_obj,]
        )
        optimizer = Scoreboard()
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

    @pytest.mark.skip('')
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
            ScoreboardPatient,
            'meals',
            [meal_obj,]
        )
        optimizer = ScoreboardPatient()
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

    @pytest.mark.skip('')
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
            Scoreboard,
            'meals',
            [meal_obj,]
        )
        optimizer = ScoreboardPatient()
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

    @pytest.mark.skip('')
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
            ScoreboardPatient,
            'meals',
            [meal_obj,]
        )
        optimizer = ScoreboardPatient()
        assert {100: [{
            'meal': meal_obj,
            'prior': [],
            'minimize': [],
            'avoid': []
        }]} == optimizer.get_score_board(MagicMock(_id=1), {
            "sodium": 0}, [], {})

    @pytest.mark.skip('')
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
            ScoreboardPatient,
            'meals',
            [meal_obj,]
        )
        optimizer = ScoreboardPatient()
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

    @pytest.mark.skip('')
    def test_get_scoreboard_method_10(self, monkeypatch):
        """prioritize nutrients"""
        meal_obj = model.Meal(
            _id='meal-id',
            name='creamy celeriac soup',
            ingredients={"soy": 3},
            nutrition={"potassium": "1020.13 mg"}
        )
        monkeypatch.setattr(
            ScoreboardPatient,
            'meals',
            [meal_obj,]
        )
        optimizer = ScoreboardPatient()
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

    @pytest.mark.skip('')
    def test_get_scoreboard_method_11(self, monkeypatch):
        """prioritize nutrients"""
        meal_obj = model.Meal(
            _id='meal-id',
            name='creamy celeriac soup',
            ingredients={"soy": 3},
            nutrition={'cals': 500}
        )
        monkeypatch.setattr(
            ScoreboardPatient,
            'meals',
            [meal_obj,]
        )
        optimizer = ScoreboardPatient()
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

    @pytest.mark.skip('')
    def test_get_scoreboard_method_12(self, mocker, repeating_meals):
        """meal is in repeat_one_week meals"""
        meal = MagicMock()
        meal.name = 'creamy celeriac soup'
        meal._id = 'id'
        meal.ingredients = {"soy": 3}
        meal.nutrition = {'cals': 500}
        repeating_meals.return_value = [meal], list()

        meals_mock = mocker.patch(
            'saana_lib.scoreboard.ScoreboardPatient.meals',
            new_callable=mocker.PropertyMock
        )
        meals_mock.return_value = [meal]

        optimizer = ScoreboardPatient()
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

    @pytest.mark.skip('')
    def test_get_scoreboard_method_13(self, mocker, repeating_meals):
        """meal is in repeat_two_week meals"""
        meal = MagicMock()
        meal.name = 'creamy celeriac soup'
        meal._id = 'id'
        meal.ingredients = {"soy": 3}
        meal.nutrition = {'cals': 500}
        repeating_meals.return_value = list(), [meal,]

        meals_mock = mocker.patch(
            'saana_lib.scoreboard.ScoreboardPatient.meals',
            new_callable=mocker.PropertyMock
        )
        meals_mock.return_value = [meal]
        optimizer = ScoreboardPatient()
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
        optimizer = Scoreboard()
        assert optimizer.adjust_score_according_to_calories(670, 500.0) == 10

    def test_adjust_score_according_to_calories_2(self):
        optimizer = Scoreboard()
        assert optimizer.adjust_score_according_to_calories(100, 500.0) == -10

    def test_adjust_score_according_to_calories_3(self):
        optimizer = Scoreboard()
        assert optimizer.adjust_score_according_to_calories(450, '400|700') == 10


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
        optimizer = ScoreboardPatient()
        assert ('Admin.TestUser', [self.base_headers, ]) == optimizer.scoreboard_to_csv_rows({}, 'abf3ed')

    def test_scoreboard_to_csv_rows_2(self, patients):
        """scoreboard with one meal"""
        optimizer = ScoreboardPatient()
        row = [120, 'creamy celeriac soup', '', 'potassium:soy', '', '3b7750fa415d304', 'Admin']
        assert ('Admin.TestUser', [self.base_headers, row]) == optimizer.scoreboard_to_csv_rows({
            120: [{
                'meal': self.meal_obj,
                'prior': ['potassium', 'soy'],
                'minimize': [],
                'avoid': []
            }]
        }, 'abf3ed')



