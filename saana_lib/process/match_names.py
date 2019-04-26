from . import processFoodMatrix
import os

PATH = os.path.join(os.getcwd(),'csv/Euphebe/')

def match_euphebe(euphebe_all):
    # get full lists from food tag matrix and euphebe of all nutritions and ingredients
    _, matrix_columns = processFoodMatrix.processFoodMatrixCSV('foodtag0328.csv')

    # dictionary to be used to convert (exact match)
    convert_dic = {'sod':'sodium','pot':'potassium', 'sod': 'sodium', 'yukon gold potatoes': 'potato', 'fiber, total dietary':'total fiber',\
                   'energy':'cals', 'fiber':'total fiber', 'calories': 'cals'}

    tag_no_match = matrix_columns[:]
    fulllist_no_match = euphebe_all[:]

    for tag_keyword in matrix_columns:
        for euphebe_name in euphebe_all:
            if tag_keyword in euphebe_name:
                convert_dic[euphebe_name] = tag_keyword
                # print('{}  |  {}'.format(tag_keyword, euphebe_name))
                if euphebe_name in fulllist_no_match:
                    fulllist_no_match.remove(euphebe_name)

    #keys are for supplier and values for food tags matrix (inexact ($in) match)
    keyword_dictionary = {'nut, nut butter':'nuts','brussels sprouts': 'brussel sprouts','vitamin k': 'vit k', 'insoluble fiber': 'totinfib','total fiber': 'totfib','turmeric (curcumin)': 'turmeric',\
                          'peppers, bell': ['pepper, bell','bell pepper', 'red pepper', 'green pepper'], 'peppers, hot':['pepper, hot','jalapeno pepper','jalape',  'chili pepper','poblano pepper','serrano pepper'], 'spicy powders':\
                              ['black pepper','curry, powder', 'curry powder','chili powder','cayenne','spices, pepper'], 'cals':'calories',\
                          'turmeric':'tumeric', 'green beans':'green peas','bean':['chickpea','chickpeas', 'peas'], 'soy':'tofu'}

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
                        if euphebe_name in fulllist_no_match:
                            fulllist_no_match.remove(euphebe_name)
            else:
                if val in euphebe_name:
                    convert_dic[euphebe_name] = tag_keyword
                    if euphebe_name in tag_no_match:
                        tag_no_match.remove(euphebe_name)
                    # print('{}  |  {}'.format(tag_keyword, euphebe_name))
                    if euphebe_name in fulllist_no_match:
                        fulllist_no_match.remove(euphebe_name)
    # pdb.set_trace()
    return convert_dic

def change_names(combined,convert_dic):
    cnt = 0
    for meal in combined[:]:
        for ingredient in list(meal.ingredients.keys())[:]:
            for key_word in convert_dic.keys():
                if key_word in ingredient:
                    if key_word == 'pot' and 'potato' in ingredient:
                        continue
                    #MANUAL
                    combined.remove(meal)
                    meal.ingredients[convert_dic[key_word]] = meal.ingredients.pop(ingredient)
                    cnt += 1
                    combined.append(meal)
                    # print('changed {} --> {}'.format(ingredient,convert_dic[key_word]))
                    break
        for nutrition in list(meal.nutrition.keys())[:]:
            for key_word in convert_dic.keys():
                if key_word == nutrition:
                    #MANUAL
                    combined.remove(meal)
                    meal.nutrition[convert_dic[key_word]] = meal.nutrition.pop(nutrition)
                    cnt += 1
                    combined.append(meal)
    # print('{} items changed'.format(cnt))
    return combined

if __name__ == "__main__":
    # match_foodnerd()
    match_euphebe()
    # match_frozenGarden()
