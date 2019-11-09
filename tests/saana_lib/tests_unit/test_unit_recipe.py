from datetime import timedelta, datetime

from pymongo.collection import ObjectId


from saana_lib.recipe import Recipe
from tests.conftest import assert_equal_objects


def obj_id():
    return ObjectId('5d7258c977f06d4208211eb4')


def test_recipe_init(mocker):
    ingredients_collection = mocker.patch('saana_lib.recipe.db.mst_recipe')
    _ = Recipe('5d7258c977f06d4208211eb4')
    ingredients_collection.find_one.assert_called_with({'_id': obj_id()})


def test_ingredients_id_prop_values(mocker):
    mocker.patch(
        'saana_lib.recipe.Recipe.recipe',
        new_callable=mocker.PropertyMock,
        return_value={'food': [{'food_ingredient_id': 1}, {'food_ingredient_id': 2}]}
    )
    assert_equal_objects(Recipe(obj_id()).ingredients_id, [1, 2])


def test_ingredients_id_quantities_values(mocker):
    mocker.patch(
        'saana_lib.recipe.Recipe.recipe',
        new_callable=mocker.PropertyMock,
        return_value={'food': [
            {'food_ingredient_id': 1, 'quantity': 10},
            {'food_ingredient_id': 2, 'quantity': 30}
        ]}
    )
    assert_equal_objects(
        Recipe(obj_id()).ingredients_id_quantity,
        {1: 10, 2: 30}
    )


def test_ingredients_names_quantities(mocker):
    mocker.patch(
        'saana_lib.recipe.Recipe.ingredients',
        new_callable=mocker.PropertyMock,
        return_value=[{'food_ingredient_fullname': 'Lactose', 'quantity': 2}]
    )
    assert_equal_objects(
        Recipe(obj_id()).ingredients_name_quantity,
        {'Lactose': 2}
    )


