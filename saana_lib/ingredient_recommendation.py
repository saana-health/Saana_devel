import logging
from datetime import datetime

from pymongo.errors import WriteError
from pymongo.collection import ObjectId

from saana_lib.connectMongo import db
from saana_lib.patient import MinimizeIngredients, AvoidIngredients, \
    PrioritizeIngredients


logger = logging.getLogger(__name__)


class Recommendation:
    ingredients_class = None
    recommendation_type = 'min'

    def __init__(self, patient_id_str):
        self.patient_id_str = patient_id_str
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
            'patient_id': ObjectId(self.patient_id_str),
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


class AllRecommendations:

    def __init__(self, patient_id_str):
        self.patient_id = patient_id_str

    def read(self):
        """
        :return: the concatenation of the 3 lists
        """
        return MinimizeRecommendation(self.patient_id).as_list() + \
               PrioritizeRecommendation(self.patient_id).as_list() + \
               AvoidRecommendation(self.patient_id).as_list()

    def write(self):
        """
        :return: the sum of the counter of the record being written
        """
        return MinimizeRecommendation(self.patient_id).to_db() + \
               PrioritizeRecommendation(self.patient_id).to_db() + \
               AvoidRecommendation(self.patient_id).to_db()
