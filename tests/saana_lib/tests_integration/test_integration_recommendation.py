from datetime import datetime

import pytest

from tests.conftest import assert_equal_objects, obj_id
from saana_lib.recommendation import AvoidRecommendation, MinimizeRecommendation, \
    RecipeRecommendation, AllRecommendations


# TODO
# for every test in this file, let integration_setup fixture
# to be automatically activated


@pytest.fixture
def tags_mock(mocker):
    m = mocker.patch(
        'saana_lib.recommendation.IngredientRecommendation.tags',
        new_callable=mocker.PropertyMock
    )
    return m


def test_new_ingredient_is_created(integration_db, mocker):
    """Verify that only one new ingredient is created after
    calling the as_list() method.
    """
    integration_db.mst_food_ingredients.insert_one({
        'name': 'flax',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
    })
    mocker.patch(
        'saana_lib.patient.AvoidIngredients.all',
        new_callable=mocker.PropertyMock,
        return_value={"onion", "flax"}
    )
    _ = AvoidRecommendation('5cab584074e88f0cb0977a08').as_list()

    assert integration_db.mst_food_ingredients.find_one({'name': 'onion'})
    assert integration_db.mst_food_ingredients.estimated_document_count() == 15


def test_two_same_recommendations_are_created(integration_db, mocker):
    """No duplicate error is raised"""

    from pymongo.collection import ObjectId

    res = integration_db.mst_food_ingredients.insert_one({
        'name': 'flax',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
    })

    integration_db.patient_ingredient_recommendation.insert_one({
        'patient_id': ObjectId('5cab584074e88f0cb0977a08'),
        'ingredient_id': res.inserted_id,
        'type': "min",
        'quantity': 0,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
    })

    mocker.patch(
        'saana_lib.patient.MinimizeIngredients.all',
        new_callable=mocker.PropertyMock,
        return_value={"flax": 0}
    )

    _ = MinimizeRecommendation(obj_id().__str__()).to_db()

    assert integration_db.patient_ingredient_recommendation.estimated_document_count() == 2
    assert integration_db.patient_ingredient_recommendation.find_one()['type'] == 'min'


def test_all_ingredients_recommendation(integration_db):
    from tests.conftest import PATIENT, ObjectId

    AllRecommendations(PATIENT['_id'].__str__()).store()
    assert integration_db.patient_ingredient_recommendation.estimated_document_count() == 13
    assert integration_db.patient_ingredient_recommendation.find_one(
        {'ingredient_id': ObjectId('6f4ec514eee84cc58c8e610a')}
    )['type'] == 'avoid'
