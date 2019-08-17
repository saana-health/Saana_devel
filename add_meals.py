from saana_lib.process import processEuphebe, processFrozenGarden, processFoodNerd, processVeestro, processFoodFlo, processFoodMatrix, match_names
import os
from saana_lib import connectMongo, model

def add_meals():
    PATH = os.getcwd()
    print('Adding Euphebe meals')
    combined = processEuphebe.process(PATH+'/csv/Euphebe/', 'menu0328_updated.csv', 'total2.csv')
    combined = match_names.get_type(combined)
    connectMongo.insert_meal(combined)
    print('Done')

   # print('Adding FoodFlo meals')
   # meals,full_list = processFoodFlo.processNutrition(PATH+'/csv/FoodFlo/nutrition.csv')
   # convert_dic = match_names.match_euphebe(full_list)
   # changed_meals = match_names.change_names(meals,convert_dic)
   # combined = match_names.get_type(changed_meals)
   # connectMongo.insert_meal(combined)
   # print('Done')

    print('Adding FoodNerd meals')
    meals,full_list = processFoodNerd.processNutrition(PATH+'/csv/FoodNerd/nutrition.csv')
    convert_dic = match_names.match_euphebe(full_list)
    changed_meals = match_names.change_names(meals,convert_dic)
    combined = match_names.get_type(changed_meals)
    connectMongo.insert_meal(combined)
    print('Done')

    print('Adding FrozenGarden meals')
    meals = processFrozenGarden.process()
    combined = match_names.get_type(meals)
    connectMongo.insert_meal(combined)
    print('Done')

    print('Adding Veestro meals')
    ingredient_meals, ingredient_list = processVeestro.processIngredients(PATH+'/csv/Veestro/ingredients_test_0816.csv')
    nutrition_meals, nutrition_list = processVeestro.processNutrition(PATH+'/csv/Veestro/nutrition_0816_test.csv')
    photo_meals = processVeestro.processPhoto('./csv/Veestro/meals_photos_test_0816.csv')
    combined = processVeestro.combine_mealinfo(ingredient_meals, nutrition_meals, photo_meals)
    full_list = ingredient_list + nutrition_list
    convert_dic = match_names.match_euphebe(full_list)
    combined2 = match_names.change_names(combined,convert_dic)
    combined2 = match_names.get_type(combined2)
    connectMongo.insert_meal(combined2)
    print('Done')

def add_tags():
    print("Processing Food Tags Matrix")
    master_dict, columns = processFoodMatrix.processFoodMatrixCSV('foodtag0817.csv')
    connectMongo.db.tags.insert_many(list(master_dict.values()))

if __name__=="__main__":
    add_tags()
    #add_meals()

