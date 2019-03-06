#test
from mixpanel_api import Mixpanel
import csv
import pdb
from model import Meal, Tag, Patient

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


def create_histogram(combined,keywords,filter = []):
    '''

    :param combined: [Meal]
    :return:
    '''
    import numpy as np
    import matplotlib.pyplot as plt
    from textwrap import wrap
    ret = False
    pair = {}
    unit = ''
    for meal in combined:
        for keyword in keywords:
            # for ingredient in meal.ingredients.keys():
            #     if keyword.lower() in ingredient.lower():
            #         for each in filter:
            #             if each in ingredient.lower():
            #                 ret = True
            #                 break
            #         if ret == True:
            #             ret = False
            #             continue
            #         print(keyword, ingredient)
            #         if meal.name in pair.keys():
            #             pair[meal.name] += float(meal.ingredients[ingredient])
            #         else:
            #             pair[meal.name] = float(meal.ingredients[ingredient])
            for nutrition in meal.nutrition.keys():
                # if keyword.lower() in nutrition.lower():
                if keyword in nutrition:
                # if keyword == nutrition:
                    print(keyword, nutrition)
                    if not unit:
                        unit = meal.nutrition[nutrition].split(' ')[1]
                    if meal.name in pair.keys():
                        pair[meal.name] += float(meal.nutrition[nutrition].split(' ')[0])
                    else:
                        pair[meal.name] = float(meal.nutrition[nutrition].split(' ')[0])

    x_label = ['\n'.join(wrap(l,35)) for l in pair.keys()]
    # x_label = pair.keys()
    y_label = pair.values()

    sorted_x_label = [x for _,x in sorted(zip(y_label,x_label))]
    ind = np.arange(len(x_label))

    fig, ax = plt.subplots()

    ax.barh(ind,sorted(y_label))
    ax.set_yticks(ind)
    ax.set_yticklabels(sorted_x_label)
    plt.title(str(keywords) + ' that is not ' + str(filter) + '(' + unit + ')')
    plt.tight_layout()
    figure = plt.gcf()
    figure.set_size_inches(16,12)

    plt.savefig('figures/'+str(keywords)+'_Not_'+str(filter),dpi=200)
    # plt.show()

def meal_dict_to_class(meal):
    return Meal(_id = meal['_id'],name = meal['name'], ingredients = meal['ingredients'], nutrition = meal['nutrition'], type = meal['type'], supplierID = meal['supplierID'], price = meal['price'])

def tag_dict_to_class(tag):
    return Tag(_id = tag['_id'],name = tag['name'], prior = tag['prior'], type = tag['type'], avoid = tag['avoid'],minimize = tag['minimize'])

def patient_dict_to_class(patient):
    return Patient(_id = patient['_id'],symptoms = patient['Symptoms'], comorbidities = patient['comorbidities'], disease = patient['disease'])

