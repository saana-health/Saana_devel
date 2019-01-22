from pymongo import MongoClient
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

if __name__ == "__main__":
    add_tags(processFoodMatrixCSV(''))