import processEuphebe
import processFoodMatrix
import os
import pdb
import pprint
import pickle
import time
from datetime import date
PATH = os.path.join(os.getcwd(),'csv/Euphebe/')

# TODO: These functions can be combined into one really

def match_euphebe(euphebe_all):
    # get full lists from food tag matrix and euphebe of all nutritions and ingredients
    _, matrix_columns = processFoodMatrix.processFoodMatrixCSV('foodtag0328.csv')

    # dictionary to be used to convert in 'processEuphebe()'
    convert_dic = {'pot':'potassium', 'sod': 'sodium', 'yukon gold potatoes': 'potato'}
    for each in convert_dic.values():
        matrix_columns.remove(each)

    tag_no_match = matrix_columns[:]

    for tag_keyword in matrix_columns:
        # print('--------')
        for euphebe_name in euphebe_all:
            if tag_keyword in euphebe_name:
                convert_dic[euphebe_name] = tag_keyword
                # print('{}  |  {}'.format(tag_keyword, euphebe_name))
                if euphebe_name in tag_no_match:
                    tag_no_match.remove(euphebe_name)

    #for Euphebe - keys are for Euphebe and values for food tags matrix
    keyword_dictionary = {'nut, nut butter':'nuts','brussels sprouts': 'brussel sprouts','vitamin k': 'vit k', 'insoluble fiber': 'totinfib','total fiber': 'totfib','turmeric (curcumin)': 'turmeric',\
                          'peppers, bell': ['pepper, bell','bell pepper'], 'peppers, hot':['pepper, hot','jalapeno pepper','chili pepper','poblano pepper','serrano pepper'], 'spicy powders':\
                              ['black pepper','curry, powder']}

    # print('------semi manual--------')
    for tag_keyword in tag_no_match[:]:
        if tag_keyword not in keyword_dictionary.keys():
            continue
        for euphebe_name in euphebe_all:
            val = keyword_dictionary[tag_keyword]
            if isinstance(val,(list,)):
                for tag_keyword_ in val:
                    if tag_keyword_ in euphebe_name:
                        convert_dic[euphebe_name] = tag_keyword
                        # print('{}  |  {}'.format(tag_keyword_, euphebe_name))
            else:
                if val in euphebe_name:
                    convert_dic[euphebe_name] = tag_keyword
                    if euphebe_name in tag_no_match:
                        tag_no_match.remove(euphebe_name)
                    # print('{}  |  {}'.format(tag_keyword, euphebe_name))

    return convert_dic

def match_foodnerd():
    from processFoodNerd import processNutrition
    PATH = os.path.join(os.getcwd(),'csv/FoodNerd/')
    _, full_list = processNutrition(PATH + 'nutrition.csv')
    _, matrix_columns = processFoodMatrix.processFoodMatrixCSV('foodtag313.csv')

    tag_no_match = matrix_columns[:]
    foodnerd_no_match = full_list[:]
    convert_dic = {'black pepper':'spicy powders', 'fiber. total dietary':'total fiber', 'chili powder':'spicy powders', 'energy':'cals','protein':'prot',\
                   'carbohydrate, by difference':'carb','total lipid (fat)':'fat'}
    for key, val in convert_dic.items():
        print(key,val)
        if val in tag_no_match:
            tag_no_match.remove(val)
        if key in foodnerd_no_match:
            foodnerd_no_match.remove(key)
    for tag_keyword in matrix_columns:
        print('----')
        for name in full_list:
            if tag_keyword in name:
                convert_dic[name] = tag_keyword
                print('{} | {} '.format(tag_keyword, name))
                if name in foodnerd_no_match:
                    foodnerd_no_match.remove(name)
                if tag_keyword in tag_no_match:
                    tag_no_match.remove(tag_keyword)

    pickle.dump(convert_dic,open('foodnerd_change.p','wb'))

def match_frozenGarden(full_list):
    import processFrozenGarden
    PATH = os.path.join(os.getcwd(),'csv/frozenGarden/')
    _, matrix_columns = processFoodMatrix.processFoodMatrixCSV('foodtag313.csv')

    # euphebe_no_match = full_list[:]
    convert_dic = {}
    for each in convert_dic.values():
        matrix_columns.remove(each)

    tag_no_match = matrix_columns[:]

    for tag_keyword in matrix_columns:
        print('--------')
        for euphebe_name in full_list:
            if tag_keyword in euphebe_name:
                convert_dic[euphebe_name] = tag_keyword
                print('{}  |  {}'.format(tag_keyword, euphebe_name))
                if euphebe_name in tag_no_match:
                    tag_no_match.remove(euphebe_name)
                # if tag_keyword in tag_no_match:
                #     tag_no_match.remove(tag_keyword)

    #for Euphebe - keys are for Euphebe and values for food tags matrix
    keyword_dictionary = {'nut, nut butter':'nuts','brussels sprouts': 'brussel sprouts','vitamin k': 'vit k', 'insoluble fiber': 'totinfib','total fiber': 'totfib','turmeric (curcumin)': 'turmeric',\
                          'peppers, bell': ['pepper, bell','bell pepper'], 'peppers, hot':['pepper, hot','jalapeno pepper','chili pepper','poblano pepper','serrano pepper'], 'spicy powders':\
                              ['black pepper','curry, powder','cayenne']}

    print('------semi manual--------')
    for tag_keyword in tag_no_match[:]:
        if tag_keyword not in keyword_dictionary.keys():
            continue
        for euphebe_name in tag_no_match:
            val = keyword_dictionary[tag_keyword]
            if isinstance(val,(list,)):
                for tag_keyword_ in val:
                    if tag_keyword_ in euphebe_name:
                        convert_dic[euphebe_name] = tag_keyword
                        print('{}  |  {}'.format(tag_keyword_, euphebe_name))
                        if euphebe_name in tag_no_match:
                            tag_no_match.remove(euphebe_name)
                        if tag_keyword in tag_no_match:
                            tag_no_match.remove(tag_keyword)
            else:
                if val in euphebe_name:
                    convert_dic[euphebe_name] = tag_keyword
                    if euphebe_name in tag_no_match:
                        tag_no_match.remove(euphebe_name)
                    print('{}  |  {}'.format(tag_keyword, euphebe_name))
                    if tag_keyword in tag_no_match:
                        tag_no_match.remove(tag_keyword)

    return convert_dic
    # pickle.dump(convert_dic,open('euphebe_change_'+DATE+'.p','wb'))

def change_names(combined,convert_dic):
    for meal in combined:
        for ingredient in list(meal.ingredients.keys())[:]:
            for key_word in convert_dic.keys():
                if key_word in ingredient:
                    #MANUAL
                    if key_word == 'pot' and 'potato' in ingredient:
                        continue
                    meal.ingredients[convert_dic[key_word]] = meal.ingredients.pop(ingredient)
                    # print('changed {} --> {}'.format(ingredient,convert_dic[key_word]))
                    break
        for nutrition in list(meal.nutrition.keys())[:]:
            for key_word in convert_dic.keys():
                if key_word in nutrition:
                    #MANUAL
                    if convert_dic[key_word] == 'cals' and nutrition != 'cals':
                        continue
                    if nutrition == 'fatcals':
                        pdb.set_trace()
                    meal.nutrition[convert_dic[key_word]] = meal.nutrition.pop(nutrition)
                    # print('changed {} --> {}'.format(nutrition,convert_dic[key_word]))
    return combined

if __name__ == "__main__":
    # match_foodnerd()
    match_euphebe()
    # match_frozenGarden()
