from pymongo import MongoClient
import pickle
import pdb
import pprint
from processEuphebe import Meal
from proccessFoodMatrix import processFoodMatrixCSV

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

def add_meals(pickle_name):
    '''

    :param pickle_name: (str)name of the pickle
    :return: True
    '''
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

if __name__ == "__main__":
    #add_tags(processFoodMatrixCSV(''))
    #a = add_meals('EuphebeMealInfo.p')
    pass
