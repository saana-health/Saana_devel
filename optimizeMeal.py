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
from model import Meal,MealHistory
import csv
from connectMongdo import add_meal_history,find_meal

client = MongoClient("mongodb+srv://admin:thalswns1!@cluster0-jblst.mongodb.net/test")
db = client.test

class Optimizer:
    '''
    Class for optimizing a patient's meals for a week
    '''
    def __init__(self,patient_id = 0):
        if patient_id:
            self.patient = db.patients.find_one({'_id': ObjectId(patient_id)})
        else:
            self.patient = db.patients.find_one()
        self.preferred_meals= []
        # This below line should be read from the db later on
        self.calorie, self.carb, self.fiber, self.protein, self.fat = 2000, 50, 50, 50, 50#submit_form(True,int(self.patient['age']),int(self.patient['feet']),\
                                                                                  # int(self.patient['inches']), int(self.patient['weight']),'Sedentary','')
        # self.calorie = 2000

    def optimize(self):
        '''
        This function tries to choose a good list of meals for a patient based on her/his constraint
        :return: [{lunchs}], [{dinners}]
        '''
        patient = self.patient

        # get tags
        #TODO: multiple diseases,symptoms, etc
        tags = []
        treatment_drugs = db.tags.find_one({'_id':patient['treatment_drugs']})
        comorbidities = db.tags.find_one({'_id':patient['comorbidities']})
        symptoms = db.tags.find_one({'_id':patient['symptoms'][0]})
        diseases = db.tags.find_one({'_id':patient['disease']})

        # append only if not None (if found)
        if treatment_drugs:
            tags.append(treatment_drugs)
        if comorbidities:
            tags.append(comorbidities)
        if symptoms:
            tags.append(symptoms)
        if diseases:
            tags.append(diseases)

        # Concat all the tags
        avoids = list(itertools.chain(*[tag['avoid'] for tag in tags]))
        priors = list(itertools.chain(*[tag['prior'] for tag in tags]))

        meals = db.meals.find()
        score_board = {}

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
        lunches = [None for x in range(7)]
        dinners = [None for x in range(7)]

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
        pdb.set_trace()
        return csv_arry

    def to_mongo(self, lunches, dinners):
        '''
        This function processes the meal lists into mongo-digestable format
        :param lunches: [{lunch}] - from optimize()
        :param dinners: [{dinner}] - from optimize()
        :return: class MealHistory
        '''
        new_history = MealHistory(self.patient['_id'], 1)
        meal = find_meal(lunches[0]['meal'].name)
        new_history.meal_list = [ find_meal(lunch['meal'].name)['_id'] for lunch in lunches] + [find_meal(dinner['meal'].name)['_id'] for dinner in dinners]
        return new_history

if __name__ == "__main__":
    test = Optimizer()
    lunches, dinners = test.optimize()
    csv_arry = test.to_csv(lunches, dinners)
    new_history = test.to_mongo(lunches, dinners)
    his = add_meal_history(new_history)
