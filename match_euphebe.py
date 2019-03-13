import processEuphebe
import processFoodMatrix
import os
import pdb
import pprint
import pickle
PATH = os.path.join(os.getcwd(),'csv/Euphebe/')

if __name__ == "__main__":
    # get full lists from food tag matrix and euphebe of all nutritions and ingredients
    _, matrix_columns = processFoodMatrix.processFoodMatrixCSV('foodtag313.csv')
    items, euphebe_all = processEuphebe.processNutrition(PATH+'test2.csv')

    combined = processEuphebe.process()

    # remove matched from this list
    euphebe_tag_no_match = euphebe_all[:]

    # dictionary to be used to convert in 'processEuphebe()'
    convert_dic = {'pot':'potassium', 'sod': 'sodium', 'yukon gold potatoes': 'potato'}
    for each in convert_dic.values():
        matrix_columns.remove(each)

    tag_no_match = matrix_columns[:]

    for tag_keyword in matrix_columns:
        print('--------')
        for euphebe_name in euphebe_all:
            if tag_keyword in euphebe_name:
                convert_dic[euphebe_name] = tag_keyword
                print('{}  |  {}'.format(tag_keyword, euphebe_name))
                if euphebe_name in euphebe_tag_no_match:
                    euphebe_tag_no_match.remove(euphebe_name)
                if tag_keyword in tag_no_match:
                    tag_no_match.remove(tag_keyword)

    #for Euphebe - keys are for Euphebe and values for food tags matrix
    keyword_dictionary = {'nut, nut butter':'nuts','brussels sprouts': 'brussel sprouts','vitamin k': 'vit k', 'insoluble fiber': 'totinfib','total fiber': 'totfib','turmeric (curcumin)': 'turmeric',\
                          'peppers, bell': ['pepper, bell','bell pepper'], 'peppers, hot':['pepper, hot','jalapeno pepper','chili pepper','poblano pepper','serrano pepper'], 'spicy powders':\
                              ['black pepper','curry, powder']}

    print('------semi manual--------')
    for tag_keyword in tag_no_match[:]:
        if tag_keyword not in keyword_dictionary.keys():
            continue
        for euphebe_name in euphebe_tag_no_match:
            val = keyword_dictionary[tag_keyword]
            if isinstance(val,(list,)):
                for tag_keyword_ in val:
                    if tag_keyword_ in euphebe_name:
                        convert_dic[euphebe_name] = tag_keyword
                        print('{}  |  {}'.format(tag_keyword_, euphebe_name))
                        if euphebe_name in euphebe_tag_no_match:
                            euphebe_tag_no_match.remove(euphebe_name)
                        if tag_keyword in tag_no_match:
                            tag_no_match.remove(tag_keyword)
            else:
                if val in euphebe_name:
                    convert_dic[euphebe_name] = tag_keyword
                    if euphebe_name in euphebe_tag_no_match:
                        euphebe_tag_no_match.remove(euphebe_name)
                    print('{}  |  {}'.format(tag_keyword, euphebe_name))
                    if tag_keyword in tag_no_match:
                        tag_no_match.remove(tag_keyword)

    pickle.dump(convert_dic,open('euphebe_change.p','wb'))

