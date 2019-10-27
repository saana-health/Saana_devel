from datetime import datetime

import pytest

from tests.conftest import assert_equal_objects
from saana_lib.ingredient_recommendation import AvoidRecommendation, MinimizeRecommendation


@pytest.fixture
def tags_mock(mocker):
    m = mocker.patch(
        'saana_lib.ingredient_recommendation.IngredientRecommendation.tags',
        new_callable=mocker.PropertyMock
    )
    return m


def test_new_ingredient_is_created(integration_setup, mocker, datetime_mock):
    """Verify that only one new ingredient is created after
    calling the as_list() method.
    """
    test_db = integration_setup
    mocker.patch('saana_lib.ingredient_recommendation.db', test_db)
    test_db.mst_food_ingredients.insert_one({
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

    assert test_db.mst_food_ingredients.find_one({'name': 'onion'})
    assert test_db.mst_food_ingredients.estimated_document_count() == 2


def test_two_same_recommendations_are_created(
        integration_setup,
        mocker,
        datetime_mock):
    """No duplicate error is raised"""

    from pymongo.collection import ObjectId

    test_db = integration_setup
    mocker.patch('saana_lib.ingredient_recommendation.db', test_db)

    res = test_db.mst_food_ingredients.insert_one({
        'name': 'flax',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
    })

    test_db.patient_ingredient_recommendation.insert_one({
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

    _ = MinimizeRecommendation('5cab584074e88f0cb0977a08').to_db()

    assert test_db.patient_ingredient_recommendation.estimated_document_count() == 2
    assert test_db.patient_ingredient_recommendation.find_one()['type'] == 'min'




