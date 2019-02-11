from pymongo import MongoClient
from bson.objectid import ObjectId
import pickle
import pdb
import pprint
from processEuphebe import Meal
from proccessFoodMatrix import processFoodMatrixCSV
from difflib import SequenceMatcher
from webscrap.dri import submit_form
import itertools
from model import Meal

client = MongoClient("mongodb+srv://admin:thalswns1!@cluster0-jblst.mongodb.net/test")
db = client.test

class Optimizer:
    def __init__(self,patient_id = 0):
        if patient_id:
            self.patient = db.patients.find_one({'_id': ObjectId(patient_id)})
        else:
            self.patient = db.patients.find_one()
        self.preferred_meals= []
        self.calorie, self.carb, self.fiber, self.protein, self.fat = 2000, 50, 50, 50, 50#submit_form(True,int(self.patient['age']),int(self.patient['feet']),\
                                                                                  # int(self.patient['inches']), int(self.patient['weight']),'Sedentary','')
        # self.calorie = 2000

    def filter_meals(self):
        '''
        This function gets patient info and filters out all meals avoids and prioritized ingredients/nutritions
        :return: [Meal()] - a preferred_mealsst of filtered meals
        '''
        # patient_collection = db.patients
        # patient = patient_collection.find_one()
        patient = self.patient

        # get tags
        #TODO: multiple diseases,symptoms, etc
        #TODO: MAP nutritions and ingredients manually, not just by string matching
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

        avoids = list(itertools.chain(*[tag['avoid'] for tag in tags]))
        priors = list(itertools.chain(*[tag['prior'] for tag in tags]))

        meals = db.meals.find()
        score_board = {}
        for meal in meals:
            new_meal = Meal(meal['name'],meal['ingredients'],meal['nutrition'],meal['type'],meal['supplierID'])
            neg = sum([1 if nutrition in avoids else 0 for nutrition in meal['nutrition']])
            neg += sum([1 if ingredient in avoids else 0 for ingredient in meal['ingredients']])

            pos = sum([1 for nutrition in meal['nutrition'] if nutrition in priors])
            pos += sum([1 for ingredient in meal['ingredients'] if ingredient in priors])

            score = 100 - neg*11 + pos * 9
            if score not in score_board.keys():
                score_board[score] = [new_meal]
            else:
                score_board[score].append(new_meal)

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


        pdb.set_trace()

    def optimize(self):
        preferred_meals, other_meals= self.filter_meals()
        cal_l = []
        for each in other_meals:
            try:
                cal_l.append(int(each.nutrition['Cals '].split('.')[0]))
            except:
                pdb.set_trace()
        calorie, ind = self._knapSack(self.calorie,cal_l,len(cal_l))
        # test(preferred_meals)
        return calorie, [other_meals[x] for x in ind]

    def test(preferred_meals):
        for each in preferred_meals:
            print(each['nutrition']['Cals (kcal)'])

if __name__ == "__main__":
    cal, result = Optimizer().optimize()
    print('Total calorie: {}, Meals: {}'.format(cal, result))
