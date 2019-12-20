import logging
from datetime import datetime, timedelta

from pymongo.errors import WriteError
from pymongo.collection import ObjectId

from saana_lib.abstract import OutIn
from saana_lib.connectMongo import db
from constants import constants_wrapper as constants
from saana_lib.patient import MinimizeIngredients, AvoidIngredients, \
    PrioritizeIngredients
from saana_lib.score import PrioritizedScore, MinimizedScore, AvoidScore, \
    NutrientScore


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
        #need to find name that resemble not exact name
        #need to store tag name in ingredient recommend.

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
            'ingredient_name': ingredient_name,
            #'ingredient_id': self.get_or_create_ingredient(ingredient_name),
            'type': self.recommendation_type,
            'quantity': ingredient_quantity,
            'language': 'en',
            'is_deleted': False,
            #'created_at': datetime.now().isoformat(),
            'created_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')
            'updated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')
        }

    @property
    def _all(self):
        for name, quantity in self.ingredients_class(self.patient_id).all.items():
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
                insert_result = db.patient_ingredient_recommendations.insert_one(
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
        for name in self.ingredients_class(self.patient_id).all:
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
is_deleted: {type: Boolean, default: false}

"""


class RecipeRecommendation:

    def __init__(self, recipe, patient_id, recipe_id=None):
        self.recipe = recipe
        self._patient_id = patient_id
        if recipe and not recipe_id:
            self._recipe_id = recipe['_id']
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
            o['recipe_id'] for o in db.patient_recipe_recommendations.find(
                {'patient_id': self._patient_id,
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

    @property
    def score(self):
        val = constants.DEFAULT_RECOMMENDATION_SCORE
        val += AvoidScore(self._recipe_id, self._patient_id).value
        val += MinimizedScore(self._recipe_id, self._patient_id).value
        val += PrioritizedScore(self._recipe_id, self._patient_id).value
#   TODO CHECK MST_NUTRIENTS
#        val += NutrientScore(self._recipe_id, self._patient_id).value

        return val

##    @property
##    def db_format(self):
##        return {
##            'patient_id': self._patient_id,
##            'recipes': self.recipes_all,
##            'created_date': datetime.now().isoformat(),
##            'updated_date': datetime.now().isoformat()
##        }

    @property
    def recipe_format(self):
        return {
            'recipe_id': self._recipe_id,
            'score': self.score,
            'is_deleted': False
            
        }
