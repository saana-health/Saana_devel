from pymongo import MongoClient
from bson.objectid import ObjectId
import pdb
import itertools
from model import Meal,Order, MealList, Patient
import csv
from connectMongo import add_order,get_all_meals, get_all_tags, get_all_patients, get_any, update_next_order,\
    get_order,get_subscription, get_next_order
from random import shuffle
import os
from utils import meal_dict_to_class, tag_dict_to_class, patient_dict_to_class, find_tuesday
import pprint
from datetime import date, timedelta, datetime
import time
DATE = time.ctime()[4:10].replace(' ','_')

class Optimizer:

    def __init__(self):
        self.meals = self._get_meals()
        self.tags = self._get_tags()
        self.inventory = self._check_inventory()
        self.patients = self._get_patients()
        self.today = datetime.combine(TODAY,datetime.min.time())

    #######CHANGED#########
    def _get_meals(self):
        '''

        :return: {_id: Meal()}
        '''
        hash_meal = {}
        # meals = [meal for meal in get_all_meals()]
        temp_meals= get_all_meals()
        meals = []
        for temp in temp_meals:
            ingredients = {}
            for ingredient in temp['ingredients']:
                name = get_any('mst_food_ingredients','_id',ingredient['food_ingredient_id'])['name']

                ingredients[name] = ingredient['quantity']
            temp['ingredients'] = ingredients
            meals.append(temp)
        for meal in meals:
            hash_meal[meal['_id']] = meal_dict_to_class(meal)
        return hash_meal

    def _get_tags(self):
        '''

        :return: {_id: Tag()}
        '''
        hash_tag = {}
        tags = [tag for tag in get_all_tags()]
        for tag in tags:
            hash_tag[tag['_id']] = tag_dict_to_class(tag)
        return hash_tag

    #######CHANGED#########
    def _get_patients(self):
        '''

        :return: [Patient()]
        '''
        patient_obj = []
        from connectMongo import get_comorbidities, get_drugs, get_symptoms, get_disease
        patients = get_all_patients()
        for patient in patients:
            #TODO: check subscription ()
            comorbidities = get_comorbidities(patient['_id'])
            disease = get_disease(patient['_id'])
            symptoms = get_symptoms(patient['_id'])
            drugs = get_drugs(patient['_id'])
            # pdb.set_trace()
            # PROBABLY ERROR HERE IN DEPLOYMENT
            name = 'Maggie'#patient['first_name']
            new_patient = Patient(name=name,comorbidities=comorbidities, disease=disease, _id = patient['_id'],\
                                  symptoms=symptoms, treatment_drugs=drugs)
            patient_obj.append(new_patient)

        return patient_obj



        # return [patient_dict_to_class(patient) for patient in get_all_patients()]
    ####################

    def _check_inventory(self):
        invent = {}
        for meal in self.meals.values():
            invent[meal.name] = 100

    def optimize(self, test = True):
        '''
        optimize -> get_sscre_board -> choose_meal -> to_mongo & write_csv
        :return:
        '''
        for patient in self.patients:
            patient.plan = get_subscription(patient._id)
            patient.next_order = get_next_order(patient._id)
            today = self.today
            start_date = today
            assert today.weekday() == 1
            num_meal = patient.plan
            if not test and patient.next_order != today:
                continue

            print('Processing   {}  on {}!'.format(patient.name,str(today)))
            score_board = {}

            # get all tags
            tag_ids = patient.symptoms+patient.disease+patient.treatment_drugs+patient.comorbidities
            tags = get_any('tags','_id',tag_ids)

            # prepare tags
            minimizes = {}
            priors = {}
            for tag in tags:
                minimizes.update(tag['minimize'])
            for tag in tags:
                priors.update(tag['prior'])

            avoids = list(set(itertools.chain(*[tag_dict_to_class(tag).avoid for tag in tags])))
            score_board, repeat_one_week = self.get_score_board(patient, minimizes, avoids, priors)

            ####### Start choosing meals ########
            # assert MEAL_PER_SUPPLIER_1 + MEAL_PER_SUPPLIER_2 == num_meal
            self.scoreboard_to_csv(score_board,patient._id)
            slots = self.choose_meal(score_board, repeat_one_week,num_meal)
            # pdb.set_trace()
            assert len(slots) == 15
            slots = self.reorder_slots(slots)
            if num_meal> 8:
                end_date = find_tuesday(start_date,2)
                self.to_mongo(slots,patient._id,start_date,end_date)
                self.write_csv(slots,patient._id,start_date,end_date)
                update_next_order(patient._id,find_tuesday(today,2))
            else:
                end_date = find_tuesday(start_date,3)
                self.to_mongo(slots, patient._id,start_date,end_date)
                self.write_csv(slots,patient._id,start_date,end_date)
                update_next_order(patient._id,find_tuesday(today,3))

    def get_score_board(self, patient, minimizes, avoids, priors):
        # get meals from one, two weeks ago to check repetition: repeat_one if one week ago, repeat_two is two weeks ago
        repeat_one_week, repeat_two_week= self._repeating_meals(patient._id,self.today)
        if repeat_one_week is None:
            repeat_one_week = []
        if repeat_two_week is None:
            repeat_two_week = []
        score_board = {}

        for meal in self.meals.values():
            score = 100
            # if meal.quantity == 0:
            #     continue

            ## AOVID
            avoid_list = []
            # should_avoid = False

            for each in list(meal.nutrition.keys()) + list(meal.ingredients.keys()):
                if each in avoids:
                    avoid_list.append(each)
                    score += DEDUCT_AVOID
                    break

            ## MINIMIZE
            minimize_list = []
            full_meal_info = {}
            full_meal_info.update(meal.ingredients)
            full_meal_info.update(meal.nutrition)

            for min_item in minimizes.keys():
                for ing in full_meal_info.keys():
                    if min_item in ing:

                        # If a unit is included in the value, get rid of it
                        if not isinstance(full_meal_info[ing],(float,)) and not isinstance(full_meal_info[ing],int):
                            contain_val = float(full_meal_info[ing].split(' ')[0])
                        else:
                            contain_val = float(full_meal_info[ing])

                        # if contain val above min 2
                        if contain_val > float(minimizes[min_item]['min2']):
                            score += DEDUCT_GR_MIN2
                        # if min1 < val < min2
                        elif contain_val > float(minimizes[min_item]['min1']):
                            score += DEDUCT_LT_MIN2
                        #if val < min1
                        elif contain_val < float(minimizes[min_item]['min1']):
                            score += DEDUCT_LT_MIN1
                        # This should never happen
                        else:
                            print('ERR')
                            raise ValueError
                        minimize_list.append(min_item)
            ## PRIORITIZE
            prior_list = []
            # prior_list = [{nutrition: meal.nutrition[nutrition]} for nutrition in meal.nutrition if nutrition in priors]
            for prior in priors.keys():
                for ingredient in meal.ingredients.keys():
                    if prior in ingredient and prior not in minimize_list + avoid_list and priors[prior] <= float(meal.ingredients[ingredient]):
                        prior_list.append(prior)
                for nutrition in meal.nutrition.keys():
                    if (nutrition in prior or prior in nutrition) and prior not in minimize_list + avoid_list and priors[prior] <= float(meal.nutrition[nutrition].split(' ')[0]):
                        prior_list.append(prior)

            prior_list = list(set(prior_list))

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

    def choose_meal(self,score_board,repeat_one_week, num_meal):
        # list for saving meals
        num_repeat = 0
        slots = []
        bucket = {'Euphebe':[], 'FoodNerd': [], 'FrozenGarden':[], 'Veestro':[]}
        restart = False
        num_meal = 15
        five_meal_supplier = None
        ten_meal_supplier = None

        while True:
            if len(bucket['Veestro']) == 15:
                slots = bucket['Veestro']
                break
            if five_meal_supplier is None:
                if len(bucket['FoodNerd']) == 5:
                    five_meal_supplier = 'FoodNerd'
                elif len(bucket['FrozenGarden']) == 5:
                    five_meal_supplier = 'FrozenGarden'
            if ten_meal_supplier is None:
                if len(bucket['Veestro']) == 10:
                    five_meal_supplier = 'Veestro'
                elif len(bucket['Euphebe']) == 10:
                    five_meal_supplier = 'Euphebe'
            if None not in [five_meal_supplier, ten_meal_supplier]:
                slots = five_meal_supplier[:5] + ten_meal_supplier[:10]
                break

            sorted_scores = sorted(score_board.keys(), reverse=True)
            for score in sorted_scores:

                if restart:
                    restart = False
                    break
                for meal in score_board[score]:

                    supplier = meal['meal'].supplierID
                    if meal['meal'].type.lower() == 'breakfast':
                        continue

                    bucket[supplier].append(meal)

                    # Update score board for this week
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

        # shuffle so that they don't look the same every week
        # shuffle(slots)

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
        print('{} repetitions from last week'.format(repeat_cnt))
        ##

        return slots

    def _repeating_meals(self,patient_id,start_date):
        prev_order = get_order(patient_id,start_date + timedelta(weeks=-1))
        prev_two_order = get_order(patient_id,start_date + timedelta(weeks=-2))
        if prev_order == []:
            prev_order = None
        else:
            try:
                prev_order = [self.meals[x] for x in prev_order[0]['patient_meal_id']]
            except:
                pdb.set_trace()
        if prev_two_order == []:
            prev_twp_order = None
        else:
            prev_two_order = [self.meals[x] for x in prev_two_order[0]['patient_meal_id']]
        return prev_order, prev_two_order

    def reorder_slots(self,slots):
        '''
        reorder based on calories
        :param slots:
        :return:
        '''
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
        new_order = Order(patient_id = patient_id,patient_meal_id = [meal['meal']._id for meal in mealinfo],\
                          week_start_date=start_date, week_end_date=end_date)
        add_order(new_order, patient_id)
        return True

    def write_csv(self,slots,patient_id,start_date,end_date):
        try:
            existing_order = list(csv.reader(open('masterOrder/masterorder.csv','r')))
        except:
            existing_order = [['ID','date','meal_name','minimize','prior','avoid','supplier']]
        for index in range(len(slots)):
            meal = slots[index]
            row = [str(patient_id)[-5:],str(start_date.date()+timedelta(days=index)),meal['meal'].name,\
                   meal['minimize'],meal['prior'],meal['avoid'],meal['meal'].supplierID]
            existing_order.append(row)
        with open('masterOrder/masterorder.csv','w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(existing_order)

    def scoreboard_to_csv(self,score_board,patient_id):
        sorted_score = sorted(score_board.keys(),reverse = True)
        csv_list = [[patient_id],['score','meal','minimize','prior','avoid','supplierID']]
        for score in sorted_score:
            for meal in score_board[score]:
                temp_list = [score]
                temp_list += [meal['meal'],meal['minimize'],meal['prior'], meal['avoid'],meal['meal'].supplierID]
                csv_list.append(temp_list)
        with open('scoreboard/scoreboard_'+str(patient_id)[-5:]+'_'+str(self.today.date())+'.csv','w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_list)
        return True

if __name__ == "__main__":
    ################
    # a = Optimizer(1)
    # a._get_meals()
    ################

    ##### SCORING VARIABLES ######
    # # Euphebe
    # MAX_MEAL_PER_SUPPLIER_1 = 12
    # MIN_MEAL_PER_SUPPLIER_1 = 12
    # # FoodNerd
    # MAX_MEAL_PER_SUPPLIER_2 = 0
    # MIN_MEAL_PER_SUPPLIER_2 = 0

    #MEAL PER SUPPLIER
    MEAL_PER_SUPPLIER_1 = 12
    MEAL_PER_SUPPLIER_2 = 0
    EUPHEBE = 10
    FOODNERD = 5
    VEESTRO = 15,10
    FROZENGARDEN = 5


    ## CAUTION: ALWAYS ADD NUMBERS IN CODE AS THEIR VALUES ARE NEGATIVES
    # MINUS
    DEDUCT_AVOID = -60
    DEDUCT_GR_MIN2 = -60
    DEDUCT_LT_MIN2 = -30
    DEDUCT_LT_MIN1 = -15

    # REPEAT
    REPEAT_ZERO = -50
    REPEAT_ONE = -30
    REPEAT_TWO = -15
    REPEAT_CUM = - 5

    # PLUS
    ADD_PRIOR = 10

    from connectMongdo import drop
    drop('orders')
    try:
        os.remove('masterOrder/masterorder.csv')
    except:
        pass

    ################
    TEST = True

    TODAY = find_tuesday(date.today(),2)

    op = Optimizer()
    op.optimize(TEST)
    # TODAY = find_tuesday(date.today(),2)
    #
    # op = Optimizer()
    # op.optimize(TEST)


