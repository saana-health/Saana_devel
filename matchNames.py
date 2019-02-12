import processEuphebe
import processFoodNerd
from processFoodMatrix import processFoodMatrixCSV
import os
import pickle
import pprint
import difflib
import pdb

#TODO: name matching based on name from Food Matrix is 'in' the name from food supplier name

def display_names(list1, list2):
    '''
    This function displays two lists to compare.
    :param list1: [str] nutrition/ingredients to display
    :param list2: [str] ^
    :return: None
    '''
    x = 0
    print(' > Record indexes for which two ingredients/nutritons ARE identical')
    for a in list1:
        print('-------{}------'.format(a))
        for b in list2:
            r = difflib.SequenceMatcher(None,a.lower(),b.lower()).ratio()
            if 0.6 > r > 0.5:
                l = ' '*(15 - len(a) - len(str(x)))
                print('{} {}{}|{}'.format(str(x),a,l,b))
                x += 1
    print('##########################')
    x = 0
    print(' > Record indexes for which two ingredients/nutritons are NOT identical')
    for a in list1:
        print('-------{}------'.format(a))
        for b in list2:
            r = difflib.SequenceMatcher(None,a.lower(),b.lower()).ratio()
            if r >= 0.6:
                l = ' '*(15 - len(a) - len(str(x)))
                print('{} {}{}|{}'.format(str(x),a,l,b))
                x += 1

def match_names(list1,list2, gr_then_5, gr_then_6):
    '''
    Based on display_names(), indexes of pairs of identical names are identified. Based on the indexes, map them together and create a dictionary
    :param list1: [str] nutrition/ingredients list to map
    :param list2: [str] ^
    :param gr_then_5: str - name of a pickle file that includes indexes of names that have similarity 0.5 < ratio < 0.6 but ARE identical
    :param gr_then_6: str - name of a pickle file that includes indexes of names that have similarity ratio > 0.6 but ARE NOT identical
    :return: {str: [str]}
    '''
    map_dict = {}
    index_6 = pickle.load(open(gr_then_6,'rb'))
    index_5 = pickle.load(open(gr_then_5,'rb'))
    x = 0
    y = 0
    for a in list1:
        for b in list2:
            r = difflib.SequenceMatcher(None,a.lower(),b.lower()).ratio()
            if r >= 0.6:
                if x not in index_6:
                    if a not in d.keys():
                        map_dict[a] = [b]
                    else:
                        map_dict[a].append(b)
                x += 1
                continue
            if 0.6 > r > 0.5:
                if y in index_5:
                    if a not in d.keys():
                        map_dict[a] = [b]
                    else:
                        mapd_dict[a].append(b)
                y += 1

    pickle.dump(map_dict,open(gr_then_5.split('Gr')[0]+'_matched.p','wb'))
    return map_dict

def _auto(new_dict,a_):
    '''
    Utils function that automates addition of dictionaries in a list
    :param new_dict: {str: [str]} - input dictionary to add more
    :param a_: {str: [str]} - another dictionary to add to new_dict
    :return: {str: [str]} - new_dict after added
    '''
    for each in a_.keys():
        try:
            new_dict[each] = new_dict[each] + a_[each]
        except:
            new_dict[each] = a_[each]
    return new_dict

def combine_matched(filenames,save_name):
    '''
    This function opens all the files with mapped dictionaries and collapse all together into a single master dictionary
    :param filenames: [str] - names of files to combine
    :param save_name: str - name of a file to svae
    :return:  {str: [str]} - combined mapped dictionary
    '''
    new_dict = {}
    for filename in filenames:
        file = pickle.load(open(filename,'rb'))
        new_dict = _auto(new_dict,file)

    pickle.dump(new_dict,open(save_name,'wb'))
    return new_dict

def match_euphebe():
    '''
    This function maps Euphebe ingredient/nutrition names to those from Food Matrix, following the steps below:
    1) process food matrix
    2) process Euphebe info xlsx
    3) display names to manually get indexes of identical pairs of names
    4) based on the indexes, map the names to create a dictionary
    :return: {str: [str]} mapped dictionary
    TODO: process food matrix only once?
    '''
    PATH = os.path.join(os.getcwd(),'csv/Euphebe/')
    PICKLE_PATH = os.path.join(os.getcwd(),'pickle/Euphebe/')
    master_dict, column_matrix = processFoodMatrixCSV('')
    items, column_Euphebe = processEuphebe.processNutrition(PATH+'nutrition.csv')
    display_names(column_matrix,column_Euphebe)
    result = match_names(column_matrix, column_Euphebe,  PICKLE_PATH + 'EuphebeGr5.p',PICKLE_PATH + 'EuphebeGr6.p')
    return result, PICKLE_PATH

def match_foodnerd():
    '''
    This function maps FoodNerd ingredient/nutrition names to those from Food Matrix, following the steps below:
    1) process food matrix
    2) process Food Nerdinfo xlsx
    3) display names to manually get indexes of identical pairs of names
    4) based on the indexes, map the names to create a dictionary
    :return: {str: [str]} mapped dictionary
    '''
    master_dict, column_matrix = processFoodMatrixCSV('')
    PATH = os.path.join(os.getcwd(),'csv/FoodNerd/')
    PICKLE_PATH = os.path.join(os.getcwd(),'pickle/FoodNerd/')
    items, column_FoodNerd= processFoodNerd.processNutrition(PATH+'nutrition.csv')
    display_names(column_matrix,column_FoodNerd)
    result = match_names(column_matrix, column_FoodNerd, PICKLE_PATH + 'FoodNerdGr5.p',PICKLE_PATH + 'FoodNerdGr6.p')
    return result, PICKLE_PATH

def change_name(lookup_dict, nutrition):
    '''
    A function for substituting a food supplier's own ingredient/nutrition name with a mapped name from Food Matrix
    :param lookup_dict: {str: [str]} - This is the returned 'result' from combined_matched() function
    :param nutrition: str - name from info sheet from food suppliers
    :return: str - return original name if in the dictionary, else return mapped value
    '''
    for key, value in lookup_dict.items():
        if nutrition in value:
            return key
    return nutrition

if __name__ == "__main__":
    euphebe, euphebe_pickle_path = match_euphebe()
    foodnerd, foodnerd_pickle_path = match_foodnerd()
    result = combine_matched([foodnerd_pickle_path + 'FoodNerd_matched.p',euphebe_pickle_path +'Euphebe_matched.p'],os.path.join(os.getcwd(),'pickle/')+'euphebeNfoodnerd.p')