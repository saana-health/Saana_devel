import csv
import pickle
import pprint
import pdb
import os
from model import Meal
from difflib import SequenceMatcher
from connectMongdo import add_meals
from utils import unicodetoascii

PATH = os.path.join(os.getcwd(),'csv/FoodNerd/')

def similar(a,b):
    return SequenceMatcher(None,a,b).ratio() > 0.76

def processNutrition(filename):
    '''

    :param filename:
    :return:
    #TODO: unit conversion (right now, everything is set to 1 unit = 150g
    '''
    convert_dic = pickle.load(open('foodnerd_change.p' , 'r'))
    columns = []
    units = []
    meals = []
    full_list = []
    with open(filename) as csvfile:
        ingredients = {}
        nutritions = {}
        reader_list = list(csv.reader(csvfile))
        is_name = True

        #first row
        columns = [convert_dic[x.lower()] if x.lower() in convert_dic.keys() else x.lower().replace('.',',') for x in list(reader_list[1])]
        # columns = [change_name(lookup_dict,x.replace('.',',')) for x in list(reader_list[1])]
        units = [y.replace('\xc2\xb5g','ng') for y in list(reader_list[2])]

        prev_type = ''
        # loop through each row starting 3rd row
        for i in range(4,len(reader_list)):
            first_word = reader_list[i][0].split(' ')[0]
            if first_word  in ['Breakfast','Lunch','Dinner']:
                type = first_word.lower()
            elif first_word != '':
                name = unicodetoascii(reader_list[i][0]).lower()
                # ingredient = change_name(lookup_dict,unicodetoascii(reader_list[i][1]))
                ingredient = unicodetoascii(reader_list[i][1]).lower()
                if ingredient in convert_dic.keys():
                    ingredient = convert_dic[ingredient]
                else:
                    ingredient = ingredient.replace('.',',')
                try:
                    ingredients[ingredient] = float(reader_list[i][3])*150
                except:
                    print(reader_list[i][3])
                continue
                if ingredient not in full_list:
                    full_list.append(ingredient)
            elif first_word == '':
                if reader_list[i][1] == 'TOTAL':
                    for j in range(4,len(reader_list[i])):
                        if reader_list[i][j].replace('.','').isdigit() and float(reader_list[i][j]) != 0:
                            nutritions[columns[j]] = str(float(reader_list[i][j])) + ' ' + units[j]
                    new_meal = Meal(name = name,ingredients = ingredients, nutrition = nutritions, type = type, supplierID = 'FoodNerd')
                    meals.append(new_meal)
                    ingredients = {}
                    nutritions = {}
                elif '%' not in reader_list[i][1] and reader_list[i][1] != '':
                    # ingredient = change_name(lookup_dict,unicodetoascii(reader_list[i][1]))
                    ingredient = unicodetoascii(reader_list[i][1]).lower()
                    if ingredient in convert_dic.keys():
                        ingredient = convert_dic[ingredient]
                    else:
                        ingredient = ingredient.replace('.',',')
                    try:
                        # TODO: conversion
                        ingredients[ingredient] = float(reader_list[i][3])*150
                    except:
                        print(reader_list[i][3])
                    if ingredient not in full_list:
                        full_list.append(ingredient)
    return meals, full_list + columns

if __name__ == "__main__":
    from matchNames import change_name
    meals,full_list = processNutrition(PATH+'nutrition.csv')
    # from utils import create_histogram
    # create_histogram(meals,'tomato')
    add_meals(meals)
    # pdb.set_trace()
