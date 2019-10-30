import csv
import os
from pymongo import MongoClient

#client = MongoClient("mongodb://root:Gf7t418E12@b4e16e1.online-server.cloud:22")
#client = MongoClient("mongodb://root:Gf7t418E12@b4e16e1.online-server.cloud:22/?authSource=saana_db&authMechanism=SCRAM-SHA-1")
#client = MongoClient('mongodb://localhost:27017')
MONGO_HOST = "b4e16e1.online-server.cloud"
MONGO_PORT = 27017
MONGO_DB = "saana_db"
MONGO_USER = "root"
MONGO_PASS = "Gf7t418E12"
connection = MongoClient(MONGO_HOST, MONGO_PORT)
db = connection[MONGO_DB]
db.authenticate(MONGO_USER, MONGO_PASS)

#db = client.saana_db

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
