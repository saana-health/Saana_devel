import processEuphebe
import processFoodNerd
from processFoodMatrix import processFoodMatrixCSV
import os
import pickle
import pprint
import difflib
import pdb

def display_names(list1, list2):
    '''
    This function only to display two lists to compare.
    :param list1:
    :param list2:
    :return: dictionary
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
    This function only for 0.6 > r > 0.5. For any r > 0.6, automatically match it.
    :param list1:
    :param list2:
    :param filename:
    :return:
    '''
    d = {}
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
                        d[a] = [b]
                    else:
                        d[a].append(b)
                x += 1
                continue
            if 0.6 > r > 0.5:
                if y in index_5:
                    if a not in d.keys():
                        d[a] = [b]
                    else:
                        d[a].append(b)
                y += 1

    pickle.dump(d,open(gr_then_5.split('Gr')[0]+'_matched.p','wb'))
    return d

def _auto(new_dict,a_):
    for each in a_.keys():
        try:
            new_dict[each] = new_dict[each] + a_[each]
        except:
            new_dict[each] = a_[each]
    return new_dict

def combine_matched(filenames,save_name):
    new_dict = {}
    for filename in filenames:
        file = pickle.load(open(filename,'rb'))
        new_dict = _auto(new_dict,file)

    pickle.dump(new_dict,open(save_name,'wb'))
    return new_dict

def match_euphebe():
    PATH = os.path.join(os.getcwd(),'csv/Euphebe/')
    PICKLE_PATH = os.path.join(os.getcwd(),'pickle/Euphebe/')
    master_dict, column_matrix = processFoodMatrixCSV('')
    items, column_Euphebe = processEuphebe.processNutrition(PATH+'nutrition.csv')
    display_names(column_matrix,column_Euphebe)
    pdb.set_trace()
    result = match_names(column_matrix, column_Euphebe,  PICKLE_PATH + 'EuphebeGr5.p',PICKLE_PATH + 'EuphebeGr6.p')
    return result, PICKLE_PATH

def match_foodnerd():
    master_dict, column_matrix = processFoodMatrixCSV('')
    PATH = os.path.join(os.getcwd(),'csv/FoodNerd/')
    PICKLE_PATH = os.path.join(os.getcwd(),'pickle/FoodNerd/')
    items, column_FoodNerd= processFoodNerd.processNutrition(PATH+'nutrition.csv')
    display_names(column_matrix,column_FoodNerd)
    result = match_names(column_matrix, column_FoodNerd, PICKLE_PATH + 'FoodNerdGr5.p',PICKLE_PATH + 'FoodNerdGr6.p')
    return result, PICKLE_PATH

def change_name(lookup_dict, nutrition):
    for key, value in lookup_dict.items():
        if nutrition in value:
            return key
    return nutrition

if __name__ == "__main__":
    euphebe, euphebe_pickle_path = match_euphebe()
    foodnerd, foodnerd_pickle_path = match_foodnerd()
    result = combine_matched([foodnerd_pickle_path + 'FoodNerd_matched.p',euphebe_pickle_path +'Euphebe_matched.p'],os.path.join(os.getcwd(),'pickle/')+'euphebeNfoodnerd.p')