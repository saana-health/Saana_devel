#test
from mixpanel_api import Mixpanel
import csv
import pdb

def export_mixpanel_to_csv():
    TOKEN = '8cfc96a92162cdef9f20674d125c37f5'
    SECRET = '1261347a3eb35286683e32a2731e4f4d'

    mp = Mixpanel(SECRET, token = TOKEN)

    mp.export_people('test_event_export.csv',
                    {},
                    format='csv')

def process_mixpanel_csv():
    with open('test_event_export.csv') as csvfile:
        reader_list = list(csv.reader(csvfile))
        columns = [x.replace('$','') for x in reader_list[0]]

        matrix = [[0 for x in range(len(reader_list[0]))] for y in range(len(reader_list))]

        for i in range(len(reader_list)):
            for j in range(len(reader_list[i])):
                content = reader_list[i][j]
                if content and content[0] == '[':
                    if content[1] == 'u':
                        content = content.replace('$','').replace('[u','').replace('[','').replace(']','')
                matrix[i][j] = content

    with open ('mixpanelData.csv','wb',) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(matrix)

def match_names(list1, list2):
    '''

    :param list1:
    :param list2:
    :return: dictionary
    '''
    d = {}
    for a in list1:
        for b in list2:
            if 0.6 > difflib.SequenceMatcher(None,a.lower(),b.lower()).ratio() > 0.5:
                x = input('{} and {} identical? [Yes:1 / No: 0]: '.format(a,b))
                if x == 1:
                    try:
                        d[a].append(b)
                    except:
                        d[a] = b

    pickle.dump(d,open('50.p','wb'))





if __name__ == "__main__":
    from processEuphebe import processNutrition
    from proccessFoodMatrix import processFoodMatrixCSV
    import os
    import pdb
    import difflib
    import pickle
    PATH = os.path.join(os.getcwd(),'csv/Euphebe/')
    master_dict, column_matrix = processFoodMatrixCSV('')
    items, column_Euphebe = processNutrition(PATH+'nutrition.csv')
    match_names(column_matrix, column_Euphebe)
    pdb.set_trace()

