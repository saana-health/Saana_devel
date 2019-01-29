from pymongo import MongoClient
import pickle
import pdb
import pprint
from processEuphebe import Meal
from proccessFoodMatrix import processFoodMatrixCSV
from difflib import SequenceMatcher
from webscrap.dri import submit_form
import itertools

client = MongoClient("mongodb+srv://admin:thalswns1!@cluster0-jblst.mongodb.net/test")
db = client.test

def filter_meals():
    '''
    This function gets patient info and filters out all meals avoids and prioritized ingredients/nutritions
    :return: [Meal()] - a list of filtered meals
    '''
    #TODO: input as patient ID and search for that patient
    patient_collection = db.patients
    patient = patient_collection.find_one()

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
    for meal in meals:
        new = False
        ingredients = meal['ingredients']
        nutritions = meal['nutrition']
        for avoid in avoids:
            if new:
                break
            for ingredient in ingredients:
                if SequenceMatcher(None,ingredient,avoid).ratio()>0.6:
                    new = True
                    break
            for nutrition in nutritions:
                if SequenceMatcher(None,nutrition,avoid).ratio() > 0.6:
                    new = True
                    break
        ## This is for appending if not found in avoids
        # if not new:
        #     li.append(meal)

        for prior in priors:
            for nutrition in nutritions:
                r = SequenceMatcher(None,prior.lower(),nutrition.lower()).ratio()
                if r > 0.6:
                    print('{} matched *{}* with *{}* by {} %'.format(meal['name'],prior,nutrition,r ))
                    li.append(meal)
            for ingredient in ingredients:
                r = SequenceMatcher(None,ingredient.lower(),prior.lower()).ratio()
                if r > 0.6:
                    print('{} matched **{}** with **{}** by {}%'.format(meal['name'],prior,ingredient,r))
                    li.append(meal)
    return li

def _knapSack(W, wt, n):
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

def optimize(li):
    '''
    This functions basically use the returned list of meals from 'filter_meals()' and apply it to the knapsack function
    :param li: [Meal()] - filtered list of meals
    :return : INT, [Meal()] - achieved calorie and list of meals
    '''
    cal_l = []
    for each in li:
        try:
            cal_l.append(int(each['nutrition']['Cals (kcal)']))
        except:
            pdb.set_trace()
    calorie, ind = _knapSack(2350,cal_l,len(cal_l))
    # test(li)
    return calorie, [li[x] for x in ind]

def test(li):
    for each in li:
        print(each['nutrition']['Cals (kcal)'])

if __name__ == "__main__":
    cal, result = optimize(filter_meals())
    pdb.set_trace()
