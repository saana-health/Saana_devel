from logging import getLogger
import itertools
import csv
from datetime import datetime
from pymongo.errors import PyMongoError

from . import model, connectMongo, utils
from saana_lib.manual_input import manual_input


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
        self.today = datetime.now().today()
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
        # TODO: optimize the for loop. Remove `if emails ...` and let patients
        # property to return only patients filtered by emails.

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
                self.scoreboard_to_csv(score_board, patient._id)

            except PyMongoError:
                logger.error('Error while generating meals for {}'.format(patient.name))

    def get_score_board(self, patient, minimizes: dict, avoids: list, priors: dict):
        """
        create a scoring system based on minimize, avoid and prior tags
        :param patient: Patient()
        :param minimizes: {str: {min1: str(int), min2: str(int)} }
        :param avoids: [ str ]
        :param priors: { str: int}
        :return: {int : [{'prior':[str], 'minimizes': [str]. 'avoids': [str],
        'meal': Meal()]}, [Meal()]

        # TODO: quantity
        if meal.quantity == 0:
        continue
        """
        logger.info("Started generating score card")
        score_board = {}

        for meal in self.meals:
            if self.suppliers and meal.supplier_id not in self.suppliers:
                continue

            score = 100
            avoid_list = []
            minimize_list = []
            prior_list = []

            # TODO: is it correct that this loop exits after the first match ?
            for each in list(meal.nutrition.keys()) + list(meal.ingredients.keys()):
                if each in avoids:
                    avoid_list.append(each)
                    score += DEDUCT_AVOID
                    break

            ## MINIMIZE ##
            full_meal_info = {}
            full_meal_info.update(meal.ingredients)
            full_meal_info.update(meal.nutrition)

            # minimizes: list of all ingredients+nutrition to minimize from tags
            # full_meal_info: from meal info
            for min_item in minimizes:

                for ing in full_meal_info:
                    # if matched
                    if min_item in ing:
                        multiplier_factor = 1

                        # If a unit is included in the value, get rid of it
                        if not isinstance(full_meal_info[ing],(float,)) and not isinstance(full_meal_info[ing],int):
                            contain_val = float(full_meal_info[ing].split(' ')[0])
                        else:
                            contain_val = float(full_meal_info[ing])

                        if contain_val > float(minimizes[min_item]['min2']):
                            score += DEDUCT_GR_MIN2*multiplier_factor
                            minimize_list.append(min_item)
                        elif contain_val > float(minimizes[min_item]['min1']):
                            score += DEDUCT_LT_MIN2*multiplier_factor
                            minimize_list.append(min_item)
                        elif contain_val <= float(minimizes[min_item]['min1']):
                            pass
                            # Do we deduct points for {value} < min1 ? No
                            # if meal.supplier_id == connectMongo.db.users.find_one({'first_name':'Veestro'})['_id']:
                            #     score += DEDUCT_LT_MIN1_VEESTRO*multiplier_factor
                            # else:
                            #     score += DEDUCT_LT_MIN1*multiplier_factor
                        # This should never happen
                        else:
                            print('ERR')
                            raise ValueError

            ## PRIORITIZE
            for prior in priors:
                # if 1) string matched 2) not in min or avoid list and 3) content value above threshold
                for ingredient in meal.ingredients.keys():
                    if prior in ingredient and prior not in minimize_list + avoid_list and priors[prior] <= float(meal.ingredients[ingredient]):
                        prior_list.append(prior)

                for nutrition in meal.nutrition.keys():
                    if (nutrition in prior or prior in nutrition) and prior not in minimize_list + avoid_list and priors[prior] <= float(meal.nutrition[nutrition].split(' ')[0]):
                        prior_list.append(prior)

            # TODO: why this line ?
            prior_list = list(set(prior_list))

            # ADD points for priors
            pos = len(prior_list)
            score += pos*ADD_PRIOR

            if score not in score_board.keys():
                score_board[score] = []
            score_board[score].append({
                'meal': meal,
                'prior': prior_list,
                'minimize': minimize_list,
                'avoid': avoid_list
            })

        return score_board

    def scoreboard_to_csv(self, score_board, patient_id):
        """
        Save score_board to csv
        :param score_board: {int : [
        {'prior':[str], 'minimizes': [str]. 'avoids': [str], 'meal': Meal()]},
        :param patient_id: ObjectId()
        :return: True
        """
        sorted_score = sorted(score_board.keys(),reverse = True)
        csv_list = [[patient_id],['score','meal','minimize','prior','avoid','supplier_id','supplier_name']]
        user = connectMongo.db.users.find_one({'_id':connectMongo.db.patients.find_one({'_id':patient_id})['user_id']})
        patient_name = user['first_name'] + '.' + user['last_name']
        for score in sorted_score:
            for meal in score_board[score]:
                supplier_name = connectMongo.db.users.find_one({'_id': meal['meal'].supplier_id})['first_name']
                temp_list = [score]
                temp_list += [meal['meal'],meal['minimize'],meal['prior'], meal['avoid'],meal['meal'].supplier_id,supplier_name]
                csv_list.append(temp_list)
        with open('scoreboard/scoreboard_'+str(patient_name)+'_'+str(self.today)+'.csv','w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_list)
        print("Successfully wrote score card to a csv file")
        return True


if __name__ == "__main__":

    ## CAUTION: ALWAYS ADD NUMBERS IN CODE AS THEIR VALUES ARE NEGATIVES
    # MINUS
    op = Optimizer()
    op.optimize()

