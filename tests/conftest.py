from datetime import datetime
from unittest.mock import MagicMock

from pymongo.database import Collection
from bson.objectid import ObjectId
import pytest

from saana_lib import connectMongo, ranking


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


@pytest.fixture
def integration_database_setup():
    from datetime import timedelta
    base_datetime = datetime(2019, 10, 10)
    test_db = connectMongo.client.test_db

    if test_db.patients.estimated_document_count() == 0:
        PATIENT['_id'] = ObjectId('311ee45a02f611eaaf720242')
        PATIENT['created_at'] = base_datetime - timedelta(days=1)
        PATIENT['updated_at'] = base_datetime - timedelta(days=1)
        test_db.patients.insert_one(PATIENT)

    if test_db.users.estimated_document_count() == 0:
        USER['_id'] = ObjectId('309a734602f611eaaf720242')
        USER['created_at'] = base_datetime - timedelta(days=2)
        USER['updated_at'] = base_datetime - timedelta(days=2)
        test_db.users.insert_one(USER)

    if test_db.nutrition_facts.estimated_document_count() == 0:
        test_db.nutrition_facts.insert_many(NUTRITIONS)
        test_db.mst_food_ingredients.insert_many(INGREDIENTS)

    if test_db.mst_recipe.estimated_document_count() == 0:
        test_db.mst_recipe.insert_many(RECIPES)

    if test_db.tags.estimated_document_count() == 0:
        test_db.tags.insert_many(TAGS)
        test_db.patient_symptoms.insert_one({
            'symptom_id': TAGS[0]['tag_id'],
            'patient_id': PATIENT['_id'],
            'created_at': base_datetime,
            'updated_at': base_datetime,
            'symptoms_scale': 4
        })
        test_db.patient_comorbidities.insert_one({
            'comorbidity_id': TAGS[1]['tag_id'],
            'patient_id': PATIENT['_id'],
            'created_at': base_datetime,
            'updated_at': base_datetime,
            'symptoms_scale': 3
        })
        test_db.patient_diseases.insert_one({
            'disease_id': TAGS[2]['tag_id'],
            'patient_id': PATIENT['_id'],
            'created_at': base_datetime,
            'updated_at': base_datetime,
            'symptoms_scale': 5
        })

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


PATIENT = {
    'feet': 5,
    'exercise': '1-2_per_month',
    'inches': 4,
    '_id': ObjectId('5cabf2ad37c87f3ac00e8701'),
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
    'user_id': ObjectId('5cabf2ad37c87f3ac00e86ff'),
}


USER = {
    'is_email_verified': True,
    'is_account_locked': False,
    '_id': ObjectId('5cabf2ad37c87f3ac00e86ff'),
    'is_deleted': False,
    'updated_at': datetime(2019, 4, 8, 14, 20, 44, 390000),
    'email': 'test_user@saana.co',
    'last_name': 'TestUser',
    'role': 'superAdmin',
    'created_at': datetime(2019, 4, 8, 14, 20, 44, 390000),
    'first_name': 'Admin',
    'password': '862156a6e9a45212b99e8f3bae6d6be4c1547b6b'
}


TAGS = [
    {
        'type': 'symptoms',
        'tag_id': ObjectId('4b91e35fe0c9cffa9e53b277'),
        'name': 'inflammation',
        'minimize': {
            'saury fish': 10,
            'fish': 20,
        },
        'avoid': ['ginger'],
        'prior': {
            'cabbage': 15,
            'pak choi': 100,
            'komatsuna': 34
        },
        'nutrient': {}
    },
    {
        'type': 'commobidity',
        'tag_id': ObjectId('29117dc0a099592ced9a6e00'),
        'name': 'diarrhea',
        'minimize': {
            'cabbage': {'min1': 30, 'min2': 200},
            'zucchini': {'min1': 2, 'min2': 20}
        },
        'avoid': ['carrot'],
        'prior': {
            'ginger': 10,
            'potato': 50
        },
        'nutrient': {}
    },
    {
        'type': 'disease',
        'tag_id': ObjectId('9f9a51ba8f5c0324299279ed'),
        'name': 'breast cancer',
        'minimize': {
            'seaweed': {'min2': '15', 'min1': '35'},
            'carrot': 30
        },
        'avoid': ['pak choi', 'ginger'],
        'prior': {
            'asparagus': 30,
            'sweet potato': 30,
            'green beans': 40,
        },
        'nutrient': {}
    }
]


INGREDIENTS = [
    {
        'name': 'saury fish',
        '_id': ObjectId('91b0794709d3300213eaf3d1')
    },
    {
        'name': 'fish',
        '_id': ObjectId('83e4a96aed96436c621b9809')
    },
    {
        'name': 'cabbage',
        '_id': ObjectId('b3188adab3f07e66582bbac4')
    },
    {
        'name': 'pak choi',
        '_id': ObjectId('1d2265b45b8a3c1b0fa27ca8')
    },
    {
        'name': 'komatsuna',
        '_id': ObjectId('9f9a51ba8f5c0324299279ed')
    },
    {
        'name': 'asparagus',
        '_id': ObjectId('08090207f34b0fd062aead92')
    },
    {
        'name': 'sweet potato',
        '_id': ObjectId('29193daa4a904cd3cc77854d')
    },
    {
        'name': 'green beans',
        '_id': ObjectId('8048b5e5a40738935af4d3d0')
    },
    {
        'name': 'zucchini',
        '_id': ObjectId('4ff258784836201af40c76e8')
    },
    {
        'name': 'seaweed',
        '_id': ObjectId('a7ef14cb46aa278a6c388136')
    },
    {
        'name': 'ginger',
        '_id': ObjectId('6f4ec514eee84cc58c8e610a')
    },
    {
        'name': 'carrot',
        '_id': ObjectId('005d05de29487ec44cd07bd9')
    },
    {
        'name': 'potato',
        '_id': ObjectId('8ee2027983915ec78acc4502')
    }
]


