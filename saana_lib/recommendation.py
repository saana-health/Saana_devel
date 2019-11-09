import logging
from datetime import datetime, timedelta

from pymongo.errors import WriteError
from pymongo.collection import ObjectId

from saana_lib.abstract import OutIn
from saana_lib.connectMongo import db
from constants import constants_wrapper as constants
from saana_lib.patient import MinimizeIngredients, AvoidIngredients, \
    PrioritizeIngredients
from saana_lib.score import PrioritizedScore, MinimizedScore, NutrientScore


logger = logging.getLogger(__name__)


class Recommendation:
    ingredients_class = None
    recommendation_type = 'min'

    def __init__(self, patient_id_str):
        self.patient_id = ObjectId(patient_id_str)
        self._tags = None
        self._restrictions = None

    def get_or_create_ingredient(self, name):
        ingredient = db.mst_food_ingredients.find_one({'name': name})
        if ingredient:
            _id = ingredient['_id']
        else:
            res = db.mst_food_ingredients.insert_one({
                'name': name,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
            })
            _id = res.inserted_id
        return _id

    def recommendation_frame(self, ingredient_name, ingredient_quantity=0):
        return {
            'patient_id': self.patient_id,
            'ingredient_id': self.get_or_create_ingredient(ingredient_name),
            'type': self.recommendation_type,
            'quantity': ingredient_quantity,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }

    @property
    def _all(self):
        for name, quantity in self.ingredients_class.all.items():
            yield self.recommendation_frame(name, quantity)

    def as_list(self):
        return list(self._all)

    def to_db(self):
        """
        Write all the recommendations of the given type to the DB.
        Although no exception should be raised, handling is done
        at the high level, so any WriteError will be caught.
        :return: the count of the recommendations successfully
        inserted
        """
        inserted_count = 0
        for recommendation in self._all:
            try:
                insert_result = db.patient_ingredient_recommendation.insert_one(
                    recommendation
                )

                if insert_result.inserted_id:
                    inserted_count += 1

            except WriteError as exc_details:
                logger.error(exc_details)

        return inserted_count


class MinimizeRecommendation(Recommendation):
    ingredients_class = MinimizeIngredients
    recommendation_type = 'min'


class PrioritizeRecommendation(Recommendation):
    ingredients_class = PrioritizeIngredients
    recommendation_type = 'prior'


class AvoidRecommendation(Recommendation):
    ingredients_class = AvoidIngredients
    recommendation_type = 'avoid'

    @property
    def _all(self):
        for name in self.ingredients_class.all:
            yield self.recommendation_frame(name)


class AllRecommendations(OutIn):

    def __init__(self, patient_id_str):
        self.patient_id = patient_id_str

    def sequence(self):
        """
        :return: the concatenation of the 3 lists
        """
        return MinimizeRecommendation(self.patient_id).as_list() + \
               PrioritizeRecommendation(self.patient_id).as_list() + \
               AvoidRecommendation(self.patient_id).as_list()

    def store(self):
        """
        :return: the sum of the counter of the record being written
        """
        return MinimizeRecommendation(self.patient_id).to_db() + \
               PrioritizeRecommendation(self.patient_id).to_db() + \
               AvoidRecommendation(self.patient_id).to_db()


"""
PATIENT_RECIPE_RECOMMENDATION

patient_id: {type: MongooseSchema.ObjectId, ref: 'Patient', required: true}
recipe_id: {type: MongooseSchema.ObjectId, ref: 'mst_recipe'}
score: {type: Number}
is_like: {type: Boolean, default: true}
created_at: {type: Date}
updated_at: {type: Date}
"""
class RecipeRecommendation:

    def __init__(self, recipe, patient_id, recipe_id=None):
        self.__recipe_id = recipe_id
        self.recipe = recipe
        self.__patient_id = patient_id
        self._score = constants.DEFAULT_RECOMMENDATION_SCORE

    @property
    def today(self):
        return datetime.now()

    def recommendations_in_time_frame(self, start, end=None):
        """
        :return: the recommendations being returned in
        """
        if not end:
            end = start - timedelta(days=7)
        return list(
            o['recipe_id'] for o in db.patient_recipe_recommendation.find(
                {'patient_id': self.__patient_id,
                 'created_at': {"$lte": start, "$gte": end}
                 }, {'recipe_id': 1, '_id': 0}
            )
        )

    def repetition_deduct_points(self, last_time):
        """
        Formula is: 40 - (# of weeks since it was recommended * 10)
        3 weeks ago == -10
        2 weeks ago == -20
        1 weeks ago == -30
        """
        weeks = (self.today.isocalendar()[1] - last_time.isocalendar()[1])
        return 40 - (weeks * 10) if weeks <= 3 else 0

    def deduct_avoid(self):
        return len(AvoidIngredients(self.__patient_id).all) * constants.DEDUCT_AVOID

    @property
    def score(self):
        val = constants.DEFAULT_RECOMMENDATION_SCORE
        val -= self.deduct_avoid()
        val -= MinimizedScore(self.__recipe_id, self.__patient_id).value
        val += PrioritizedScore(self.__recipe_id, self.__patient_id).value
        val += NutrientScore(self.__recipe_id, self.__patient_id).value
        return val
