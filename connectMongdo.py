from pymongo import MongoClient
import pickle
import pdb
import pprint
from model import Meal, MealHistory,MealList

client = MongoClient("mongodb+srv://admin:thalswns1!@cluster0-jblst.mongodb.net/test")
db = client.test

def add_tags(tag_dict):
    '''
    This function adds tag_dict into a db on MongoDB atlas
    :param tag_dict: return dictionary of processFoodMatrix.processFoodMatrixCSV
    :return: True/False based on successfulness
    '''
    tags = db.tags
    l = []
    result = tags.insert_many(tag_dict.values())
    return True

def add_meals(meal_list = [],pickle_name = ''):
    '''

    :param pickle_name: (str)name of the pickle
    :return: True
    '''
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

def add_meal_history(meal_history,id):
    '''
    This function adds meal info (list of meals ordered/planned for a week) to the MongoDB database
    :param meal_history: [class MealHistory]
    :return: True if successful
    '''
    existing_history = db.mealInfo.find_one({'patient_id': id})
    if existing_history is None:
        meal_history_dict = {}
        meal_history_dict['patient_id'] = meal_history.patient_id
        meal_history_dict['week_' + str(meal_history.week_num)] = {'meal_list': meal_history.meal_list}
        db.mealInfo.insert_one(meal_history_dict)
    else:
        db.mealInfo.update({'patient_id':id},{'$set': {'week_'+str(meal_history.week_num): {'meal_list':meal_history.meal_list}}})
    return True

def find_meal(name):
    '''
    This function finds a meal based on its name
    :param name: str - name of a meal
    :return: {mealInfo}
    '''
    meal = db.meals.find_one({"name":name})
    return meal

def find_patient(name):
    '''
    This function finds a patient based on her/his name
    :param name: str - name of a patient
    :return: {(patient info)}
    '''
    patient = db.patients.find_one({"name":name})
    return patient

def get_all_meals():
    cursor = db.meals.find()
    meals = MealList()
    for meal in cursor:
        # meals.append(Meal().import_dict(meal))
        meals.append(meal)

    return meals

def get_mealinfo_by_patient(id):
    mealinfo = db.mealInfo.find_one({'patient_id': id})
    return mealinfo

def get_all_tags():
    return db.tags.find()

def get_all_patients():
    return db.patients.find()

if __name__ == "__main__":
    pass
