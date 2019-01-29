from pymongo import MongoClient
import pickle
import pdb
import pprint
from processEuphebe import Meal
from proccessFoodMatrix import processFoodMatrixCSV

client = MongoClient("mongodb+srv://admin:thalswns1!@cluster0-jblst.mongodb.net/test")
db = client.test

def add_tags():
    tags = db.patients
    result = tags.insert_many(tag_dict.values())
    return True

if __name__ == "__main__":
    #add_tags(processFoodMatrixCSV(''))
    #a = add_meals('EuphebeMealInfo.p')
    pass
