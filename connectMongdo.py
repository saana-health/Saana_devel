from pymongo import MongoClient
import pickle
import pdb
import pprint
from model import Meal, MealHistory


def add_tags(tag_dict):
    '''
    This function adds tag_dict into a db on MongoDB atlas
    :param tag_dict: return dictionary of processFoodMatrix.processFoodMatrixCSV
    :return: True/False based on successfulness
    '''
    client = MongoClient("mongodb+srv://admin:thalswns1!@cluster0-jblst.mongodb.net/test")
    db = client.test
    tags = db.tags
    l = []
    result = tags.insert_many(tag_dict.values())
    return True

def add_meals(meal_list = [],pickle_name = ''):
    '''

    :param pickle_name: (str)name of the pickle
    :return: True
    '''
    client = MongoClient("mongodb+srv://admin:thalswns1!@cluster0-jblst.mongodb.net/test")
    db = client.test
    if not meal_list:
        meal_list = pickle.load( open(pickle_name,'rb'))
    meals = db.meals

    l = []
    for each in meal_list:
        new_dict = {}
        new_dict['name'] = each.name
        new_dict['nutrition'] = each.nutrition
        new_dict['ingredients'] = each.ingredients
        new_dict['supplierID'] = each.supplierID
        new_dict['price'] = each.price
        new_dict['type'] = each.type
        l.append(new_dict)
    meals.insert_many(l)
    return True

def add_meal_history(meal_history):
    client = MongoClient("mongodb+srv://admin:thalswns1!@cluster0-jblst.mongodb.net/test")
    db = client.test
    meal_history_dict = {}
    meal_history_dict['patient_id'] = meal_history.patient_id
    meal_history_dict['week_num'] = meal_history.week_num
    meal_history_dict['meal_list'] = meal_history.meal_list
    db.mealInfo.insert_one(meal_history_dict)
    return True

def find_meal(name):
    client = MongoClient("mongodb+srv://admin:thalswns1!@cluster0-jblst.mongodb.net/test")
    db = client.test
    meal = db.meals.find_one({"name":name})
    return meal

def find_patient(name):
    client = MongoClient("mongodb+srv://admin:thalswns1!@cluster0-jblst.mongodb.net/test")
    db = client.test
    patient = db.patients.find_one({"name":name})
    return patient

if __name__ == "__main__":
    pass