NUTRITIONS = [
    {
        'name': 'Protein',
        '_id': ObjectId('989e987c7aa4a808de81252f'),
    },
    {
        'name': 'Total lipid (fat)',
        '_id': ObjectId('e3e800af6cbbf4d438d3f94d'),
    },
    {
        'name': 'Energy',
        '_id': ObjectId('3e797dddd4dbb33adb18c8ce'),
    },
    {
        'name': 'Startch',
        '_id': ObjectId('02a42284998e2ce6a3776ad3'),
    },
    {
        'name': 'Sucrose',
        '_id': ObjectId('0479b5bfaeb44553de055511'),
    },
    {
        'name': 'Glucose',
        '_id': ObjectId('e8931f7482b091e90300c7f8'),
    },
    {
        'name': 'Fructose',
        '_id': ObjectId('b03f608e81ecd2ad921f2226'),
    },
    {
        'name': 'Lactose',
        '_id': ObjectId('07c1e26a796cf27eb4cde5fb'),
    },
    {
        'name': 'Maltose',
        '_id': ObjectId('d80ef1ffe8ba5a4b5458f5c6'),
    },
]


RECIPES = [{
    '_id': ObjectId('a85f7f35a9963e1bbea2355a'),
    'image': 'https://recipe-1.url',
    'image_url': '',
    'name': 'recipe 1',
    'created_at': datetime(2019, 4, 8, 14, 20, 44, 390000),
    'updated_at': datetime(2019, 4, 8, 14, 20, 44, 390000),
    'food': [
        {
            'food_ingredient_id': ObjectId('91b0794709d3300213eaf3d1'),
            'quantity': 10,
            'unit': 'g',
            'food_ingredient_fullname': 'saury fish',
        },
        {
            'food_ingredient_id': ObjectId('83e4a96aed96436c621b9809'),
            'quantity': 30,
            'unit': 'g',
            'food_ingredient_fullname': 'fish',
        },
        {
            'food_ingredient_id': ObjectId('b3188adab3f07e66582bbac4'),
            'quantity': 200,
            'unit': 'g',
            'food_ingredient_fullname': 'cabbage',
        },
        {
            'food_ingredient_id': ObjectId('1d2265b45b8a3c1b0fa27ca8'),
            'quantity': 10,
            'unit': 'g',
            'food_ingredient_fullname': 'pak choi',
        },
        {
            'food_ingredient_id': ObjectId('9f9a51ba8f5c0324299279ed'),
            'quantity': 10,
            'unit': 'g',
            'food_ingredient_fullname': 'komatsuna',
        },
        {
            'food_ingredient_id': ObjectId('08090207f34b0fd062aead92'),
            'quantity': 10,
            'unit': 'g',
            'food_ingredient_fullname': 'asparagus',
        }
    ],
    'nutrients': NUTRITIONS[:3]
    }, {
    '_id': ObjectId('c799fca3b97b6934613d6f38'),
    'image': 'https://recipe-2.url',
    'image_url': '',
    'name': 'recipe 2',
    'created_at': datetime(2019, 3, 1, 14, 10, 44, 390000),
    'updated_at': datetime(2019, 3, 1, 14, 10, 44, 390000),
    'food': [
        {
            'food_ingredient_id': ObjectId('8048b5e5a40738935af4d3d0'),
            'quantity': 30,
            'unit': 'mg',
            'food_ingredient_fullname': 'green beans',
        },
        {
            'food_ingredient_id': ObjectId('4ff258784836201af40c76e8'),
            'quantity': 14,
            'unit': 'g',
            'food_ingredient_fullname': 'zucchini',
        },
        {
            'food_ingredient_id': ObjectId('a7ef14cb46aa278a6c388136'),
            'quantity': 10,
            'unit': 'g',
            'food_ingredient_fullname': 'seaweed',
        },
        {
            'food_ingredient_id': ObjectId('6f4ec514eee84cc58c8e610a'),
            'quantity': 10,
            'unit': 'g',
            'food_ingredient_fullname': 'ginger',
        },
        {
            'food_ingredient_id': ObjectId('005d05de29487ec44cd07bd9'),
            'quantity': 10,
            'unit': 'g',
            'food_ingredient_fullname': 'carrot',
        },
        {
            'food_ingredient_id': ObjectId('8ee2027983915ec78acc4502'),
            'quantity': 60,
            'unit': 'g',
            'food_ingredient_fullname': 'potato',
        }
    ],
    'nutrients': NUTRITIONS[3:6]
}]


@pytest.fixture
def integration_db(integration_database_setup, mocker, datetime_mock):
    mocker.patch('saana_lib.patient.db', integration_database_setup)
    mocker.patch('saana_lib.ranking.db', integration_database_setup)
    mocker.patch('saana_lib.recipe.db', integration_database_setup)
    mocker.patch('saana_lib.recommendation.db', integration_database_setup)
    mocker.patch('saana_lib.score.db', integration_database_setup)
    mocker.patch('saana_lib.tag.db', integration_database_setup)
    return integration_database_setup
