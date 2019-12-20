from logging import getLogger
from collections import OrderedDict
from datetime import datetime
from pymongo.collection import ObjectId

from constants import constants_wrapper as constants
from saana_lib.abstract import OutIn
from saana_lib.connectMongo import db
from saana_lib.recommendation import RecipeRecommendation, AllRecommendations
from saana_lib.utils import out_to_xls
import datetime

logger = getLogger(__name__)


class Ranking:

    def __init__(self, patient_id):
        self.patient_id = patient_id
        if not isinstance(patient_id, ObjectId):
            self.patient_id = ObjectId(patient_id)
        self.today = datetime.utcnow()

    def compute(self, descending=True):
        _ranking = dict()
        for recipe in db.mst_recipes.find():
            recommendation = RecipeRecommendation(recipe, self.patient_id)
            score = recommendation.score
            if score not in _ranking:
                _ranking[score] = list()
            _ranking[score].append(recommendation)
        return OrderedDict(
            (k, v) for k, v in sorted(_ranking.items(), reverse=descending)
        )


class RankingOut(OutIn):
    """"""

    def __init__(self, patient_id):
        self.patient_id = ObjectId(patient_id)

    def store(self, limit=constants.RECIPES_TO_RANK):
        counter = 0
        print('Test')
        _ranking = Ranking(self.patient_id).compute()
        print (_ranking)
        recipes_all = []
        for score, recipes in _ranking.items():
            if counter == limit:
                break

            for recipe_recommendation in recipes:
                print (recipe_recommendation)
                recipes_all.append(recipe_recommendation.recipe_format) #recipe in array
                counter += 1

        patient_rec = {
            'patient_id': self.patient_id,
            'recipe': recipes_all,
            'is_deleted': False,
            'created_at': datetime.utcnow().isoformat().strftime('%Y-%m-%d %H:%M:%SZ'),
            'updated_at': datetime.utcnow().isoformat().strftime('%Y-%m-%d %H:%M:%SZ')
            }
        self.proxy(patient_rec) #insert all recipes 

    def sequence(self):
        """TODO to implement"""


class RankingToDatabase(RankingOut):
    """"""

    def proxy(self, content):
        db.patient_recipe_recommendations.insert_one(content)
    

class RankingToFile(RankingOut):
    """"""
    headers = False
    filename = ""

    def write_headers(self):
        headers = ["Recipe ID", "Score"]
        out_to_xls(self.filename, headers)

    def proxy(self, content):
        self.filename = "{}-{}".format(
            self.patient_id.__str__(),
            datetime.utcnow().isoformat().strftime("%Y-%m-%d"),
        )
        if not self.headers:
            self.write_headers()
            self.headers = True

        out_to_xls(self.filename, [
            content.get('recipe_id'),
            "{}".format(content.get('score'))
        ])
