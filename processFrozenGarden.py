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
    convert_dic = {}

    columns = []
    with open(filename) as csvfile:
        ingredients = {}
        nutritions = {}

        reader_list = list(csv.reader(csvfile))
        meal_name = reader_list[1][0]
        columns = [x.strip().lower() for x in reader_list[3]]
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
            ingredients[reader_list[row][0].strip().lower()] = reader_list[row][1]
        for ind in range(len(units)):
            if units[ind] == '':
                continue
            nutritions[columns[ind]] = reader_list[-2][ind] + ' ' + units[ind]
        new_meal = Meal(name = meal_name, ingredients=ingredients, nutrition= nutritions, supplierID='FrozenGarden')
        return list(ingredients.keys()) + list(set(columns))
        pdb.set_trace


if __name__ == "__main__":
    for filename in os.listdir(PATH):
        if filename[0] != '.':
            print(filename)
            processNutrition(PATH+filename)
