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
        self.li = []
        self.calorie, self.carb, self.fiber, self.protein, self.fat = submit_form(True,int(self.patient['age']),int(self.patient['feet']),\
                                                                                  int(self.patient['inches']), int(self.patient['weight']),'Sedentary','')

    def filter_meals(self):
        '''
        This function gets patient info and filters out all meals avoids and prioritized ingredients/nutritions
        :return: [Meal()] - a list of filtered meals
        '''
        # patient_collection = db.patients
        # patient = patient_collection.find_one()
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

        avoids = list(itertools.chain(*[tag['avoid'] for tag in tags]))
        priors = list(itertools.chain(*[tag['prior'] for tag in tags]))

        # generate a list of meals
        li = []
        meals = db.meals.find()
        for new_meal in meals:
            meal = Meal(new_meal['name'], new_meal['ingredients'], new_meal['nutrition'], new_meal['type'], new_meal['supplierID'], new_meal['price'])
            new = False
            ingredients = meal.ingredients
            nutritions = meal.nutrition
            # Matching part below should be gone once mapping is done in the preliminary part
            for avoid in avoids:
                if new:
                    break
                pdb.set_trace()
                for ingredient in ingredients:
                    if SequenceMatcher(None,ingredient.lower(),avoid.lower()).ratio()>0.6:
                        print(ingredient,avoid,SequenceMatcher(None,ingredient.lower(),avoid.lower()).ratio())
                        new = True
                        break
                for nutrition in nutritions:
                    if SequenceMatcher(None,nutrition.lower(),avoid.lower()).ratio() > 0.6:
                        print(nutrition,avoid,SequenceMatcher(None,nutrition.lower(),avoid.lower()).ratio())
                        new = True
                        break
            ## This is for appending if not found in avoids
            # if not new:
            #     li.append(meal)

            for prior in priors:
                for nutrition in nutritions:
                    r = SequenceMatcher(None,prior.lower(),nutrition.lower()).ratio()
                    if r > 0.6:
                        print('{} matched *{}* with *{}* by {} %'.format(meal.name,prior,nutrition,r ))
                        li.append(meal)
                for ingredient in ingredients:
                    r = SequenceMatcher(None,ingredient.lower(),prior.lower()).ratio()
                    if r > 0.6:
                        print('{} matched **{}** with **{}** by {}%'.format(meal.name,prior,ingredient,r))
                        li.append(meal)
        return li

    def _knapSack(self,W, wt, n):
        '''
        This function is a solver algorithm for a knapsack problem. Used to find meals with best results with a constratint W.
        More information can be found here: https://www.geeksforgeeks.org/0-1-knapsack-problem-dp-10/
        >Basically solving: Given limit integer 'W', find among 'n' times in the array 'wt' that best maximize the value (in this case val = wt)
        TODO: This algorithm only uses calories

        :param W: INT - 'weight' (daily calorie limit)
        :param wt: [INT] - a list of 'weights' (calories) for each meal
        :param n: INT - number of items
        :return: [Meal()] - best matching meals
        '''
        val = wt

        # This is the ultimate 4D list [item index][weight][value, [list of meals]] that stores values and meals
        K = [[[0,[]] for x in range(W+1)] for x in range(n+1)]

        for i in range(n+1):
            for w in range(W+1):
                # base cases
                if i==0 or w==0:
                    K[i][w][0] = 0

                # if 'weight'(calorie) is smaller than the current 'w' index
                elif wt[i-1] <= w:
                    K[i][w][0] = max(val[i-1] + K[i-1][w-wt[i-1]][0],  K[i-1][w][0])
                    if val[i-1] + K[i-1][w-wt[i-1]][0] >  K[i-1][w][0]:
                        K[i][w][1] = K[i-1][w-wt[i-1]][1][:]+[i-1]
                    else:
                        K[i][w][1] = K[i-1][w][1][:]

                else:
                    K[i][w][0] = K[i-1][w][0]
                    K[i][w][1] = K[i-1][w][1][:]

        return K[n][W][0],K[n][W][1]

    def optimize(self):
        '''
        This functions basically use the returned list of meals from 'filter_meals()' and apply it to the knapsack function
        :param li: [Meal()] - filtered list of meals
        :return : INT, [Meal()] - achieved calorie and list of meals
        '''
        li = self.filter_meals()
        cal_l = []
        for each in li:
            try:
                cal_l.append(int(each.nutrition['Cals (kcal)']))
            except:
                pdb.set_trace()
        calorie, ind = self._knapSack(self.calorie,cal_l,len(cal_l))
        # test(li)
        return calorie, [li[x] for x in ind]

    def test(li):
        for each in li:
            print(each['nutrition']['Cals (kcal)'])

if __name__ == "__main__":
    cal, result = Optimizer().optimize()
    pdb.set_trace()
