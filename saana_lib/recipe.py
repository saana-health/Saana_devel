from datetime import timedelta

from pymongo.collection import ObjectId

from constants import constants_wrapper as constants
from saana_lib.connectMongo import db


"""
Schema of MST_RECIPE

name: {type: String, required: true,},
url: {type: String,},
created_at: {type: Date},
image_url: {type: String,},
food: [{
    food_ingredient_id: {type: ObjectId, ref: 'Mst_Food_Ingredient',},
    quantity: {type: Number,},
    unit: {type: String},}
]
nutrients: [{
    nutrient_id: {type: ObjectId, ref: 'Mst_Food_Ingredient',},
    quantity: {type: Number,},
    unit: {type: String},}
}],
updated_at: {type: Date}
"""
class Recipe:

    def __init__(self, recipe_id=None):
        self.recipe_id = recipe_id
        if not isinstance(self.recipe_id, ObjectId):
            self.recipe_id = ObjectId(self.recipe_id)
        self._recipe = db.mst_recipe.find_one({'_id': self.recipe_id})

    @property
    def recipe(self):
        return self._recipe

    @property
    def ingredients(self):
        return self.recipe['food']

    @property
    def ingredients_id(self):
        return list(e['food_ingredient_id'] for e in self.ingredients)

    @property
    def ingredients_id_quantity(self):
        """
        This property does not need to run an additional query
        because the recipe object contains and array with all
        the ingredients
        """
        return dict(
            (e['food_ingredient_id'], e['quantity'])
            for e in self.ingredients
        )

    @property
    def ingredients_name_quantity(self):
        """Instead to get the names of the ingredients another
        query is needed.
        """
        return dict(
            (e['food_ingredient_fullname'], e['quantity'])
            for e in self.ingredients
        )

    @property
    def ingredients_names(self):
        return list(
            e['food_ingredient_fullname'] for e in self.ingredients
        )

    @property
    def name(self):
        return self.recipe['name']

    """
    NOTE: these properties have yet to be implemented because, 
    as today Nov 3, recipes (which replaced meals) do not contain 
    any nutrients (i.e. there are no indications of nutrients)
    """
    @property
    def nutrients(self):
        return dict(
            (nutrient['nutrient_id'], nutrient)
            for nutrient in self.recipe['nutrient']
        )
