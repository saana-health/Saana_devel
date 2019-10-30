import csv
import os
from pymongo import MongoClient
from recipe_extractor import *

client = MongoClient('mongodb://localhost:27017')
db = client.saana_db

ingredient_recipes = db.mst_recipes

PATH = os.path.join(os.getcwd(),'csv/')
recipe_list = []

def processRecipes(filename):
    j = 0
    with open(filename) as csvfile:
        
        reader_list = list(csv.reader(csvfile))
        recipes = {}
        for row in reader_list:
            name = row[0].lower()
            print(name, type(name))
            if j > 0:
                extract_recipe_main(name)
            j += 1
            #recipe_db.insert_one({'url': name})

         #   extract_recipe_main(name)
##            recipes['name'] = name
##            recipes_list.append(ingredients)
##            recipes = {}
            
processRecipes(PATH+'wfpb_recipes.csv')
#recipes_db.insert_many(ingredient_list)
