import csv
import pprint
import pdb
import os
from model import Meal
from difflib import SequenceMatcher
from connectMongo import add_meals, get_ingredient,insert_meal
from utils import similar
from match_names import match_euphebe, change_names

PATH = os.path.join(os.getcwd(),'csv/Veestro/')

def processIngredients(filename):
    with open(filename) as csvfile:
        meals = []
        full_list = []
        reader_list = list(csv.reader(csvfile))
        ingredients = {}
        is_new_meal = True
        for row in reader_list:
            name = row[0].lower()
            if name != '':
                if is_new_meal:
                    new_meal = Meal(name = name, supplierID = 'Veestro')
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
        for row in reader_list[17:]:
            name = row[0].lower()
            if '  ' in name:
                continue
            for col_index in range(1,len(columns)):
                nutrition[columns[col_index]] = row[col_index].lower()
            new_meal = Meal(name = name,nutrition = nutrition)
            meals.append(new_meal)
            nutrition = {}
    return meals, list(set(columns))

def processPhoto(filename):
    meals = []
    with open(filename) as csvfile:
        reader_list = list(csv.reader(csvfile))
        for row in reader_list[1:]:
            new_meal = Meal(name = row[0].lower(), image = 'https:'+row[1])
            meals.append(new_meal)
    return meals

def combine_mealinfo(ingredient_meals, nutrition_meals, photo_meals):
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
        for photo_meal in photo_meals:
            if similar(ingredient_meal.name, photo_meal.name,0.8) or photo_meal.name in ingredient_meal.name or ingredient_meal.name in photo_meal.name:
                # print('{}   |   {}'.format(ingredient_meal, nutrition_meal))
                ingredient_meal.image= photo_meal.image
                cnt +=1
                photo_meals.remove(photo_meal)
                break
        meals.append(ingredient_meal)
    return meals

if __name__ == '__main__':
    print('Adding Veestro meals')
    ingredient_meals, ingredient_list = processIngredients(PATH+'ingredients0405.csv')
    nutrition_meals, nutrition_list = processNutrition(PATH+'nutrition0405.csv')
    photo_meals = processPhoto('veestro-meals-photos.csv')
    combined = combine_mealinfo(ingredient_meals, nutrition_meals, photo_meals)
    full_list = ingredient_list + nutrition_list
    convert_dic = match_euphebe(full_list)
    combined2 = change_names(combined,convert_dic)
    insert_meal(combined2)
    print('Done')
