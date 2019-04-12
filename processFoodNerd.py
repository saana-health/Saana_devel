import csv
import pickle
import pprint
import pdb
import os
from model import Meal
from difflib import SequenceMatcher
from connectMongo import insert_meal
from utils import unicodetoascii
from match_names import match_euphebe, change_names

PATH = os.path.join(os.getcwd(),'csv/FoodNerd/')

def processNutrition(filename):
    '''

    :param filename:
    :return:
    #TODO: unit conversion (right now, everything is set to 1 unit = 150g
    '''
    from s3bucket import get_image_url
    from connectMongo import get_supplier
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
        columns = [x.lower().replace('.',',') for x in list(reader_list[1])]
        units = reader_list[2]

        prev_type = ''
        # loop through each row starting 3rd row
        for i in range(4,len(reader_list)):
            first_word = reader_list[i][0].split(' ')[0]
            # Type
            if first_word  in ['Breakfast','Lunch','Dinner']:
                type = first_word.lower()

            # Meal name
            elif first_word != '':
                name = reader_list[i][0].lower()
                ingredient = reader_list[i][1].lower().replace('.',',')

                # TODO: grams measurement
                ingredients[ingredient] = float(reader_list[i][3])*150
                full_list.append(ingredient)
            elif first_word == '':
                if reader_list[i][1] == 'TOTAL':
                    for j in range(4,len(reader_list[i])):
                        if reader_list[i][j].replace('.','').isdigit() and float(reader_list[i][j]) != 0:
                            nutritions[columns[j]] = str(float(reader_list[i][j])) + ' ' + units[j]
                    new_meal = Meal(name = name,ingredients = ingredients, nutrition = nutritions, type = type, supplierID = get_supplier('FoodNerd')['_id'], image = get_image_url(name))
                    meals.append(new_meal)
                    ingredients = {}
                    nutritions = {}
                elif '%' not in reader_list[i][1] and reader_list[i][1] != '':
                    ingredient = reader_list[i][1].lower().replace('.',',')
                    if reader_list[i][3] != '':
                        ingredients[ingredient] = float(reader_list[i][3])*150
                    if ingredient not in full_list:
                        full_list.append(ingredient)
    return meals, list(set(full_list + columns))

if __name__ == "__main__":
    print('Adding FoodNerd meals')
    meals,full_list = processNutrition(PATH+'nutrition.csv')
    convert_dic = match_euphebe(full_list)
    changed_meals = change_names(meals,convert_dic)
    insert_meal(meals)
    print('Done')

    # from utils import create_histogram
    # create_histogram(meals,'tomato')
