from pymongo import MongoClient
from bson.objectid import ObjectId
import pdb
import itertools
from model import Meal,MealHistory, MealList, Patient
import csv
from connectMongdo import add_meal_history,get_all_meals, get_mealinfo_by_patient, get_all_tags, get_all_patients, get_any, update_next_order
from random import shuffle
import os
from utils import meal_dict_to_class, tag_dict_to_class, patient_dict_to_class, find_tuesday
import pprint
from datetime import date, timedelta
import time
DATE = time.ctime()[4:10].replace(' ','_')

class Optimizer:

    def __init__(self, week):
        self.meals = self._get_meals()
        self.tags = self._get_tags()
        self.inventory = self._check_inventory()
        self.patients = self._get_patients()
        self.week = week

    def _get_meals(self):
        '''

        :return: {_id: Meal()}
        '''
        hash_meal = {}
        meals = [meal for meal in get_all_meals()]
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

    def _get_patients(self):
        '''

        :return: [Patient()]
        '''
        return [patient_dict_to_class(patient) for patient in get_all_patients()]

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
            today = TODAY
            assert today.weekday() == 1
            # today = date.today()
            num_meal = patient.plan
            if not test and patient.next_order != today:
                continue

            print('Processing   {}  !'.format(patient.name))
            score_board = {}

            # get all tags
            tag_ids = patient.symptoms+[patient.disease]+patient.treatment_drugs+patient.comorbidities
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

            assert len(slots) == 15

            slots = self.reorder_slots(slots)

            if num_meal> 8:
                self.to_mongo(slots,patient._id, self.week)
                self.write_csv(slots,patient._id, self.week)
                update_next_order(patient._id,find_tuesday(today,2))
            else:
                self.to_mongo(slots[:num_meal], patient._id, self.week)
                self.to_mongo(slots[num_meal:], patient._id, self.week +1)
                self.write_csv(slots[:num_meal], patient._id, self.week)
                self.write_csv(slots[num_meal:], patient._id, self.week +1)
                update_next_order(patient._id,find_tuesday(today,3))

    def get_score_board(self, patient, minimizes, avoids, priors):
        # get meals from one, two weeks ago to check repetition: repeat_one if one week ago, repeat_two is two weeks ago
        repeat_one_week, repeat_two_week= self._repeating_meals(patient._id)
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
                        if not isinstance(full_meal_info[ing],(float,)):
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
                            continue
                            # score += DEDUCT_LT_MIN1
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
                    if prior in ingredient and prior not in minimize_list + avoid_list and priors[prior] < meal.ingredients[ingredient]:
                        prior_list.append(prior)
                for nutrition in meal.nutrition.keys():
                    if (nutrition in prior or prior in nutrition) and prior not in minimize_list + avoid_list and priors[prior] < float(meal.nutrition[nutrition].split(' ')[0]):
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
        slots = []
        meal_num_per_supplier = {'Euphebe':0, 'FoodNerd': 0}
        num_repeat = 0
        restart = False

        num_meal = 15
        while len(slots) < num_meal:
            sorted_scores = sorted(score_board.keys(), reverse=True)
            for score in sorted_scores:

                if restart:
                    restart = False
                    break
                for meal in score_board[score]:

                    supplier = meal['meal'].supplierID

                    if supplier == 'Euphebe' and meal_num_per_supplier[supplier] >= MEAL_PER_SUPPLIER_1:
                            continue
                    elif supplier == 'FoodNerd' and meal_num_per_supplier[supplier] >= MEAL_PER_SUPPLIER_2:
                            continue

                    # ADD meal
                    # print('{}: -- {} -- chose'.format(score,meal))
                    slots.append(meal)

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

    def _repeating_meals(self,patient_id):
        wk_num = self.week
        mealinfo = get_mealinfo_by_patient(patient_id)
        prev_list = []
        prev2_list = []
        week1 = []
        week2 = []
        if mealinfo is None:
            return None, None

        if 'week_' + str(wk_num -1) in mealinfo.keys():
                prev_week = mealinfo['week_'+str(wk_num -1)]
                prev_list = list(set(itertools.chain(*[x for x in prev_week['meal_list'].values()])))
                week1 = [self.meals[k] for k in prev_list]

        if 'week_' + str(wk_num -2) in mealinfo.keys():
            prev2_week = mealinfo['week_'+str(wk_num -2)]
            prev2_list = list(set(itertools.chain(*[x for x in prev2_week['meal_list'].values()])))
            week2 = [self.meals[k] for k in prev2_list]
        return week1,week2

    def reorder_slots(self,slots):
        slots = sorted(slots, key = lambda meal: float(meal['meal'].nutrition['cals'].split(' ')[0]),reverse=True)
        high_cal = slots[:7]
        low_cal = slots[8:]
        new_slots = []
        for high,low in zip(high_cal,low_cal[::-1]):
            new_slots.append(high)
            new_slots.append(low)
        new_slots.append(slots[7])
        return new_slots

    def to_mongo(self, mealinfo, patient_id, wk):
        new_history = MealHistory(patient_id, wk)
        # for 6 meals
        if len(mealinfo) <= 8:
            for i in range(len(mealinfo)):
                new_history.meal_list['day_'+str(i+1)] = [mealinfo[i]['meal']._id]
        # for 12 meals
        else:
            for i in range(len(mealinfo)):
                if not i % 2:
                    new_history.meal_list['day_'+str(int(i/2) + 1)] = [mealinfo[i]['meal']._id]
                else:
                    new_history.meal_list['day_'+str(int(i/2) + 1)] += [mealinfo[i]['meal']._id]
            # for i in range(len(mealinfo)2):
            #     new_history.meal_list['day_'+str(i+1)] = [mealinfo[2*i]['meal']._id, mealinfo[2*i+1]['meal']._id]
        his = add_meal_history(new_history, patient_id)
        return True

    def write_csv(self,slots,patient_id,wk):
        try:
            existing_order = list(csv.reader(open('masterOrder/masterorder.csv','r')))
        except:
            existing_order = [['ID','Week','Day','meal_name','minimize','prior','avoid','supplier']]
        for index in range(len(slots)):
            meal = slots[index]
            row = [str(patient_id)[-5:], wk, 'day '+ str(index+1),meal['meal'].name, meal['minimize'],meal['prior'],meal['avoid'],meal['meal'].supplierID]
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
        with open('scoreboard/scoreboard_'+str(patient_id)[-5:]+'_'+str(self.week)+'.csv','w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_list)
        return True

if __name__ == "__main__":
    # # Euphebe
    # MAX_MEAL_PER_SUPPLIER_1 = 12
    # MIN_MEAL_PER_SUPPLIER_1 = 12
    # # FoodNerd
    # MAX_MEAL_PER_SUPPLIER_2 = 0
    # MIN_MEAL_PER_SUPPLIER_2 = 0

    #MEAL PER SUPPLIER
    MEAL_PER_SUPPLIER_1 = 12
    MEAL_PER_SUPPLIER_2 = 0

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
    drop('mealInfo')
    try:
        os.remove('masterOrder/masterorder.csv')
    except:
        pass

    TEST = False

    print('----WK1----')
    TODAY = find_tuesday(date.today(),1)
    op = Optimizer(week = 1)
    op.optimize(TEST)

    # print('----WK2----')
    # TODAY = find_tuesday(date.today(),2)
    # op = Optimizer(week = 2)
    # op.optimize(TEST)
    #
    # print('----WK3----')
    # TODAY = find_tuesday(date.today(),3)
    # op = Optimizer(week = 3)
    # op.optimize(TEST)
    #
    # print('----WK4----')
    # TODAY = find_tuesday(date.today(),4)
    # op = Optimizer(week = 4)
    # op.optimize(TEST)
