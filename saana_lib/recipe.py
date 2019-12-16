from pymongo.collection import ObjectId

from saana_lib.connectMongo import db


class Recipe:

    def __init__(self, recipe_id=None):
        self.recipe_id = recipe_id
        if not isinstance(self.recipe_id, ObjectId):
            self.recipe_id = ObjectId(self.recipe_id)

    @property
    def recipe(self):
        return db.mst_recipes.find_one({'_id': self.recipe_id})

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
            (e['ingredient_full_name'], e['quantity'])
            for e in self.ingredients
        )

    @property
    def ingredients_names(self):
        return list(
            e['ingredient_full_name'] for e in self.ingredients
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
            (nutrient['_id'], nutrient)
            for nutrient in self.recipe.get('nutrients', {})
        )
