import logging

from abc import ABCMeta
from constants import constants_wrapper as constants
from saana_lib.connectMongo import db
from saana_lib.patient import SymptomsProgress, Nutrients
from saana_lib.recommendation import MinimizeIngredients, PrioritizeIngredients, \
    AvoidIngredients
from saana_lib.recipe import Recipe


logger = logging.getLogger(__name__)

def matching_ingredients(ingredients, obj):
    '''
    find if there is match between ingredients names 
    :param ingredients: [str] and list of ingredients 
    return True if similar 
    '''
    ingr = ingredients
    #change to ingredient short name not full name
    obj_tags = obj
    matched_ingr = ""
    comparison = False

    for item in obj_tags:
        if item in ingr:
            comparison = True
            matched_ingr = item
    splits = ingr.split()
    if comparison == False:
        for split in splits:
            for item in obj_tags:
                if split in item:
                    matched_ingr = item
                if item in split:
                    matched_ingr = item
    print (matched_ingr)
    return matched_ingr

class RecipeScore:
    __metaclass__ = ABCMeta

    def __init__(self, recipe_id, patient_id):
        self.recipe = Recipe(recipe_id)
        self.patient_id = patient_id
        self.score = 0
        self._multiplier_ingredients = None

    def value(self, **kwargs):
        raise NotImplementedError()


class IngredientScore:

    def __init__(self, progress_ingredient=False):
        if progress_ingredient:
            self.multiplier = constants.INGREDIENT_PROGRESS_MULTIPLIER
        else:
            self.multiplier = constants.DEFAULT_INGREDIENT_MULTIPLIER

    def single_value_score(self, val, ref):
        """
        :param val: recipe ingredient's quantity
        :param ref: patient quantity reference for that ingredient
        """
        deduct = 0

        if val > ref:
            deduct = constants.DEDUCT_SINGLE_VALUE * self.multiplier
        return 0 - deduct

    def lower_upper_bound_score(self, val, ref):
        """as today if the val is less than (<=) min1, no value
        is deducted from the score (originally was
        constants.DEDUCT_LT_MIN1 * multiplier_factor)

        :param score: current score
        :param val: recipe ingredient's quantity
        :param ref: patient quantity reference for that ingredient
        """
        deduct = 0

        if val >= float(ref.get('min2', 0)):
            deduct = constants.DEDUCT_GR_MIN2 * self.multiplier
        elif val >= float(ref.get('min1', 0)):
            deduct = constants.DEDUCT_GR_MIN1 * self.multiplier

        return 0 - deduct


class MinimizedScore(RecipeScore):

    @property
    def worsen_ingredients(self):
        if self._multiplier_ingredients is None:
            self._multiplier_ingredients = SymptomsProgress(self.patient_id).worsen
        return self._multiplier_ingredients

    @property
    def ingredient_set(self):
        minimized = MinimizeIngredients(self.patient_id).all
        for ingr_name, quantity in self.recipe.ingredients_name_quantity.items():
              if matching_ingredients(ingr_name, minimized) != "":
                  quantity_ref = minimized[matching_ingredients(ingr_name, minimized)]
                  #yield ingr_name, quantity, quantity_ref
##                # add quantity stuff
##                #yiel quantity ref..
                  yield 1
##            if ingr_name in minimized:
                

    @property
    def value(self):
        """"""
        return 0 - sum(self.ingredient_set) * constants.DEDUCT_AVOID
##        for ingr_id, quantity, ref_quantity in self.ingredient_set:
            #add symptomes stuff
            
##            isc = IngredientScore(ingr_id in self.worsen_ingredients)
##            if isinstance(ref_quantity, dict):
##                self.score += isc.lower_upper_bound_score(
##                    quantity, ref_quantity
##                )
##            else:
##                self.score += isc.single_value_score(
##                    quantity, ref_quantity
##                )
##        return self.score


class PrioritizedScore(RecipeScore):

    @property
    def ingredient_set(self):
        prioritized = PrioritizeIngredients(self.patient_id).all
        for ingr_name, quantity in self.recipe.ingredients_name_quantity.items():
            if matching_ingredients(ingr_name, prioritized) != "" and int(quantity) > int(prioritized[matching_ingredients(ingr_name, prioritized)]):
                yield 1
##            if ingr_name in prioritized and quantity > prioritized[ingr_name]:
##                yield 1

    @property
    def value(self):
        return sum(self.ingredient_set) * constants.ADD_PRIOR


class AvoidScore(RecipeScore):

    @property
    def ingredient_set(self):
        avoids = AvoidIngredients(self.patient_id).all
        #not ok because not exact same names of ingredients 
        for ingr_name, quantity in self.recipe.ingredients_name_quantity.items():
            if matching_ingredients(ingr_name, avoids) != "":
                yield 1
##            if ingr_name in avoids:
##                yield 1
            
    @property
    def value(self):
        return 0 - sum(self.ingredient_set) * constants.DEDUCT_AVOID


class NutrientScore(RecipeScore):
    """
    # TODO: this method should be refactored using this schema as model

    nutrient: string
    quantity: int
    unit: string  [mg, gr, cals, ...]
    type: min/prior
    """
    @property
    def nutrient_set(self):
        """
        :returns the ObjectId(s) of those nutrients that are in
        both sets
        """
        return set(self.recipe.nutrients.keys()).intersection(
            set(Nutrients(self.patient_id).all.keys())
        )

    def _get_nutrient_facts(self, nutrient_id):
        return self.recipe.nutrients[nutrient_id], Nutrients(self.nutrient_set).all.get(nutrient_id)

    def calories_score(self, nutrient_id):
        quantity, quantity_ref = self._get_nutrient_facts(nutrient_id)

        if isinstance(quantity_ref, dict):
            if quantity > quantity_ref['upper']:
                val = 0 - constants.ADD_CALORIES * 2
            elif quantity > quantity_ref['lower']:
                val = 0 - constants.DEDUCT_CALORIES
            else:
                val = 0 + constants.ADD_CALORIES
        else:
            if quantity >= quantity_ref:
                val = 0 - constants.DEDUCT_CALORIES
            else:
                val = 0 + constants.ADD_CALORIES

        return val

    @property
    def add_calories_score(self):
    #   TODO CHECK DB
    #   nutrient_obj_id = db.mst_nutrients.find_one({'name': 'calories'})
        if nutrient_obj_id in self.nutrient_set:
            return self.calories_score(nutrient_obj_id)
        return 0

    @property
    def value(self):
        """
        the simplest way to get the name of a single nutrient is
        to query it.
        """
        return len(self.nutrient_set) + self.add_calories_score



