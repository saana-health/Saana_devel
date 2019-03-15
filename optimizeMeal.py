from pymongo import MongoClient
from bson.objectid import ObjectId
import pdb
import itertools
from model import Meal,MealHistory, MealList, Patient
import csv
from connectMongdo import add_meal_history,find_meal, get_all_meals, get_mealinfo_by_patient, get_all_tags, get_all_patients, find_tag,get_any
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

            NUM_MEAL = 6
            que = []
            score_board = {}
            ids = patient.symptoms+[patient.disease]+patient.treatment_drugs+patient.comorbidities
            tags = get_any('tags','_id',ids)
            # minimizes = list(set(itertools.chain(*[tag_dict_to_class(tag).minimize for tag in tags])))
            minimizes = {}
            for tag in tags:
                minimizes.update(tag['minimize'])

            priors = list(set(itertools.chain(*[tag_dict_to_class(tag).prior for tag in tags])))
            avoids = list(set(itertools.chain(*[tag_dict_to_class(tag).avoid for tag in tags])))
            repeat_one_week, repeat_two_week= self._repeating_meals(patient._id)
            should_avoid = False
            for meal in self.meals.values():
                should_avoid = False
                score = 100
                ## STRAIGHT AVOIDS
                # for each in meal.nutrition.keys() + meal.ingredients.keys():
                #     if each in avoids:
                #         print('Avoid {}'.format(each))
                #         should_avoid = True
                #         break



                # neg = sum([1 for nutrition in meal.nutrition if nutrition in minimizes])
                # neg += sum([1 for ingredient in meal.ingredients if ingredient in minimizes])
                # minimize_list = [{nutrition: meal.nutrition[nutrition]} for nutrition in meal.nutrition if nutrition in minimizes]
                # minimize_list += list(set([ingredient for ingredient in meal.ingredients if ingredient in minimizes and ingredient not in minimize_list]))

                minimize_list = []
                full_meal_info = {}
                full_meal_info.update(meal.ingredients)
                full_meal_info.update(meal.nutrition)

                for min_item in minimizes.keys():
                    if min_item in full_meal_info.keys():
                        minimize_list.append(min_item)
                        if not isinstance(full_meal_info[min_item],(float,)):
                            contain_val = float(full_meal_info[min_item].split(' ')[0])
                        else:
                            contain_val = float(full_meal_info[min_item])

                        if contain_val > float(minimizes[min_item]['min2']):
                            print('Avoid {}'.format(min_item))
                            should_avoid = True
                            break
                        elif contain_val > float(minimizes[min_item]['min1']):
                            score -= 15
                        elif contain_val < float(minimizes[min_item]['min1']):
                            score -= 10
                        else:
                            print('ERR')
                            raise ValueError

                if should_avoid:
                    continue

                # pos = sum([1 for nutrition in meal.nutrition if nutrition in priors])
                # pos += sum([1 for ingredient in meal.ingredients if ingredient in priors and ingredient not in minimize_list])
                prior_list = [{nutrition: meal.nutrition[nutrition]} for nutrition in meal.nutrition if nutrition in priors]
                prior_list += list(set([ingredient for ingredient in meal.ingredients if ingredient in priors and ingredient not in minimize_list]))

                # neg = len(minimize_list)
                pos = len(prior_list)

                if repeat_one_week is not None and meal in repeat_one_week:
                    score -= 60
                if repeat_two_week is not None and meal in repeat_two_week:
                    score -= 40
                score += pos*10
                if score not in score_board.keys():
                    score_board[score] = [{'meal': meal,'prior':prior_list,'minimize':minimize_list}]
                else:
                    score_board[score].append({'meal': meal,'prior':prior_list,'minimize':minimize_list})

            slots = [None for _ in range(NUM_MEAL)]
            sorted_scores = sorted(score_board.keys(), reverse=True)
            i=0
            MAX_MEAL_PER_SUPPLIER_1 = 7
            MAX_MEAL_PER_SUPPLIER_2 = 0

            meal_num_per_supplier = {}
            for score in sorted_scores:
                if i >= len(slots):
                    break
                for meal in score_board[score]:
                    # if all slots filled
                    if i >= len(slots):
                        break

                    supplier = meal['meal'].supplierID
                    if supplier not in meal_num_per_supplier.keys():
                        if supplier == 'Euphebe' and MAX_MEAL_PER_SUPPLIER_1 == 0:
                            continue
                        elif supplier == 'FoodNerd' and MAX_MEAL_PER_SUPPLIER_2 == 0:
                            continue
                        meal_num_per_supplier[supplier] = 1

                    elif supplier == 'Euphebe':
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
            shuffle(slots)
            if None in slots:
                print('Not enough maching meals')
                pdb.set_trace()
            cnt = 0
            for each in score_board.values():
                for each2 in each:
                    cnt += 1
            print(' TOTAL   {}  available meals'.format(cnt))
            # self.debug(slots)
            self.to_mongo(slots,patient._id)
            self.to_csv(slots,patient._id)

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
        elif len(mealinfo) == 6:
            for i in range(6):
                new_history.meal_list['day_'+str(i+1)] = [mealinfo[i]['meal']._id]

        else:
            for i in range(7):
                new_history.meal_list['day_'+str(i+1)] = [mealinfo[2*i - 2]['meal']._id, mealinfo[2*i -1]['meal']._id]
        his = add_meal_history(new_history, patient_id)
        return True

    def to_csv(self, slots, patient_id):
        '''
        This function is for generating master order file for a week
        :param lunches: [{lunch}] - from optimize()
        :param dinners: [{dinner}] - ^
        :return: [[]] - 2D array that is written to the csv file
        '''
        csv_arry = [[patient_id],['Date','Meal Type','Meal Name','Limiting nutrition','Prioritized nutrtion','Meal provider',\
                                  'Tot Cal', 'Protein','Carb','Fat','Tot Fib','TotSolFib']]
        if len(slots) == 14:
            for index in range(7):
                meal_1 = slots[2*index]
                meal_2 = slots[2*index +1]
                csv_arry.append(['Day '+str(index+1),'meal_1',meal_1['meal'].name,meal_1['minimize'],meal_1['prior'],meal_1['meal'].supplierID,meal_1['meal'].nutrition])
                csv_arry.append(['Day '+str(index+1),'meal_2',meal_2['meal'].name,meal_2['minimize'],meal_2['prior'],meal_2['meal'].supplierID,meal_2['meal'].nutrition])
        else:
            for index in range(6):
                meal_1 = slots[index]
                nutrition_dic = meal_1['meal'].nutrition
                csv_arry.append(['Day '+str(index+1),'meal_1',meal_1['meal'].name,meal_1['minimize'],meal_1['prior'],meal_1['meal'].supplierID,\
                                 nutrition_dic['cals'],nutrition_dic['prot'],nutrition_dic['carb'],nutrition_dic['fat'],nutrition_dic['totfib'],nutrition_dic['totsolfib']])
        with open('masterOrder/'+str(patient_id)+'_wk'+str(self.week)+'.csv','wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_arry)
        return csv_arry

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

    def debug(self,slots):
        import pprint
        meals =[]
        for each in slots:
            meals.append(each['meal'])

        pdb.set_trace()


if __name__ == "__main__":
    op = Optimizer(week = 1)
    op.optimize()
    op = Optimizer(week = 2)
    op.optimize()
    # op = Optimizer(week = 3)
    # op.optimize()
    # ab = op.temp()
    # pdb.set_trace()

