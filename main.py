from process import processEuphebe, processFrozenGarden, processFoodNerd, processVeestro, processFoodFlo, processFoodMatrix, match_names
import os
import connectMongo
import model

PATH = os.getcwd()
print('Adding Euphebe meals')
combined = processEuphebe.process(PATH+'/csv/Euphebe/', 'menu0328.csv', 'total2.csv')
connectMongo.insert_meal(combined)
print('Done')

print('Adding FoodFlo meals')
meals,full_list = processFoodFlo.processNutrition(PATH+'nutrition.csv')
convert_dic = match_names.match_euphebe(full_list)
changed_meals = match_names.change_names(meals,convert_dic)
connectMongo.insert_meal(meals)
print('Done')

print('Adding FoodNerd meals')
meals,full_list = processFoodNerd.processNutrition(PATH+'nutrition.csv')
convert_dic = match_names.match_euphebe(full_list)
changed_meals = match_names.change_names(meals,convert_dic)
connectMongo.insert_meal(meals)
print('Done')

print('Adding FrozenGarden meals')
meals = processFrozenGarden.process()
connectMongo.insert_meal(meals)
print('Done')

print('Adding Veestro meals')
ingredient_meals, ingredient_list = processVeestro.processIngredients(PATH+'ingredients0405.csv')
nutrition_meals, nutrition_list = processVeestro.processNutrition(PATH+'nutrition0405.csv')
photo_meals = processVeestro.processPhoto('veestro-meals-photos.csv')
combined = processVeestro.combine_mealinfo(ingredient_meals, nutrition_meals, photo_meals)
full_list = ingredient_list + nutrition_list
convert_dic = match_names.match_euphebe(full_list)
combined2 = match_names.change_names(combined,convert_dic)
connectMongo.insert_meal(combined2)
print('Done')
