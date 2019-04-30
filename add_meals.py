from saana_lib.process import processEuphebe, processFrozenGarden, processFoodNerd, processVeestro, processFoodFlo, processFoodMatrix, match_names
import os
from saana_lib import connectMongo, model

def add_meals():
    PATH = os.getcwd()
    print('Adding Euphebe meals')
    combined = processEuphebe.process(PATH+'/csv/Euphebe/', 'menu0328.csv', 'total2.csv')
    connectMongo.insert_meal(combined)
    print('Done')

    print('Adding FoodFlo meals')
    meals,full_list = processFoodFlo.processNutrition(PATH+'/csv/FoodFlo/nutrition.csv')
    convert_dic = match_names.match_euphebe(full_list)
    changed_meals = match_names.change_names(meals,convert_dic)
    connectMongo.insert_meal(meals)
    print('Done')

    print('Adding FoodNerd meals')
    meals,full_list = processFoodNerd.processNutrition(PATH+'/csv/FoodNerd/nutrition.csv')
    convert_dic = match_names.match_euphebe(full_list)
    changed_meals = match_names.change_names(meals,convert_dic)
    connectMongo.insert_meal(meals)
    print('Done')

    print('Adding FrozenGarden meals')
    meals = processFrozenGarden.process()
    connectMongo.insert_meal(meals)
    print('Done')

    print('Adding Veestro meals')
    ingredient_meals, ingredient_list = processVeestro.processIngredients(PATH+'/csv/Veestro/ingredients0405.csv')
    nutrition_meals, nutrition_list = processVeestro.processNutrition(PATH+'/csv/Veestro/nutrition0405.csv')
    photo_meals = processVeestro.processPhoto('./csv/Veestro/veestro-meals-photos.csv')
    combined = processVeestro.combine_mealinfo(ingredient_meals, nutrition_meals, photo_meals)
    full_list = ingredient_list + nutrition_list
    convert_dic = match_names.match_euphebe(full_list)
    combined2 = match_names.change_names(combined,convert_dic)
    connectMongo.insert_meal(combined2)
    print('Done')

def add_tags():
    master_dict, columns = processFoodMatrix.processFoodMatrixCSV('foodtag0328.csv')
    connectMongo.db.tags.insert_many(list(master_dict.values()))

if __name__=="__main__":
    add_tags()

