from saana_lib.process import processEuphebe, processFrozenGarden, processFoodNerd, processVeestro, processFoodFlo, processFoodMatrix, match_names
import os
from saana_lib import connectMongo, model

def add_meals():
	print('Adding Oisix meals')
    ingredient_meals, ingredient_list = processOisix.processIngredients(PATH+'/csv/Oisix/demo_ingredients.csv')
    nutrition_meals, nutrition_list = processOisix.processNutrition(PATH+'/csv/Oisix/demo_nutrition.csv')
    # photo_meals = processVeestro.processPhoto('./csv/Veestro/veestro-meals-photos.csv')
    combined = processOisix.combine_mealinfo(ingredient_meals, nutrition_meals)
    full_list = ingredient_list + nutrition_list
    convert_dic = match_names.match_euphebe(full_list)
    combined2 = match_names.change_names(combined,convert_dic)
    combined2 = match_names.get_type(combined2)
    connectMongo.insert_meal(combined2)
    print('Done')