import csv
import connectMongo
import os
from model import Meal
from difflib import SequenceMatcher
import re

PATH = os.path.join(os.getcwd(),'csv/frozenGarden/')

def similar(a,b):
    return SequenceMatcher(None,a,b).ratio() > 0.76

def processNutrition(filename):
    '''

    :param filename:
    :return:
    '''
    from tools.s3bucket import get_image_url
    with open(filename) as csvfile:
        ingredients = {}
        nutritions = {}

        reader_list = list(csv.reader(csvfile))
        meal_name = reader_list[1][0].lower()
        columns = [x.strip().lower().replace('.',',') for x in reader_list[3]]

        units = [re.search('\(.{0,3}\)',columns[y]).group()[1:-1] if re.search('\(.{0,3}\)',columns[y]) else '' for y in range(len(columns))]
        #get rid of units
        [columns[i].replace(' ('+units[i]+')','') for i in range(len(columns))]
        for row in range(4,len(reader_list)-2):
            ingredients[reader_list[row][0].strip().lower().replace('.',',')] = reader_list[row][1]
        for ind in range(len(units)):
            if units[ind] == '' and columns[ind] != 'calories':
                continue
            nutritions[columns[ind]] = reader_list[-2][ind].replace('.',',') + ' ' + units[ind]
        new_meal = Meal(name = meal_name, ingredients=ingredients, nutrition= nutritions, supplierID=\
            connectMongo.db.users.find_one({'first_name':'FrozenGarden'})['_id'], image=get_image_url(meal_name))
        return new_meal, list(set(list(ingredients.keys()) + columns))

def process():
    full_list = []
    meals = []
    from process.match_names import change_names, match_euphebe
    for filename in os.listdir(PATH):
        if filename[0] != '.':
            meal, columns = processNutrition(PATH+filename)
            meals.append(meal)
            full_list += columns
    convert_dic = match_euphebe(list(set(full_list)))
    meals = change_names(meals, convert_dic)
    return meals

if __name__ == "__main__":
    print('Adding FrozenGarden meals')
    meals = process()
    connectMongo.insert_meal(meals)
    print('Done')
