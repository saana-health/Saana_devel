import pytest

from saana_lib.recipe import Recipe
from tests.conftest import obj_id

recipe_id = obj_id


def test_recipe_ingredients(integration_db, mocker):
    assert len(Recipe('a85f7f35a9963e1bbea2355a').ingredients_name_quantity) == 6


