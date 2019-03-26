from pymongo import MongoClient
from bson.objectid import ObjectId
import pdb
import itertools
from model import Meal,MealHistory, MealList, Patient
import csv
from connectMongdo import add_meal_history,get_all_meals, get_mealinfo_by_patient, get_all_tags, get_all_patients, get_any
from random import shuffle
import os
from utils import meal_dict_to_class, tag_dict_to_class, patient_dict_to_class
import pprint

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

    def optimize(self):
        for patient in self.patients:

            # number of meals per week
            # TODO: this should be retrieved from the db
            NUM_MEAL = 15
            score_board = {}

            # get Mongodb IDs and retrieve data from db based on the ID
            tag_ids = patient.symptoms+[patient.disease]+patient.treatment_drugs+patient.comorbidities
            tags = get_any('tags','_id',tag_ids)

            # populate minimize dictionary
            minimizes = {}
            for tag in tags:
                minimizes.update(tag['minimize'])


            ####### Score meals (preprocess) ########
            priors = list(set(itertools.chain(*[tag_dict_to_class(tag).prior for tag in tags])))
            avoids = list(set(itertools.chain(*[tag_dict_to_class(tag).avoid for tag in tags])))
            # get meals from one, two weeks ago to check repetition: repeat_one if one week ago, repeat_two is two weeks ago
            repeat_one_week, repeat_two_week= self._repeating_meals(patient._id)
            should_avoid = False
            for meal in self.meals.values():
                if meal.quantity == 0:
                    continue
                should_avoid = False
                score = 100
                # STRAIGHT AVOIDS
                for each in meal.nutrition.keys() + meal.ingredients.keys():
                    if each in avoids:
                        print('(AOVID TAG) Avoid {}'.format(each))
                        # instead of skipping, penalize by deducting 100 points
                        score -= 80
                        # should_avoid = True
                        break

                # list of keep matched tags
                minimize_list = []
                full_meal_info = {}
                full_meal_info.update(meal.ingredients)
                full_meal_info.update(meal.nutrition)

                for min_item in minimizes.keys():
                    if min_item in full_meal_info.keys():
                        minimize_list.append(min_item)

                        # If a unit is included in the value, get rid of it
                        if not isinstance(full_meal_info[min_item],(float,)):
                            contain_val = float(full_meal_info[min_item].split(' ')[0])
                        else:
                            contain_val = float(full_meal_info[min_item])

                        # if contain val above min 2
                        if contain_val > float(minimizes[min_item]['min2']):
                            print('(MINIMIZE) Avoid {}'.format(min_item))
                            score -= 80
                            # should_avoid = True
                            break
                        # if min1 < val < min2
                        elif contain_val > float(minimizes[min_item]['min1']):
                            score -= 15
                        #if val < min1
                        elif contain_val < float(minimizes[min_item]['min1']):
                            score -= 10
                        # This should never happen
                        else:
                            print('ERR')
                            raise ValueError
                # No need to continue at this point
                # if should_avoid:
                #     continue

                # lists for matched prior tags
                prior_list = [{nutrition: meal.nutrition[nutrition]} for nutrition in meal.nutrition if nutrition in priors]
                prior_list += list(set([ingredient for ingredient in meal.ingredients if ingredient in priors and ingredient not in minimize_list]))
                pos = len(prior_list)
                score += pos*10

                # check repetition. deduct for every repetition of meal
                if repeat_one_week is not None:
                    for repeat_meal in repeat_one_week:
                        if meal == repeat_meal:
                            score -= 60
                if repeat_two_week is not None:
                    for repeat_meal in repeat_two_week:
                        if meal == repeat_meal:
                            score -= 40
                # if repeat_two_week is not None and meal in repeat_two_week:
                #     score -= 40

                # update the score_board
                if score not in score_board.keys():
                    score_board[score] = [{'meal': meal,'prior':prior_list,'minimize':minimize_list}]
                else:
                    score_board[score].append({'meal': meal,'prior':prior_list,'minimize':minimize_list})

            self.scoreboard_to_csv(score_board,patient._id)

            ####### Start choosing meals ########
            # list for saving meals
            if NUM_MEAL > 7:
                slots = [None for _ in range(NUM_MEAL)]
            else:
                slots = [None for _ in range(NUM_MEAL*2)]
            i=0
            # TODO: below should auto link to supplier from db
            # Euphebe
            MAX_MEAL_PER_SUPPLIER_1 = 10
            MIN_MEAL_PER_SUPPLIER_1 = 5
            # FoodNerd
            MAX_MEAL_PER_SUPPLIER_2 = 10
            MIN_MEAL_PER_SUPPLIER_2 = 5

            if MAX_MEAL_PER_SUPPLIER_1 + MAX_MEAL_PER_SUPPLIER_2 < NUM_MEAL or MIN_MEAL_PER_SUPPLIER_2 + MIN_MEAL_PER_SUPPLIER_1 > NUM_MEAL:
                print('maximum meal number constraints to low')
                raise ValueError

            meal_num_per_supplier = {'Euphebe':0, 'FoodNerd': 0}

            num_repeat = 0
            restart = False
            # minimum req
            while i < MIN_MEAL_PER_SUPPLIER_1 + MIN_MEAL_PER_SUPPLIER_2:
                print('restarted')
                sorted_scores = sorted(score_board.keys(), reverse=True)
                # print('-----------{}----------'.format(sorted_scores[0]))
                # pprint.pprint([score_board[sorted_scores[1]]])
                for score in sorted_scores:
                    if i >= MIN_MEAL_PER_SUPPLIER_1 + MIN_MEAL_PER_SUPPLIER_2 or restart:
                        restart = False
                        break
                    for meal in score_board[score]:
                        # if all slots filled
                        if i >= MIN_MEAL_PER_SUPPLIER_1 + MIN_MEAL_PER_SUPPLIER_2 or restart:
                            break

                        supplier = meal['meal'].supplierID
                        if supplier == 'Euphebe':
                            if meal_num_per_supplier[supplier] >= MIN_MEAL_PER_SUPPLIER_1:
                                continue

                        elif supplier == 'FoodNerd':
                            if meal_num_per_supplier[supplier] >= MIN_MEAL_PER_SUPPLIER_2:
                                continue

                        # print('!!!! {} ADDED !!!!'.format(meal['meal']))
                        meal_num_per_supplier[supplier] +=1
                        slots[i] = meal
                        i += 1

                        # deduct just added meal
                        score_board[score].remove(meal)
                        if score - 100 in score_board.keys():
                            score_board[score-100].append(meal)
                        else:
                            score_board[score-100] = [meal]

                        # penalize more as more repetition
                        if repeat_one_week is not None and meal['meal'] in repeat_one_week:
                            num_repeat += 1
                            for score_ in sorted_scores:
                                for repeat in repeat_one_week:
                                    for meal_info in score_board[score_]:
                                        if meal_info['meal'] == repeat:
                                            score_board[score_].remove(meal_info)
                                            if score_ - 5 in score_board.keys():
                                                score_board[score_ -5*num_repeat].append(meal_info)
                                            else:
                                                score_board[score_ -5*num_repeat] = [meal_info]

                        restart = True
                        break

            restart = False
            ### maximum req ###
            while i < len(slots):
                print('RESTARTED')
                sorted_scores = sorted(score_board.keys(), reverse=True)
                print('-----------{}----------'.format(sorted_scores[0]))
                pprint.pprint([score_board[sorted_scores[0]]])
                for score in sorted_scores:
                    if i >= len(slots) or restart:
                        restart = False
                        break
                    for meal in score_board[score]:
                        # if all slots filled
                        if i >= len(slots) or restart:
                            break

                        supplier = meal['meal'].supplierID
                        if supplier == 'Euphebe':
                            if meal_num_per_supplier[supplier] >= MAX_MEAL_PER_SUPPLIER_1:
                                continue
                            meal_num_per_supplier[supplier] += 1
                        elif supplier == 'FoodNerd':
                            if meal_num_per_supplier[supplier] >= MAX_MEAL_PER_SUPPLIER_2:
                                continue
                            meal_num_per_supplier[supplier] += 1
                        else:
                            pdb.set_trace()
                        slots[i] = meal
                        i += 1
                        print('!!!! {} ADDED !!!!'.format(meal['meal']))

                        # deduct just added meal
                        score_board[score].remove(meal)
                        if score - 100 in score_board.keys():
                            score_board[score-100].append(meal)
                        else:
                            score_board[score-100] = [meal]

                        if repeat_one_week is not None and meal['meal'] in repeat_one_week:
                                    num_repeat += 1
                                    for score_ in sorted_scores:
                                        for repeat in repeat_one_week:
                                            for meal_info in score_board[score_]:
                                                if meal_info['meal'] == repeat:
                                                    score_board[score_].remove(meal_info)
                                                    if score_ - 5 in score_board.keys():
                                                        score_board[score_ -5*num_repeat].append(meal_info)
                                                    else:
                                                        score_board[score_ -5*num_repeat] = [meal_info]

                        restart = True
                        break

            # shuffle so that they don't look the same every week
            shuffle(slots)

            # how many repetition from past 2 weeks?
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
            if NUM_MEAL > 7:
                self.to_mongo(slots,patient._id, self.week)
                self.write_csv(slots,patient._id, self.week)
            elif NUM_MEAL <= 7:
                self.to_mongo(slots[:NUM_MEAL], patient._id, self.week)
                self.to_mongo(slots[NUM_MEAL:], patient._id, self.week +1)
                self.write_csv(slots[:NUM_MEAL], patient._id, self.week)
                self.write_csv(slots[NUM_MEAL:], patient._id, self.week +1)


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

    def to_mongo(self, mealinfo, patient_id, wk):
        new_history = MealHistory(patient_id, wk)
        # for 6 meals
        if len(mealinfo) <= 7:
            for i in range(len(mealinfo)):
                new_history.meal_list['day_'+str(i+1)] = [mealinfo[i]['meal']._id]
        # for 12 meals
        else:
            for i in range(len(mealinfo)/2):
                new_history.meal_list['day_'+str(i+1)] = [mealinfo[2*i]['meal']._id, mealinfo[2*i+1]['meal']._id]
        his = add_meal_history(new_history, patient_id)
        return True

    def write_csv(self,slots,patient_id,wk):
        try:
            existing_order = list(csv.reader(open('masterorder.csv','rb')))
        except:
            existing_order = [['ID','Week','Day','meal_name','minimize','prior','supplier']]
        for index in range(len(slots)):
            meal = slots[index]
            row = [str(patient_id)[-5:], wk, 'day '+ str(index+1),meal['meal'].name, meal['minimize'],meal['prior'],meal['meal'].supplierID]
            existing_order.append(row)
        with open('masterorder.csv','wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(existing_order)

    def temp(self):
        # To see how many meals repeat
        wk_num = self.week
        mealinfo = get_mealinfo_by_patient(self.patients[0]._id)
        all_meals = [meal for meal in get_all_meals()]

        if mealinfo is None:
            return None
        curr_list = []
        meal_list = []
        if 'week_'+str(wk_num) in mealinfo.keys():
            prev_week = mealinfo['week_'+str(wk_num)]
            prev_list = prev_week['meal_list']
            for key in prev_list.keys():
                curr_list+= prev_list[key]

        if 'week_'+str(wk_num - 1) in mealinfo.keys():
            prev_week = mealinfo['week_'+str(wk_num - 1)]
            prev_list = prev_week['meal_list']
            for key in prev_list.keys():
                meal_list += prev_list[key]
        last_week = len([x for x in meal_list if x in curr_list])
        print('Repeat from last week: {}'.format(last_week))

        if 'week_'+str(wk_num - 2) in mealinfo.keys():
            prev2_week = mealinfo['week_'+str(wk_num - 2)]
            prev2_list = prev2_week['meal_list']
            for key in prev2_list.keys():
                meal_list += prev2_list[key]
        # no_repeat = [meal for meal in all_meals if meal['_id'] in meal_list]
        print('Repeat from 2 weeks ago: {}'.format(len([x for x in meal_list if x in curr_list]) - last_week))
        return [x for x in meal_list if x in curr_list]

    def scoreboard_to_csv(self,score_board,patient_id):
        sorted_score = sorted(score_board.keys(),reverse = True)
        csv_list = [[patient_id],['score','meal','minimize','prior']]
        for score in sorted_score:
            for meal in score_board[score]:
                temp_list = [score]
                temp_list += [meal['meal'],meal['minimize'],meal['prior']]
                csv_list.append(temp_list)
        with open('scoreboard_'+str(patient_id)[-5:]+'.csv','wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_list)
        return True




if __name__ == "__main__":
    from connectMongdo import drop
    drop('mealInfo')
    os.remove('masterorder.csv')
    op = Optimizer(week = 1)
    op.optimize()
    # op = Optimizer(week = 2)
    # op.optimize()
    # op = Optimizer(week = 3)
    # op.optimize()
    # ab = op.temp()
    # pdb.set_trace()

