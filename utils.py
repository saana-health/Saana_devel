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

def unicodetoascii(text):

    uni2ascii = {
            ord('\xe2\x80\x99'.decode('utf-8')): ord("'"),
            ord('\xe2\x80\x9c'.decode('utf-8')): ord('"'),
            ord('\xe2\x80\x9d'.decode('utf-8')): ord('"'),
            ord('\xe2\x80\x9e'.decode('utf-8')): ord('"'),
            ord('\xe2\x80\x9f'.decode('utf-8')): ord('"'),
            ord('\xc3\xa9'.decode('utf-8')): ord('e'),
            ord('\xe2\x80\x9c'.decode('utf-8')): ord('"'),
            ord('\xe2\x80\x93'.decode('utf-8')): ord('-'),
            ord('\xe2\x80\x92'.decode('utf-8')): ord('-'),
            ord('\xe2\x80\x94'.decode('utf-8')): ord('-'),
            ord('\xe2\x80\x94'.decode('utf-8')): ord('-'),
            ord('\xe2\x80\x98'.decode('utf-8')): ord("'"),
            ord('\xe2\x80\x9b'.decode('utf-8')): ord("'"),

            ord('\xe2\x80\x90'.decode('utf-8')): ord('-'),
            ord('\xe2\x80\x91'.decode('utf-8')): ord('-'),

            ord('\xe2\x80\xb2'.decode('utf-8')): ord("'"),
            ord('\xe2\x80\xb3'.decode('utf-8')): ord("'"),
            ord('\xe2\x80\xb4'.decode('utf-8')): ord("'"),
            ord('\xe2\x80\xb5'.decode('utf-8')): ord("'"),
            ord('\xe2\x80\xb6'.decode('utf-8')): ord("'"),
            ord('\xe2\x80\xb7'.decode('utf-8')): ord("'"),

            ord('\xe2\x81\xba'.decode('utf-8')): ord("+"),
            ord('\xe2\x81\xbb'.decode('utf-8')): ord("-"),
            ord('\xe2\x81\xbc'.decode('utf-8')): ord("="),
            ord('\xe2\x81\xbd'.decode('utf-8')): ord("("),
            ord('\xe2\x81\xbe'.decode('utf-8')): ord(")"),

                            }
    return text.decode('utf-8').translate(uni2ascii).encode('ascii')


def create_histogram(combined,keyword):
    '''

    :param combined: [Meal]
    :return:
    '''
    import numpy as np
    import matplotlib.pyplot as plt

    x_label = []
    y_label = []

    for meal in combined:
        print('-----------')
        for ingredient in meal.ingredients.keys():
            if keyword.lower() in ingredient.lower():
                print(ingredient)
                x_label.append(meal.name)
                y_label.append(float(meal.ingredients[ingredient]))

    sorted_x_label = [x for _,x in sorted(zip(y_label,x_label))]
    ind = np.arange(len(x_label))

    fig, ax = plt.subplots()

    ax.barh(ind,sorted(y_label))
    ax.set_yticks(ind)
    ax.set_yticklabels(sorted_x_label)

    plt.show()
