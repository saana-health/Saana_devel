import csv
import os
from pymongo import MongoClient
from urllib.parse import quote_plus
import conf


client = MongoClient('mongodb://{}:{}@{}:{}'.format(
    quote_plus(conf.DATABASE_USER),
    quote_plus(conf.DATABASE_PASSWORD),
    quote_plus(conf.DATABASE_ADDRESS),
    quote_plus(conf.DATABASE_PORT),
))

db = client.saana_db

#client = MongoClient('mongodb://localhost:27017')

ingredient_db = db.mst_food_ingredients

##data = {}
##data['name'] = "celery"
##
##result = ingredient_db.insert_one(data)
##print('One post: {0}'.format(result.inserted_id))

PATH = os.path.join(os.getcwd(),'csv/')
ingredient_list = []
def processIngredients(filename):
    with open(filename) as csvfile:
        
        reader_list = list(csv.reader(csvfile))
        ingredients = {}
        for row in reader_list:
            name = row[0].lower()
            print(name, type(name))
            ingredients['name'] = name
            ingredient_list.append(ingredients)
            ingredients = {}
            

        
##            if name != '':
##                if is_new_meal:
##                    new_meal = Meal(name = name, supplierID = connectMongo.db.users.find_one({'first_name':'Veestro'})['_id'])
##                    is_new_meal = False
##                else:
##                    full_list.append(name)
##                    ingredients[name] = 0
##            else:
##                is_new_meal = True
##                new_meal.ingredients = ingredients
##                meals.append(new_meal)
##                ingredients = {}
##    return meals, list(set(full_list))

processIngredients(PATH+'ingredient-list.csv')
ingredient_db.insert_many(ingredient_list)
