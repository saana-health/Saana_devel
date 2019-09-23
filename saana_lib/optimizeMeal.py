import itertools
import csv
import os
import sys
from datetime import date, timedelta, datetime

from . import model, connectMongo, utils, chemo, feedback
from saana_lib.manual_input import manual_input
from constants import constants_wrapper as constants
from saana_lib.utils import csv_writer


DEDUCT_AVOID = -60
DEDUCT_GR_MIN2 = -60
DEDUCT_LT_MIN2 = -30
DEDUCT_LT_MIN1 = -15
DEDUCT_LT_MIN1_VEESTRO = - 20

# REPEAT
REPEAT_ZERO = -50
REPEAT_ONE = -30
REPEAT_TWO = -15
REPEAT_CUM = - 5

# PLUS
ADD_PRIOR = 10

LIKED_MEAL = 10

try:
    os.remove('masterOrder/masterorder.csv')
except:
    pass

TEST = True

TODAY = utils.find_tuesday(date.today(),2)

class Optimizer:

    def __init__(self, test = True):
        self.today = datetime.combine(TODAY,datetime.min.time())
        # check today is tuesday
        assert self.today.weekday() == 1
        self.test = test
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

    def _check_subscription(self, patient_id):
        '''
        Checks subscription status

        :param patient_id: ObjectId()
        :return: True / False
        '''
        if self.test:
            return True

        patient_subscription = connectMongo.db.patient_subscriptions.find_one({'patient_id':patient_id})
        # No subscription
        if patient_subscription is None:
            return False

        # Inactive status
        if patient_subscription['status'] != 'active':
            return False

        # Weekly order
        if connectMongo.db.mst_subscriptions.find_one({'_id':patient_subscription['subscription_id']})['interval_count']\
            == 1:
            return True

        # order if not ordered last week
        order_lastWeek = connectMongo.db.orders.find_one({'patient_id':patient_id, 'week_start_date':self.today + timedelta(weeks=-1)})
        if order_lastWeek is None:
           return True
        else:
            return False

    def optimize(self):
        '''
        optimize -> get_sscre_board -> choose_meal -> to_mongo & write_csv
        :return:
        '''
        for patient in self.patients:
            try:
                # plan either 7 or 15
                num_meal = connectMongo.get_subscription(patient._id)

                ## deprecated
                # patient.next_order = connectMongo.get_next_order(patient._id)

                today = self.today
                start_date = today

                print('Processing   {}  on {}!'.format(patient.name,str(today)))

                score_board = {}

                # get all tags
                tag_ids = patient.symptoms + patient.disease + patient.treatment_drugs + patient.comorbidities
                tags = list(connectMongo.db.tags.find({'tag_id':{'$in':tag_ids}}))
                print('tags:', tag_ids)

                # prepare tags
                minimizes = {}
                priors = {}
                multiplier = []
                symptoms_progress = feedback.get_lateset_symptoms(patient._id)
                for tag in tags:
                    minimizes.update(tag['minimize'])
                    priors.update(tag['prior'])
                    if tag['tag_id'] in symptoms_progress['worsen']:
                        multiplier += list(tag['minimize'].keys())+list(tag['prior'].keys())


                avoids = list(set(itertools.chain(*[utils.tag_dict_to_class(tag).avoid for tag in tags])))

                ## Get scoreboard ##
                score_board, repeat_one_week = self.get_score_board(patient, minimizes, avoids, priors, list(set(multiplier)))
                self.scoreboard_to_csv_rows(score_board, patient._id)

                ## Start choosing meals ##
                slots, supplierIds = self.choose_meal(score_board, repeat_one_week)
                assert len(slots) == 15
                slots = self.reorder_slots(slots)

                # Save the result to csv and update on mongo
                if num_meal> 8:
                    end_date = utils.find_tuesday(start_date,2)
                else:
                    end_date = utils.find_tuesday(start_date,3)

                slots = chemo.reorder_chemo(slots, patient._id, start_date, end_date, score_board, supplierIds)
                self.to_mongo(slots, patient._id,start_date,end_date)
                self.write_csv(slots,patient._id,start_date,end_date)
                print('Finished processing   {}'.format(patient.name,str(today)))

            except:
                print('Error while generating meals for {}'.format(patient.name))

    def compute_minimize_score(self, current, minimize_elements, meal_info):
        minimize_list = list()
        for item_name, min_item in minimize_elements.items():
            item_name = item_name.lower()
            if item_name in meal_info:
                multiplier_factor = 1

                # If a unit is included in the value, get rid of it
                if not isinstance(meal_info[item_name], (float,)) and \
                        not isinstance(meal_info[item_name], int):
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

    def get_score_board(self, patient, minimizes, avoids, priors, multiplier):
        '''
        create a scoring system based on minimize, avoid and prior tags

        :param patient: Patient()
        :param minimizes: {str: {min1: str(int), min2: str(int)} }
        :param avoids: [ str ]
        :param priors: { str: int}
        :return: {int : [{'prior':[str], 'minimizes': [str]. 'avoids': [str], 'meal': Meal()]}, [Meal()]
        '''
        print("Started generating score card")
        # get meals from one, two weeks ago to check repetition: repeat_one if one week ago, repeat_two is two weeks ago
        repeat_one_week, repeat_two_week= self._repeating_meals(patient._id,self.today)
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

                    # TODO #2: since we are using MongoDB, we can play around with dictionaries
                    # as long as we want, so instead of saving nutrition fact quantities
                    # as strings, they might be saved in this form:
                    # {'quantity': float, 'unit': [mcg, gr, ...whatever]}, so that we don't
                    # have to retrieve data using awkward method (like split + indexing)
                    if (nutrition in elem_name or elem_name in nutrition) and \
                            elem_quantity <= float(meal.nutrition[nutrition].split(' ')[0]):
                                prior_list.append(elem_name)

            # ADD points for priors
            pos = len(prior_list)
            score += pos*ADD_PRIOR

            ## REPETITION
            # check repetition. deduct for every repetition of meal
            for repeat_meal in repeat_one_week:
                if meal == repeat_meal:
                    score += REPEAT_ONE
            for repeat_meal in repeat_two_week:
                if meal == repeat_meal:
                    score += REPEAT_TWO

            # update the score_board
            if score not in score_board.keys():
                score_board[score] = [{'meal': meal,'prior':prior_list,'minimize':minimize_list, 'avoid':avoid_list}]
            else:
                score_board[score].append({'meal': meal,'prior':prior_list,'minimize':minimize_list, 'avoid':avoid_list})

        return score_board, repeat_one_week

    def choose_meal(self,score_board,repeat_one_week):
        '''
        Choosing meals
        :param score_board:  {int : [{'prior':[str], 'minimizes': [str]. 'avoids': [str], 'meal': Meal()]}
        :param repeat_one_week: [Meal()]
        :return: [Meal()]
        '''

        # list for saving meals
        num_repeat = 0
        bucket = {}
        suppliers = list(connectMongo.db.users.find({'role':'supplier'}))

        # manual matching suppliers with their ID (ObjectId)
        Veestro = [obj['_id'] for obj in suppliers if obj['first_name'] == 'Veestro'][0]
        Euphebe = [obj['_id'] for obj in suppliers if obj['first_name'] == 'Euphebe'][0]
        FoodNerd = [obj['_id'] for obj in suppliers if obj['first_name'] == 'FoodNerd'][0]
        FrozenGarden = [obj['_id'] for obj in suppliers if obj['first_name'] == 'FrozenGarden'][0]

        for supplier in [x['_id'] for x in suppliers]:
            bucket[supplier] = []
        restart = False
        num_meal = 15
        five_meal_supplier = None
        ten_meal_supplier = None

        while True:

            # Check if two suppliers can be chosen
            if len(bucket[Veestro]) == 15:
                five_meal_supplier = Veestro
                ten_meal_supplier = Veestro
                slots = bucket[Veestro]
                break
            if five_meal_supplier is None:
                if len(bucket[FoodNerd]) == 5:
                    five_meal_supplier = FoodNerd
                elif len(bucket[FrozenGarden]) == 5:
                    five_meal_supplier = FrozenGarden
            if ten_meal_supplier is None:
                if len(bucket[Veestro]) == 10:
                    ten_meal_supplier = Veestro
                elif len(bucket[Euphebe]) == 10:
                    ten_meal_supplier = Euphebe
            if None not in [five_meal_supplier, ten_meal_supplier]:
                slots = bucket[five_meal_supplier][:5] + bucket[ten_meal_supplier][:10]
                break

            sorted_scores = sorted(score_board.keys(), reverse=True)
            for score in sorted_scores:

                if restart:
                    restart = False
                    break

                for meal in score_board[score]:

                    supplier = meal['meal'].supplier_id
                    if 'breakfast' in meal['meal'].type:
                        continue
                    try:
                        bucket[supplier].append(meal)
                    except:
                        pdb.set_trace()

                    # Update score board for meal just selected
                    score_board[score].remove(meal)
                    new_score = score + REPEAT_ZERO
                    if new_score in score_board.keys():
                        score_board[new_score].append(meal)
                    else:
                        score_board[new_score] = [meal]

                    # Update score board2 - penalize more as more repetition
                    if meal['meal'] in repeat_one_week:
                        num_repeat += 1
                        for score_ in sorted_scores:
                            for repeat in repeat_one_week:
                                for each_meal in score_board[score_]:
                                    if each_meal['meal'] == repeat:
                                        score_board[score_].remove(each_meal)
                                        deduct_pnt = REPEAT_CUM*num_repeat
                                        if score_ + deduct_pnt in score_board.keys():
                                            score_board[score_ + deduct_pnt].append(each_meal)
                                        else:
                                            score_board[score_ + deduct_pnt] = [each_meal]


                    restart = True
                    break

        # slots filled up
        assert len(slots) == num_meal

        ## OPTIONAL - how many repetition from past 2 weeks?
        repeat_cnt = 0
        repeat_same_week = {}
        for each in slots:
            if repeat_one_week is not None and each['meal'] in repeat_one_week:
                repeat_cnt += 1
            if each['meal'].name in repeat_same_week.keys():
                repeat_same_week[each['meal'].name] += 1
            else:
                repeat_same_week[each['meal'].name] = 1
        # print('{} repetitions from last week'.format(repeat_cnt))


        return slots, [five_meal_supplier, ten_meal_supplier]

    def _repeating_meals(self,patient_id,start_date):
        '''
        Check previously ordered meals

        :param patient_id: ObjectId()
        :param start_date: datetime.datetime()
        :return: [Meal()] or None, [Meal()] or None
        '''
        # prev_order = connectMongo.get_order(patient_id,start_date + timedelta(weeks=-1))
        prev_order = connectMongo.db.orders.find_one({'patient_id':patient_id, 'week_start_date': start_date + timedelta(weeks=-1)})
        prev_two_order = connectMongo.db.orders.find_one({'patient_id':patient_id, 'week_start_date': start_date + timedelta(weeks=-2)})

        if prev_order is not None:
            # for catching errors
            try:
                prev_order = [self.meals[x] for x in prev_order['patient_meal_id']]
            except:
                pdb.set_trace()
        else:
            prev_order = []

        if prev_two_order is not None:
            prev_two_order = [self.meals[x] for x in prev_two_order['patient_meal_id']]
        else:
            prev_two_order = []

        return prev_order, prev_two_order

    def reorder_slots(self,slots):
        '''
        reorder based on calories
        :param slots:[Meal()]
        :return: [Meal()]
        '''
        #sort by calories
        slots = sorted(slots, key = lambda meal: float(meal['meal'].nutrition['cals'].split(' ')[0]),reverse=True)
        high_cal = slots[:7]
        low_cal = slots[8:]
        new_slots = []
        for high,low in zip(high_cal,low_cal[::-1]):
            new_slots.append(high)
            new_slots.append(low)
        new_slots.append(slots[7])
        return new_slots

    def to_mongo(self, mealinfo, patient_id,start_date,end_date):
        patient_meal_id = []
        for meal in mealinfo:
            patient_meal = model.Patient_meal(patient_id, meal['meal']._id, 'pending', datetime.today())
            return_id = connectMongo.db.patient_meals.insert_one(patient_meal.class_to_dict()).inserted_id
            patient_meal_id.append(return_id)
        new_order = model.Order(patient_id = patient_id,patient_meal_id = patient_meal_id,\
                          week_start_date=start_date, week_end_date=end_date)
        connectMongo.db.orders.insert_one(new_order.class_to_dict())
        return True

    def write_csv(self,slots,patient_id,start_date,end_date):
        try:
            existing_order = list(csv.reader(open('masterOrder/masterorder.csv','r')))
        except:
            existing_order = [['Patient_ID','Patient_name','date','meal_name','minimize','prior','avoid','supplier_id','supplier_name']]
        for index in range(len(slots)):
            meal = slots[index]
            user = connectMongo.db.users.find_one({'_id':connectMongo.db.patients.find_one({'_id':patient_id})['user_id']})
            patient_name = user['first_name'] + ' ' + user['last_name']
            supplier_name = connectMongo.db.users.find_one({'_id': meal['meal'].supplier_id})['first_name']

            row = [str(patient_id), patient_name, str(start_date.date()+timedelta(days=index)), meal['meal'].name,\
                   meal['minimize'], meal['prior'], meal['avoid'], meal['meal'].supplier_id, supplier_name]
            existing_order.append(row)
        with open('masterOrder/masterorder.csv','w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(existing_order)
        print("Successfully generated orders to a csv file")

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



if __name__ == "__main__":

    ## CAUTION: ALWAYS ADD NUMBERS IN CODE AS THEIR VALUES ARE NEGATIVES
    # MINUS

    op = Optimizer()
    op.optimize(TEST)


