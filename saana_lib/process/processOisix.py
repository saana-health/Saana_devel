## 8/12/2019
## Script for processing and inputting Oisix Demo Meals
## Adapted from the Veestro Process script

import csv
import os

from ..model import Meal
from .. import connectMongo
from ..utils import similar
from .match_names import match_euphebe, change_names


# run from working directory of devel_folder
PATH = os.path.join(os.getcwd(), 'csv/Oisix/')

def processIngredients(filename):
    with open(filename) as csvfile:
        meals = []
        full_list = []
        reader_list = list(csv.reader(csvfile))
        ingredients = {}
        is_new_meal = True
        for row in reader_list:
            name = row
            print(name)
            if name != '':
                if is_new_meal:
                    # kept name as Veestro cause Oisix doesn't exist in the db right now
                    new_meal = Meal(name = name, supplierID = connectMongo.db.users.find_one({'first_name':'Veestro'})['_id'])
                    is_new_meal = False
                else:
                    full_list.append(name)
                    ingredients[name] = 0
            else:
                is_new_meal = True
                new_meal.ingredients = ingredients
                meals.append(new_meal)
                ingredients = {}
    return meals, list(set(full_list))



def processNutrition(filename):
    with open(filename) as csvfile:
        meals = []
        reader_list = list(csv.reader(csvfile))
        nutrition = {}
        columns = [x.lower() for x in reader_list[0][:8]]
        for row in reader_list[1:]:
            name = row[0].lower()
            if '  ' in name:
                continue
            for col_index in range(1,len(columns)):
                nutrition[columns[col_index]] = row[col_index].lower()
            new_meal = Meal(name = name,nutrition = nutrition)
            meals.append(new_meal)
            nutrition = {}
    return meals, list(set(columns))



def combine_mealinfo(ingredient_meals, nutrition_meals):
    cnt = 0
    meals = []
    result = []
    for ingredient_meal in ingredient_meals:
        for nutrition_meal in nutrition_meals:
            if similar(ingredient_meal.name, nutrition_meal.name,0.8) or ingredient_meal.name in nutrition_meal.name or nutrition_meal.name in ingredient_meal.name:
                # print('{}   |   {}'.format(ingredient_meal, nutrition_meal))
                ingredient_meal.nutrition= nutrition_meal.nutrition
                nutrition_meals.remove(nutrition_meal)
                break
        meals.append(ingredient_meal)
    return meals


if __name__ == '__main__':
    print('Adding Oisix meals')
    ingredient_meals, ingredient_list = processIngredients(PATH+'demo_ingredients.csv')
    nutrition_meals, nutrition_list = processNutrition(PATH+'demo_nutrition.csv')
    combined = combine_mealinfo(ingredient_meals, nutrition_meals)
    full_list = ingredient_list + nutrition_list
    convert_dic = match_euphebe(full_list)
    combined2 = change_names(combined,convert_dic)
    connectMongo.insert_meal(combined2)
    print('Done')
