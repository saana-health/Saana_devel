import csv
import pickle
import pprint
import pdb
import os
from model import Meal
from difflib import SequenceMatcher
from connectMongdo import add_meals
# from utils import unicodetoascii
import re

PATH = os.path.join(os.getcwd(),'csv/frozenGarden/')

def similar(a,b):
    return SequenceMatcher(None,a,b).ratio() > 0.76

def processNutrition(filename):
    '''

    :param filename:
    :return:
    '''
    from s3bucket import get_image_url
    with open(filename) as csvfile:
        ingredients = {}
        nutritions = {}

        reader_list = list(csv.reader(csvfile))
        meal_name = reader_list[1][0].lower()
        columns = [x.strip().lower().replace('.',',') for x in reader_list[3]]
        # for each in columns:
        #     # print(each.encode('utf-8').decode('unicode_escape'))
        #     # print(each.decode().encode('utf-8'))
        #     print(each.encode('utf-8'))
        # columns = [x.strip().lower().replace('\\xc2\\xac\\xc2\\xb','n') if '\\xc2\\xac\\xc2\\xb' in x else x.strip().lower() for x in list(reader_list[3])]


        units = [re.search('\(.{0,3}\)',columns[y]).group()[1:-1] if re.search('\(.{0,3}\)',columns[y]) else '' for y in range(len(columns))]
        for i in range(len(columns)):
            name = columns[i].replace(' ('+units[i]+')','')
            columns[i] = name
        # test = columns[-5][10]

        for row in range(4,len(reader_list)-2):
            ingredients[reader_list[row][0].strip().lower().replace('.',',')] = reader_list[row][1]
        for ind in range(len(units)):
            if units[ind] == '':
                continue
            nutritions[columns[ind]] = reader_list[-2][ind].replace('.',',') + ' ' + units[ind]
        new_meal = Meal(name = meal_name, ingredients=ingredients, nutrition= nutritions, supplierID='FrozenGarden', image=get_image_url(meal_name))
        return new_meal, list(ingredients.keys()) + list(set(columns))

def process():
    full_list = []
    meals = []
    from match_names import match_frozenGarden, change_names
    for filename in os.listdir(PATH):
        if filename[0] != '.':
            meal, columns = processNutrition(PATH+filename)
            meals.append(meal)
            full_list += columns
    convert_dic = match_frozenGarden(full_list)
    meals = change_names(meals, convert_dic)
    return meals

if __name__ == "__main__":
    from connectMongo import insert_meal
    meals = process()
    insert_meal(meals)
