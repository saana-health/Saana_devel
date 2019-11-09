from datetime import datetime
from unittest.mock import MagicMock

from pymongo.database import Collection
from bson.objectid import ObjectId
import pytest

from saana_lib import connectMongo, ranking


PATIENT_DATA = {
    'feet': 5,
    'exercise': '1-2_per_month',
    'inches': 4,
    'questionnaire_session_id': '5cabf1511887db3ac1a89e46',
    '_id': '5cabf2ad37c87f3ac00e8701',
    'weight': 182,
    'preferred_coaching_channel': 'text',
    'updated_at': datetime(2019, 4, 9, 1, 17, 33, 866000),
    'created_at': datetime(2019, 4, 9, 1, 17, 33, 866000),
    'identity': 'patient',
    'gender': 'female',
    'past_radiation': 'no',
    'further_chemo': 'no',
    'past_surgery': 'yes',
    'surgery_what': 'none',
    'surgery': 'NA',
    'age': 52,
    'user_id': '5cabf2ad37c87f3ac00e86ff',
    '__v': 0
}


USER_DATA = {
    'is_email_verified': True,
    'is_account_locked': False,
    '_id': '5cabf2ad37c87f3ac00e86ff',
    'is_deleted': False,
    'salt': '7f039ee0-5a09-11e9-bab7-f3ab285a283c',
    'updated_at': datetime(2019, 4, 8, 14, 20, 44, 390000),
    'email': 'test_user@saana.co',
    'last_name': 'TestUser',
    'role': 'superAdmin',
    'created_at': datetime(2019, 4, 8, 14, 20, 44, 390000),
    '__v': 0,
    'first_name': 'Admin',
    'password': '862156a6e9a45212b99e8f3bae6d6be4c1547b6b'
}


NUTRITION_DATA = {
    'moly': '6.55 mcg',
    'vit b3': '1.13 mg',
    'cals': '23.490000000000002 kcal',
    'chln': '12.37 mg',
    'panto': '0.58 mg',
    'vit e-a-toco': '1.76 mg',
    'prot': '12.639999999999999 g',
    'total fiber': '11.98 g',
    'magn': '55.440000000000005 mg',
}


INGREDIENTS_DATA = [
    {'quantity': 131.09, 'food_ingredient_id': '5cafc1e73b7750e4f9533da0'},
    {'quantity': 14.97, 'food_ingredient_id': '5cafc1e73b7750e4f9533da1'},
    {'quantity': 0.68, 'food_ingredient_id': '5cafc1e73b7750e4f9533da2'},
    {'quantity': 12.26, 'food_ingredient_id': '5cafc1e73b7750e4f9533da3'},
    {'quantity': 27.730000000000004, 'food_ingredient_id': '5cafc1e73b7750e4f9533da4'},
    {'quantity': 320.0, 'food_ingredient_id': '5cafc1e73b7750e4f9533da5'}
]


MEAL_DATA = {
    '_id': '5cb0fa2f3b7750fa4c2d5a42',
    'nutrition': NUTRITION_DATA,
    'image': 'https://recipe.url',
    'supplier_id': '5cb0fa253b7750fa415d3043',
    'updated_at': datetime(2019, 4, 8, 14, 20, 44, 390000),
    'type': 'dinner',
    'name': 'creamy celeriac soup with rosemary oat crumble',
    'created_at': datetime(2019, 4, 8, 14, 20, 44, 390000),
    'ingredients': INGREDIENTS_DATA
}


TAGS_DATA = [{
    'type': 'symptoms',
    'minimize': {},
    'tag_id': '5cab584074e88f0cb0977a10',
    'name': 'inflammation',
    'avoid': [],
    'prior': {
        'saury fish': 0,
        'fish': 0,
        'cabbage': 0,
        'pak choi': 0,
        'komatsuna': 0
        }
    },{
    'type': 'symptoms',
    'minimize': {
        'insoluble fiber': {'min2': '15', 'min1': '10'}
        },
    'tag_id': '5cab584074e88f0cb0977a0a',
    'name': 'diarrhea',
    'avoid': [],
    'prior': {
        'asparagus': 0,
        'sweet potato': 0,
        'green beans': 0,
        'zucchini': 0,
        'seaweed': 0,
        'ginger': 0,
        'carrot': 0,
        'potato': 0}
    }]


@pytest.fixture(autouse=True)
def set_dev_env(monkeypatch):
    """Remove requests.sessions.Session.request for all tests."""
    monkeypatch.setenv('DEV_ENV', 'true')


@pytest.fixture
def argparse_patch(monkeypatch):
    import argparse

    class ArgumentParserMock:

        def add_argument(self, *args, **kwargs):
            pass

        def parse_args(self):
            return argparse.Namespace(mode='test')

    monkeypatch.setattr(argparse, 'ArgumentParser', ArgumentParserMock)
    return monkeypatch


@pytest.fixture
def default_patient():
    return PATIENT_DATA


@pytest.fixture
def default_user():
    return USER_DATA


class BaseCollectionMock(MagicMock):
    spec = Collection

    def find(self, *args, **kwargs):
        return list()


class PatientsCollectionMock(BaseCollectionMock):
    empty = False

    def find(self):
        if self.empty:
            return list()

        return [PATIENT_DATA,]


class TagsCollectionMock(BaseCollectionMock):

    def find(self):
        return TAGS_DATA


class UsersCollectionMock(BaseCollectionMock):

    def find(self):
        return USER_DATA

    def find_one(self, *args, **kwargs):
        return self.find()


