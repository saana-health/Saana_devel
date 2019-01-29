from pymongo import MongoClient
import pickle
import pdb
import pprint
from processEuphebe import Meal
from proccessFoodMatrix import processFoodMatrixCSV
from difflib import SequenceMatcher
from webscrap.dri import submit_form

client = MongoClient("mongodb+srv://admin:thalswns1!@cluster0-jblst.mongodb.net/test")
db = client.test

def avoid():
    patient_collection = db.patients
    patient = patient_collection.find_one()

    # get tags
    tags = db.tags.find_one({'_id':patient['disease']})

    # get meals
    li = []
    meals = db.meals.find()
    for meal in meals:
        new = False
        ingredients = meal['ingredients']
        nutritions = meal['nutrition']
        # pdb.set_trace()
        for avoid in tags['avoid']:
            if new:
                break
            for ingredient in ingredients:
                if SequenceMatcher(None,ingredient,avoid).ratio()>0.6:
                    new = True
                    break
        if not new:
            li.append(meal)

        for prior in tags['prior']:
            for nutrition in nutritions:
                r = SequenceMatcher(None,prior.lower(),nutrition.lower()).ratio()
                if r > 0.6:
                    print('{} matched {} with {} by {} %'.format(meal['name'],prior,nutrition,r ))
            for ingredient in ingredients:
                r = SequenceMatcher(None,ingredient.lower(),prior.lower()).ratio()
                if r > 0.6:
                    print('{} matched {} with {} by {}%'.format(meal['name'],prior,ingredient,r))
    return li

def knapSack(W, wt, n):
    val = wt
    K = [[[0,[]] for x in range(W+1)] for x in range(n+1)]

    for i in range(n+1):
        for w in range(W+1):
            if i==0 or w==0:
                K[i][w][0] = 0
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
    cal_l = []
    for each in li:
        try:
            cal_l.append(int(each['nutrition']['Cals (kcal)']))
        except:
            pdb.set_trace()
    calorie, ind= knapSack(2350,cal_l,3)
    return calorie, [li[x] for x in ind]



if __name__ == "__main__":
    cal, result = optimize(avoid())
    pdb.set_trace()
