from pymongo import MongoClient
from bson.objectid import ObjectId
import pdb
import itertools
from model import Meal,MealHistory, MealList, Patient
import csv
from connectMongdo import add_meal_history,find_meal, get_all_meals, get_mealinfo_by_patient, get_all_tags, get_all_patients
from random import shuffle
import os
from utils import meal_dict_to_class, tag_dict_to_class, patient_dict_to_class

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

            NUM_MEAL = 14
            que = []
            score_board = {}
            tags = self.tags

            minimizes = list(set(itertools.chain(*[tag.minimize for tag in tags.values()])))
            priors = list(set(itertools.chain(*[tag.prior for tag in tags.values()])))
            avoids = list(set(itertools.chain(*[tag.avoid for tag in tags.values()])))
            repeat_one_week, repeat_two_week= self._repeating_meals(patient._id)


            for meal in self.meals.values():
                score = 100
                if repeat_one_week is not None and meal in repeat_one_week:
                    score -= 60
                if repeat_two_week is not None and meal in repeat_two_week:
                    score -= 40


                # neg = sum([1 for nutrition in meal.nutrition if nutrition in minimizes])
                # neg += sum([1 for ingredient in meal.ingredients if ingredient in minimizes])
                minimize_list = [{nutrition: meal.nutrition[nutrition]} for nutrition in meal.nutrition if nutrition in minimizes]
                minimize_list += list(set([ingredient for ingredient in meal.ingredients if ingredient in minimizes and ingredient not in minimize_list]))

                # pos = sum([1 for nutrition in meal.nutrition if nutrition in priors])
                # pos += sum([1 for ingredient in meal.ingredients if ingredient in priors and ingredient not in minimize_list])
                prior_list = [{nutrition: meal.nutrition[nutrition]} for nutrition in meal.nutrition if nutrition in priors]
                prior_list += list(set([ingredient for ingredient in meal.ingredients if ingredient in priors and ingredient not in minimize_list]))

                neg = len(minimize_list)
                pos = len(prior_list)

                score += pos*10 - neg*9
                if score not in score_board.keys():
                    score_board[score] = [{'meal': meal,'prior':prior_list,'minimize':minimize_list}]
                else:
                    score_board[score].append({'meal': meal,'prior':prior_list,'minimize':minimize_list})
            slots = [None for _ in range(NUM_MEAL)]
            sorted_scores = sorted(score_board.keys(), reverse=True)
            i=0
            for score in sorted_scores:
                if i >= len(slots):
                    break
                for meal in score_board[score]:
                    if i >= len(slots):
                        break
                    slots[i] = meal
                    i += 1
            self.to_mongo(slots,patient._id)


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

    def to_mongo(self, mealinfo, patient_id):
        new_history = MealHistory(patient_id, self.week)
        if len(mealinfo) == 7:
            for i in range(7):
                new_history.meal_list['day_'+str(i+1)] = [mealinfo[i]['meal']._id]
        else:
            for i in range(7):
                new_history.meal_list['day_'+str(i+1)] = [mealinfo[2*i - 2]['meal']._id, mealinfo[2*i -1]['meal']._id]
        his = add_meal_history(new_history, patient_id)
        return True

    def temp(self):
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

        if 'week_'+str(wk_num - 2) in mealinfo.keys():
            prev2_week = mealinfo['week_'+str(wk_num - 2)]
            prev2_list = prev2_week['meal_list']
            for key in prev2_list.keys():
                meal_list += prev2_list[key]
        # no_repeat = [meal for meal in all_meals if meal['_id'] in meal_list]
        return [x for x in meal_list if x in curr_list]
if __name__ == "__main__":
    op = Optimizer(week = 1)
    op.optimize()
    op = Optimizer(week = 2)
    op.optimize()
    op = Optimizer(week = 3)
    op.optimize()
    # ab = op.temp()
    # pdb.set_trace()

