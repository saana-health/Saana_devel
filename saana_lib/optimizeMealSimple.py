from logging import getLogger
import itertools
from datetime import datetime
from pymongo.errors import PyMongoError

from . import model, connectMongo, utils
from saana_lib.manual_input import manual_input
from constants import constants_wrapper as constants
from saana_lib.utils import csv_writer


logger = getLogger(__name__)

# Deductions
DEDUCT_AVOID = -60
DEDUCT_GR_MIN2 = -60
DEDUCT_LT_MIN2 = -30
DEDUCT_LT_MIN1 = -15
DEDUCT_LT_MIN1_VEESTRO = - 20

# Additions
ADD_PRIOR = 10
LIKED_MEAL = 10


class Optimizer:

    def __init__(self, test=True):
        self.test = test
        self.today = datetime.now()
        self.db_client = connectMongo
        self.suppliers, self.patients_emails = manual_input('suppliers.csv')

    def get_ingredient_name(self, ingredient_id):
        ing = connectMongo.db.mst_food_ingredients.find_one({'_id': ingredient_id})
        return ing['name'] if ing else ''

    @property
    def meals(self):
        """
        TODO: fix inner loop (has no sense). Making N queries to retrieve
        only one information (the name) that might be already stored
        inside the meal dict

        NOTE:
        If an ingredient is not found then it should not be added to
        :return: a list of Meal object
        """
        meals_list = list()
        for meal in connectMongo.db.meal_infos.find():
            ingredients = {}
            for ingredient in meal['ingredients']:
                name = self.get_ingredient_name(ingredient['food_ingredient_id'])
                if name:
                    ingredients[name] = ingredient['quantity']

            meal['ingredients'] = ingredients
            new_meal = model.Meal()
            new_meal.dict_to_class(meal)
            meals_list.append(new_meal)
        return meals_list

    @property
    def tags(self):
        hash_tag = {}
        for tag in connectMongo.db.tags.find():
            new_tag = model.Tag()
            new_tag.dict_to_class(tag)
            hash_tag[tag['_id']] = new_tag
        return hash_tag

    def get_patient_related_data(self, patient_id):
        comorbidities = self.db_client.get_comorbidities(patient_id)
        disease = self.db_client.get_disease(patient_id)
        symptoms = self.db_client.get_symptoms(patient_id)
        drugs = self.db_client.get_drugs(patient_id)
        return comorbidities, disease, symptoms, drugs

    @property
    def patients(self):
        """
        TODO: optimize the for loop. Remove `if emails ...` and let patients
        property to return only patients filtered by emails.

        if selecting patients based on emails read in from manual file
        if no emails are specified -> run on all patients
        :return:
        """
        patients_list = []
        patients = connectMongo.db.patients.find()
        users = connectMongo.db.users
        for patient in patients:
            if self.patients_emails and \
                    users.find_one({'_id': patient['user_id']})['email'] not in self.patients_emails:
                continue

            comorbidities, disease, symptoms, drugs = self.get_patient_related_data(patient['_id'])
            user_id = connectMongo.db.patients.find_one({'_id':patient['_id']})['user_id']
            name = connectMongo.db.users.find_one({'_id':user_id})['first_name']

            new_patient = model.Patient(
                name=name,
                comorbidities=comorbidities,
                disease=disease,
                _id = patient['_id'],
                symptoms=symptoms,
                treatment_drugs=drugs
            )
            patients_list.append(new_patient)

        return patients_list

    def optimize(self):
        """
        optimize -> get_score_board -> choose_meal -> to_mongo & write_csv
        :return:
        """
        logger.info("Starting optimization")
        for patient in self.patients:
            try:
                tag_ids = patient.symptoms + \
                          patient.disease + \
                          patient.treatment_drugs + \
                          patient.comorbidities

                tags = list(connectMongo.db.tags.find({'tag_id': {'$in': tag_ids}}))
                minimizes = {}
                priors = {}
                multiplier = []
                for tag in tags:
                    minimizes.update(tag['minimize'])
                    priors.update(tag['prior'])

                avoids = list(
                    set(itertools.chain(*[utils.tag_dict_to_class(tag).avoid for tag in tags]))
                )

                score_board = self.get_score_board(patient, minimizes, avoids, priors)

                patient_name, csv_list = self.scoreboard_to_csv_rows(score_board, patient._id)
                filename = constants.SCOREBOARD_CSV_FILE_NAME_PATTERN.format(
                    constants.SCOREBOARD_FOLDER,
                    patient_name,
                    self.today
                )

                csv_writer(filename, csv_list)

            except PyMongoError:
                logger.error('Error while generating meals for {}'.format(patient.name))

    def compute_minimize_score(self, current, minimize_elements, meal_info):
        minimize_list = list()
        for item_name, min_item in minimize_elements.items():
            item_name = item_name.lower()
            if item_name in meal_info:
                multiplier_factor = 1

                # If a unit is included in the value, get rid of it
                if not isinstance(meal_info[item_name], (float,)) and not isinstance(meal_info[item_name], int):
                    contain_val = float(meal_info[item_name].split(' ')[0])
                else:
                    contain_val = float(meal_info[item_name])

                if contain_val > float(min_item['min2']):
                    current += DEDUCT_GR_MIN2 * multiplier_factor
                    minimize_list.append(item_name)
                elif contain_val > float(min_item['min1']):
                    current += DEDUCT_LT_MIN2 * multiplier_factor
                    minimize_list.append(item_name)
                elif contain_val <= float(min_item['min1']):
                    pass
                    # Do we deduct points for {value} < min1 ? No
                    # if meal.supplier_id == connectMongo.db.users.find_one({'first_name':'Veestro'})['_id']:
                    #     score += DEDUCT_LT_MIN1_VEESTRO*multiplier_factor
                    # else:
                    #     score += DEDUCT_LT_MIN1*multiplier_factor
                # This should never happen
                else:
                    raise ValueError("")

        return current, minimize_list

    def get_score_board(self, patient, minimizes: dict, avoids: list, priors: dict):
        """
        create a scoring system based on minimize, avoid and prior tags
        :return: {int : [{'prior':[str], 'minimizes': [str]. 'avoids': [str],
        'meal': Meal()]}, [Meal()]

        # TODO: quantity
        if meal.quantity == 0:
        continue
        """
        logger.info("Started generating score card")
        score_board = dict()

        for meal in self.meals:
            if self.suppliers and meal.supplier_id not in self.suppliers:
                continue

            score = 100
            avoid_list = list()
            prior_list = list()

            # TODO: is it correct that this loop exits after the first match ?
            for each in list(meal.nutrition.keys()) + list(meal.ingredients.keys()):
                if each in avoids:
                    avoid_list.append(each)
                    score += DEDUCT_AVOID
                    break

            full_meal_info = {}
            full_meal_info.update(meal.ingredients)
            full_meal_info.update(meal.nutrition)

            score, minimize_list = self.compute_minimize_score(score, minimizes, full_meal_info)
            for elem_name in priors:
                if elem_name in minimize_list + avoid_list:
                    continue

                elem_quantity = priors[elem_name]
                if elem_name in meal.ingredients and \
                        elem_quantity <= float(meal.ingredients[elem_name]):
                    prior_list.append(elem_name)

                for nutrition in meal.nutrition.keys():
                    # TODO #1: this behavior should be fixed. either is A IN B
                    # or B in A. Usually one of the two information comes from the
                    # database, so it can be considered safe

                    # TODO #2: since we are using MongoDB, we can around with dictionaries
                    # as long as we want, so instead of saving nutrition fact quantities
                    # as strings, they might be saved in this form:
                    # {'quantity': float, 'unit': [mcg, gr, ...whatever]}, so that we don't
                    # have to retrieve data using awkward method (like split + indexing)
                    if (nutrition in elem_name or elem_name in nutrition) and \
                            elem_quantity <= float(meal.nutrition[nutrition].split(' ')[0]):
                                prior_list.append(elem_name)

            # TODO: why this line ? to avoid duplicates ?
            prior_list = list(set(prior_list))
            score += len(prior_list) * ADD_PRIOR

            if score not in score_board.keys():
                score_board[score] = list()

            score_board[score].append({
                'meal': meal,
                'prior': prior_list,
                'minimize': minimize_list,
                'avoid': avoid_list
            })

        return score_board

    def scoreboard_to_csv_rows(self, score_board, patient_id):
        """
        TODO: move CSV headers to a constants
        """
        sorted_score = sorted(score_board.keys(), reverse=True)
        csv_list = [[patient_id, 'score', 'meal', 'minimize', 'prior', 'avoid', 'supplier_id','supplier_name'], ]
        user = connectMongo.db.users.find_one({
            '_id':connectMongo.db.patients.find_one({'_id':patient_id})['user_id']
        })
        patient_name = "{}.{}".format(user['first_name'], user['last_name'])
        for score in sorted_score:
            for meal in score_board[score]:
                supplier_name = connectMongo.db.users.find_one({'_id': meal['meal'].supplier_id})['first_name']
                csv_list.append([
                    score,
                    meal['meal'].name,
                    ":".join(meal['minimize']),
                    ":".join(meal['prior']),
                    ":".join(meal['avoid']),
                    meal['meal'].supplier_id,
                    supplier_name
                ])

        return patient_name, csv_list

