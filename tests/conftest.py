from datetime import datetime
from unittest.mock import MagicMock

from pymongo.database import Collection
from bson.objectid import ObjectId
import pytest


PATIENT_DATA = {
    'feet': 5,
    'exercise': '1-2_per_month',
    'inches': 4,
    'questionnaire_session_id': ObjectId('5cabf1511887db3ac1a89e46'),
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
    '__v': 0
}


USER_DATA = {
    'is_email_verified': True,
    'is_account_locked': False,
    '_id': ObjectId('5cabf2ad37c87f3ac00e86ff'),
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
    {'quantity': 131.09, 'food_ingredient_id': ObjectId('5cafc1e73b7750e4f9533da0')},
    {'quantity': 14.97, 'food_ingredient_id': ObjectId('5cafc1e73b7750e4f9533da1')},
    {'quantity': 0.68, 'food_ingredient_id': ObjectId('5cafc1e73b7750e4f9533da2')},
    {'quantity': 12.26, 'food_ingredient_id': ObjectId('5cafc1e73b7750e4f9533da3')},
    {'quantity': 27.730000000000004, 'food_ingredient_id': ObjectId('5cafc1e73b7750e4f9533da4')},
    {'quantity': 320.0, 'food_ingredient_id': ObjectId('5cafc1e73b7750e4f9533da5')}
]


MEAL_DATA = {
    '_id': ObjectId('5cb0fa2f3b7750fa4c2d5a42'),
    'nutrition': NUTRITION_DATA,
    'image': 'https://recipe.url',
    'supplier_id': ObjectId('5cb0fa253b7750fa415d3043'),
    'updated_at': datetime(2019, 4, 8, 14, 20, 44, 390000),
    'type': 'dinner',
    'name': 'creamy celeriac soup with rosemary oat crumble',
    'created_at': datetime(2019, 4, 8, 14, 20, 44, 390000),
    'ingredients': INGREDIENTS_DATA
}


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
        return [deepcopy(MEAL_DATA), ]


class IngredientsCollectionMock(BaseCollectionMock):
    elements = list()

    def find(self, *args, **kwargs):
        return [INGREDIENTS_DATA, ]

    def find_one(self, *args, **kwargs):
        ingredients_id = [e['food_ingredient_id'].binary for e in INGREDIENTS_DATA]
        ing = set(ingredients_id).difference(set(self.elements)).pop()
        self.elements.append(ing)
        return {'name': 'basil'}


class FakeDb:
    def __init__(self, **kwargs):
        super().__init__()
        for k, v in kwargs.items():
            setattr(self, k, v())


class MongoStub:

    def __init__(self, **kwargs):
        self.db = FakeDb(**kwargs)


def get_mongo_stub(**kwargs):
    return FakeDb(**kwargs)


@pytest.fixture
def manual_input_patch(monkeypatch):
    def manual_input_stub(a):
        return list(), list()

    monkeypatch.setattr(
        'saana_lib.optimizeMealSimple.manual_input',
        manual_input_stub
    )
    return monkeypatch


@pytest.fixture
def patients(monkeypatch):
    from saana_lib import connectMongo, manual_input, optimizeMealSimple

    def get_patient_related_data_stub(a, b):
        return list(), list(), list(), list()

    monkeypatch.setattr(connectMongo, 'db', get_mongo_stub(
        patients=PatientsCollectionMock,
        users=UsersCollectionMock,
    ))
    monkeypatch.setattr(
        optimizeMealSimple.Optimizer,
        'get_patient_related_data',
        get_patient_related_data_stub
    )
    return monkeypatch


@pytest.fixture
def empty_patients(patients):
    from saana_lib import connectMongo

    patients.setattr(connectMongo, 'db', get_mongo_stub(
        patients=BaseCollectionMock,
        users=UsersCollectionMock
    ))


@pytest.fixture
def empty_meals(monkeypatch):
    from saana_lib import connectMongo

    monkeypatch.setattr(connectMongo, 'db', get_mongo_stub(
        meal_infos=BaseCollectionMock
    ))


@pytest.fixture
def meals_patch(monkeypatch):
    from saana_lib import connectMongo

    monkeypatch.setattr(connectMongo, 'db', get_mongo_stub(
        meal_infos=MealsCollectionMock
    ))
    return monkeypatch