class ComorbitiesCollectionMock(BaseCollectionMock):
    """"""


class MealsCollectionMock(BaseCollectionMock):

    def find(self, *args, **kwargs):
        from copy import deepcopy
        return {ObjectId('5cb0fa2f3b7750fa4c2d5a42'): deepcopy(MEAL_DATA)}


class FakeDb:
    def __init__(self, **kwargs):
        super().__init__()
        for k, v in kwargs.items():
            setattr(self, k, v())


def get_mongo_stub(**kwargs):
    return FakeDb(**kwargs)


@pytest.fixture
def manual_input_mock(mocker):
    m = mocker.patch(
        'saana_lib.scoreboard.manual_input',
        return_value=([], [])
    )
    return m


@pytest.fixture
def scoreboard_base_patch(file_opening):

    class datetime_mock(MagicMock):
        @classmethod
        def now(cls):
            return '2019-09-18T11:10:00'

    file_opening.setattr(
        ranking,
        'datetime',
        datetime_mock
    )


@pytest.fixture
def patients(monkeypatch):

    def get_patient_related_data_stub(a, b):
        return list(), list(), list(), list()

    monkeypatch.setattr(connectMongo, 'db', get_mongo_stub(
        patients=PatientsCollectionMock,
        users=UsersCollectionMock,
    ))
    return monkeypatch


@pytest.fixture
def empty_patients(patients):

    patients.setattr(connectMongo, 'db', get_mongo_stub(
        patients=BaseCollectionMock,
        users=UsersCollectionMock
    ))


@pytest.fixture
def empty_meals(monkeypatch):
    monkeypatch.setattr(connectMongo, 'db', get_mongo_stub(
        meal_infos=BaseCollectionMock
    ))


@pytest.fixture
def meals_patch(monkeypatch):
    monkeypatch.setattr(connectMongo, 'db', get_mongo_stub(
        meal_infos=MealsCollectionMock
    ))
    return monkeypatch


@pytest.fixture
def tags_patch(monkeypatch):

    monkeypatch.setattr(connectMongo, 'db', get_mongo_stub(
        tags=TagsCollectionMock,
    ))
    return monkeypatch


@pytest.fixture(name='file_opening')
def file_opening(mocker):
    fopen_mock = mocker.patch('builtins.open')
    return fopen_mock


def assert_equal_objects(o1, o2):
    """
    o1 and o2 are two objects. might be of almost any type (i'm
    sure that there are some Python types that will break this out)
    but basically this utility comes in hand for those cases where
    I have to compare sequences (as tuple, lists) that are generated
    in a way that the original order is not preserved (ex. a list
    generated during the execution of for loop over a dictionary)
    """
    def _dict_equal(d1, d2):
        """
        this assert over the length of d1 is to guarantee that
        the same number of keys are contained in both dictionaries
        that's because if d1 is empty it won't enter the loop
        resulting in two identical objects, when indeed they
        might not be
        """
        assert len(d1) == len(d2)
        for k, v in d1.items():
            assert k in d2
            assert_equal_objects(v, d2[k])

    assert type(o1) is type(o2)
    if not hasattr(o1, '__iter__') or isinstance(o1, str):
        assert o1 == o2
    elif isinstance(o1, dict):
        _dict_equal(o1, o2)
    else:
        o1 = list(o1)
        o2 = list(o2)
        assert len(o1) == len(o2)
        for pos, el in enumerate(o1):
            if isinstance(el, dict):
                _dict_equal(el, o2[pos])
            else:
                assert el in o2


def assert_not_equal_objects(o1, o2):
    """
    If two objects are not the same, then an AssertionError is
    expected. If no exception is caught, then the two objects
    are the same and False is returned
    """
    def _assert_not_equal_objects(o1, o2):
        try:
            assert_equal_objects(o1, o2)
        except AssertionError as e:
            print(e)
            return True
        else:
            return False

    assert _assert_not_equal_objects(o1, o2)


def assert_equal_tuples(t1, t2):
    assert len(t1) == len(t2)
    for pos, element in enumerate(t1):
        assert_equal_objects(element, t2[pos])


@pytest.fixture(name='integration_setup')
def integration_tests_setup(mocker):
    test_db = connectMongo.client.test_db

    if test_db.patients.estimated_document_count() == 0:
        PATIENT_DATA.pop('_id')
        test_db.patients.insert_one(PATIENT_DATA)

    if test_db.users.estimated_document_count() == 0:
        USER_DATA.pop('_id')
        test_db.users.insert_one(USER_DATA)

    if test_db.nutrition_facts.estimated_document_count() == 0:
        test_db.nutrition_facts.insert_one(NUTRITION_DATA)
        test_db.ingredients.insert_many(INGREDIENTS_DATA)

    if test_db.meals.estimated_document_count() == 0:
        MEAL_DATA.pop('_id')
        test_db.meals.insert_one(MEAL_DATA)

    if test_db.tags.estimated_document_count() == 0:
        test_db.tags.insert_many(TAGS_DATA)

    yield test_db
    connectMongo.client.drop_database('test_db')


@pytest.fixture
def datetime_mock(mocker):
    from datetime import datetime
    mock = mocker.patch('saana_lib.recommendation.datetime')
    mock.now.return_value = datetime(2019, 5, 18, 15, 17, 8, 132263)
    return mock


def obj_id():
    return ObjectId('5d7258c977f06d4208211eb4')

