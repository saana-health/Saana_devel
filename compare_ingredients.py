import csv
import os
from pymongo import MongoClient
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from pymongo import MongoClient
from urllib.parse import quote_plus
import conf


client = MongoClient('mongodb://{admin}:{g3am1ba5ck9de8er}@127.0.0.1', authSource='saana_db')

db = client.saana_dbb


##client = MongoClient('mongodb://localhost:27017')

ingredient_db = db.mst_food_ingredients
recipe_db = db.mst_recipes
##
##ing = {'ingredient_full_name': u' quartered artichoke heart', 'measure': u'cup',
##       'quantity': u'1', 'ingredient': u'artichoke'}
##
##str2Match = "banana"
##strOptions = ["rice","brown rice long-grain","brown rice flour pasta","brown rice flour",
##              "rice noodle", "risotto rice", "whole wheat pasta"]
##Ratios = process.extract(str2Match,strOptions)
##print(Ratios)
### You can also select the string with the highest matching percentage
##highest = process.extractOne(str2Match,strOptions)
##print(highest)


def get_ingredient_highest(ingredients):
    '''
    get ingredient id and quantity by its name
    :param ingredients: [str]
    :return: [{_id, quantity}]
    '''
    return_id = ""
    ingr = ingredients
    matching_ingredients = []
    strOptions = []
    obj = ingredient_db.find_one({'name': {'$regex':ingr}})
   # print obj
    
    if obj is None:
               
        splits = ingr.split()
        for split in splits:
            #print split
            obj2 = ingredient_db.find({'name': {'$regex':split}})
            if obj2 is None:
                print "FALSE"             
            else:
                for record in obj2:
                    #print record
                    #print record['name']
                    return_id = record['_id']
                    return_name = record['name']
                    exist_list = False 
                    length = len(matching_ingredients)
                    if length == 0:
                        matching_ingredients.append({'name':return_name, 'id':return_id})
                        strOptions.append(return_name)
                    else: 
                        for i in range(length):
                            if matching_ingredients[i]['id'] == return_id:
                                exist_list = True
                        if exist_list == False:
                            matching_ingredients.append({'name':return_name, 'id':return_id})
                            strOptions.append(return_name)
        #print matching_ingredients
        length = len(matching_ingredients)
        if length == 0:
            print "no ingredient matching in db"
            ingredient_db.insert_one({'name': ingredients})
        else:
            Ratios = process.extract(ingredients,strOptions)
            #print(Ratios)
            # You can also select the string with the highest matching percentage
            highest = process.extractOne(ingredients,strOptions)
            #print(highest)
            for i in range(length):
                if matching_ingredients[i]['name'] == highest[0]:
                    return_id = matching_ingredients[i]['id']
                                          
    else:
        
        return_id = obj['_id']
   
    return return_id

# print get_ingredient("brown rice pasta")
#print get_ingredient_highest(str2Match)
