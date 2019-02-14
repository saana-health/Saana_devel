from pymongo import MongoClient
from bson.objectid import ObjectId
import pickle
import pdb
import pprint
from processEuphebe import Meal
from processFoodMatrix import processFoodMatrixCSV
from difflib import SequenceMatcher
from webscrap.dri import submit_form
import itertools
from model import Meal,MealHistory, MealList
import csv
from connectMongdo import add_meal_history,find_meal, get_all_meals, get_mealinfo_by_patient

client = MongoClient("mongodb+srv://admin:thalswns1!@cluster0-jblst.mongodb.net/test")
db = client.test

class Optimizer:
    '''
    Class for optimizing a patient's meals for a week
    '''
    def __init__(self,patient_id = 0, week_num = 1):
        if patient_id:
            self.patient = db.patients.find_one({'_id': ObjectId(patient_id)})
        else:
            self.patient = db.patients.find_one()
        self.week_num = week_num
        self.preferred_meals= []
        # This below line should be read from the db later on
        self.calorie, self.carb, self.fiber, self.protein, self.fat = 2000, 50, 50, 50, 50#submit_form(True,int(self.patient['age']),int(self.patient['feet']),\
                                                                                  # int(self.patient['inches']), int(self.patient['weight']),'Sedentary','')
        # self.calorie = 2000

    # def get_history(self):


    def optimize(self):
        '''
        This function tries to choose a good list of meals for a patient based on her/his constraint
        :return: [{lunchs}], [{dinners}]
        '''
        print(1)
        patient = self.patient

        # get tags
        #TODO: multiple diseases,symptoms, etc
        tags = []
        # treatment_drugs = db.tags.find_one({'_id':patient['treatment_drugs']})
        # comorbidities = db.tags.find_one({'_id':patient['comorbidities']})
        # symptoms = db.tags.find_one({'_id':patient['symptoms'][0]})
        diseases = db.tags.find_one({'_id':patient['disease']})

        # append only if not None (if found)
        # if treatment_drugs:
        #     tags.append(treatment_drugs)
        # if comorbidities:
        #     tags.append(comorbidities)
        # if symptoms:
        #     tags.append(symptoms)
        if diseases:
            tags.append(diseases)

        # Concat all the tags
        avoids = list(itertools.chain(*[tag['avoid'] for tag in tags]))
        priors = list(itertools.chain(*[tag['prior'] for tag in tags]))

        meals = self._check_repitition()
        score_board = {}
        print(2)
        # Score each meal based on their ingredients/nutritions
        for meal in meals:
            new_meal = Meal(meal['name'],meal['ingredients'],meal['nutrition'],meal['type'],meal['supplierID'])

            neg = sum([1 if nutrition in avoids else 0 for nutrition in meal['nutrition']])
            neg += sum([1 if ingredient in avoids else 0 for ingredient in meal['ingredients']])
            pos = sum([1 for nutrition in meal['nutrition'] if nutrition in priors])
            pos += sum([1 for ingredient in meal['ingredients'] if ingredient in priors])

            avoid_list = [nutrition for nutrition in meal['nutrition'] if nutrition in avoids]
            avoid_list += [ingredient for ingredient in meal['ingredients'] if ingredient in avoids]
            prior_list = [nutrition for nutrition in meal['nutrition'] if nutrition in priors]
            prior_list += [ingredient for ingredient in meal['ingredients'] if ingredient in priors]

            score = 100 - neg*11 + pos * 9
            if score not in score_board.keys():
                score_board[score] = [{'meal': new_meal,'prior':prior_list,'avoid':avoid_list}]
            else:
                score_board[score].append({'meal': new_meal,'prior':prior_list,'avoid':avoid_list})

        # This is where meals will be saved
        # TODO: change the number based on input
        lunches = [None for x in range(7)]
        dinners = [None for x in range(7)]
        print(3)
        sorted_scores = sorted(score_board.keys(),reverse=True)
        i = 0
        for score in sorted_scores:
            if i >= len(dinners) + len(lunches):
                break
            for meal in score_board[score]:
                if i < len(dinners):
                    dinners[i] =  meal
                    i += 1
                elif i < len(dinners) + len(lunches):
                    lunches[i-len(dinners)] = meal
                    i += 1
                else:
                    break
        return lunches, dinners

    def _check_repitition(self):
        print(4)
        wk_num = self.week_num
        mealinfo = get_mealinfo_by_patient(self.patient['_id'])
        all_meals = [meal for meal in get_all_meals()]

        if mealinfo is None:
            return all_meals
        meal_list = []
        if 'week_'+str(wk_num - 1) in mealinfo.keys():
            prev_week = mealinfo['week_'+str(wk_num - 1)]
            prev_list = prev_week['meal_list']
            for key in prev_list.keys():
                meal_list.append(prev_list[key]['lunch'])
                meal_list.append(prev_list[key]['dinner'])

        if 'week_'+str(wk_num - 2) in mealinfo.keys():
            prev2_week = mealinfo['week_'+str(wk_num - 2)]
            prev2_list = prev2_week['meal_list']
            for key in prev2_list.keys():
                meal_list.append(prev2_list[key]['lunch'])
                meal_list.append(prev2_list[key]['dinner'])

        no_repeat = [meal for meal in all_meals if meal['_id'] not in meal_list]
        return no_repeat

    def to_csv(self, lunches, dinners):
        '''
        This function is for generating master order file for a week
        :param lunches: [{lunch}] - from optimize()
        :param dinners: [{dinner}] - ^
        :return: [[]] - 2D array that is written to the csv file
        '''
        csv_arry = [[self.patient['_id']],['Date','Meal Type','Meal Name','Limiting nutritions','Prioritized nutrtions','Meal provider','Price']]
        for index in range(7):
            lunch = lunches[index]
            dinner = dinners[index]
            csv_arry.append(['Feb '+str(index+1),'Lunch',lunch['meal'].name,lunch['avoid'],lunch['prior'],lunch['meal'].supplierID,lunch['meal'].price])
            csv_arry.append(['Feb '+str(index+1),'dinner',dinner['meal'].name,dinner['avoid'],dinner['prior'],dinner['meal'].supplierID,dinner['meal'].price])
        with open('master_order.csv','wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_arry)
        return csv_arry

    def to_mongo(self, lunches, dinners):
        '''
        This function processes the meal lists into mongo-digestable format
        :param lunches: [{lunch}] - from optimize()
        :param dinners: [{dinner}] - from optimize()
        :return: class MealHistory
        '''
        new_history = MealHistory(self.patient['_id'], self.week_num)
        # new_history.meal_list = [ find_meal(lunch['meal'].name)['_id'] for lunch in lunches] + [find_meal(dinner['meal'].name)['_id'] for dinner in dinners]
        all_meals = get_all_meals()
        for i in range(7):
            lunch = [x for x in all_meals if x['name'] == lunches[i]['meal'].name][0]
            dinner = [x for x in all_meals if x['name'] == dinners[i]['meal'].name][0]
            # lunch = all_meals.find_by('name',lunches[i]['meal'].name)
            # dinner = all_meals.find_by('name', dinners[i]['meal'].name)
            new_history.meal_list['day_'+str(i+1)] = {'lunch': lunch['_id'], 'dinner': dinner['_id']}
        return new_history

if __name__ == "__main__":
    test = Optimizer(patient_id = ObjectId('5c07a873a56a67691f9fd6e6'),week_num = 3)
    lunches, dinners = test.optimize()
    # test._check_repitition()
    # csv_arry = test.to_csv(lunches, dinners)
    new_history = test.to_mongo(lunches, dinners)
    his = add_meal_history(new_history, test.patient['_id'])
