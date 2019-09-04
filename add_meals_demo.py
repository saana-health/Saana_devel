from saana_lib.process import processColruyt, processOisix, processEuphebe, processFrozenGarden, processFoodNerd, processVeestro, processFoodFlo, processFoodMatrix, match_names
import os
from saana_lib import connectMongo, model


def add_meals():
    PATH = os.getcwd()
    print('Adding Colruyt meals')
    ingredient_meals, ingredient_list = processColruyt.processIngredients(PATH+'/csv/Colruyt/demo_ingredients.csv')
    nutrition_meals, nutrition_list = processColruyt.processNutrition(PATH+'/csv/Colruyt/demo_nutrition.csv')
    combined = processColruyt.combine_mealinfo(ingredient_meals, nutrition_meals)
    full_list = ingredient_list + nutrition_list
    convert_dic = match_names.match_euphebe(full_list)
    combined2 = match_names.change_names(combined,convert_dic)
    combined2 = match_names.get_type(combined2)
    connectMongo.insert_meal(combined2)
    print('Done')

if __name__=="__main__":
    add_meals()
