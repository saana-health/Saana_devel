from logging import getLogger
from collections import OrderedDict
from datetime import datetime
from pymongo.collection import ObjectId

from constants import constants_wrapper as constants
from saana_lib.abstract import OutIn
from saana_lib.connectMongo import db
from saana_lib.recommendation import RecipeRecommendation
from saana_lib.utils import out_to_xls


logger = getLogger(__name__)


class Ranking:

    def __init__(self, patient_id):
        self.patient_id = patient_id
        if not isinstance(patient_id, ObjectId):
            self.patient_id = ObjectId(patient_id)
        self.today = datetime.now()

    def compute(self, descending=True):
        _ranking = dict()
        for recipe in db.mst_recipe.find():
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
        _ranking = Ranking(self.patient_id).compute()
        for score, recipes in _ranking.items():
            if counter == limit:
                break

            for recipe_recommendation in recipes:
                self.proxy(recipe_recommendation)
                counter += 1

    def sequence(self):
        """TODO to implement"""


class RankingToDatabase(RankingOut):
    """"""

    def proxy(self, content):
        db.patient_recipe_recommendation.insert_one(content.db_format)


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
            datetime.now().strftime("%Y-%m-%d"),
        )
        if not self.headers:
            self.write_headers()
            self.headers = True

        out_to_xls(self.filename, [
            content.get('recipe_id'),
            "{}".format(content.get('score'))
        ])
