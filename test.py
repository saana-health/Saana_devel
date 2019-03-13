import processEuphebe
import processFoodMatrix
import os
import pdb
import pprint
import pickle
PATH = os.path.join(os.getcwd(),'csv/Euphebe/')

if __name__ == "__main__":
    master_dict, matrix_columns = processFoodMatrix.processFoodMatrixCSV('new.csv')
    menus = processEuphebe.processMenu(PATH + 'menu.csv')
    items, euphebe_all = processEuphebe.processNutrition(PATH+'nutrition.csv')
    mapped, not_found = processEuphebe.mapToMeal(menus, items)
    newly_mapped = processEuphebe.manual_input(menus,not_found,mapped)
    combined = processEuphebe.combine_nutrition(newly_mapped)

    euphebe_not_matched = euphebe_all[:]

    convert_dic = {'pot':'potassium', 'sod': 'sodium', 'yukon gold potatoes': 'potato'}
    for each in convert_dic.values():
        matrix_columns.remove(each)
    not_matched = matrix_columns[:]
    for each1 in matrix_columns:
        print('--------')
        for each2 in euphebe_all:
            if each1 in each2:
                convert_dic[each2] = each1
                print('{}  |  {}'.format(each1, each2))
                if each2 in euphebe_not_matched:
                    euphebe_not_matched.remove(each2)
                if each1 in not_matched:
                    not_matched.remove(each1)

    #for Euphebe
    keyword_dictionary = {'nut, nut butter':'nuts','brussel sprouts': 'brussels sprouts','vitamin k': 'vit k', 'fiber': 'totfib','turmeric (curcumin)': 'turmeric',\
                          'pepper, bell': 'bell pepper', 'pepper, hot':['jalapeno pepper','chili pepper','poblano pepper','serrane pepper'], 'spicy powder':\
                              ['black pepper','curry, powder']}

    print('------semi manual--------')
    temp = not_matched[:]
    for each1 in temp:
        if each1 not in keyword_dictionary.keys():
            print('{} skipped'.format(each1))
            continue
        for each2 in euphebe_all:
            val = keyword_dictionary[each1]
            if isinstance(val,(list,)):
                for each1_ in val:
                    if each1_ in each2:
                        convert_dic[each2] = each1
                        print('{}  |  {}'.format(each1_, each2))
                        if each2 in euphebe_not_matched:
                            euphebe_not_matched.remove(each2)
                        if each1 in not_matched:
                            not_matched.remove(each1)
            else:
                if val in each2:
                    convert_dic[each2] = each1
                    if each2 in euphebe_not_matched:
                        euphebe_not_matched.remove(each2)
                    print('{}  |  {}'.format(each1, each2))
                    if each1 in not_matched:
                        not_matched.remove(each1)
    pickle.dump(convert_dic,open('euphebe_change.p','wb'))

