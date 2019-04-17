#test
# from mixpanel_api import Mixpanel
import csv
import pdb
from model import Meal, Tag, Patient
from datetime import date, timedelta
from difflib import SequenceMatcher

def unicodetoascii(text):
    print(text)
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
            ord('\xc2\xac\xc2\xb5'.decode('utf-8')): ord("n")

                            }
    return text.decode('utf-8').translate(uni2ascii).encode('ascii')

def create_histogram(combined,keywords,filter = [],filename = ''):
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
    cnt = 0
    for meal in combined:
        for keyword in keywords:
            for ingredient in meal.ingredients.keys():
                # if keyword.lower() == ingredient.lower():
                if keyword.lower() in ingredient.lower():

                    cnt += 1
                    for each in filter:
                        if each in ingredient.lower():
                            ret = True
                            break
                    if ret == True:
                        ret = False
                        continue
                    print(keyword, ingredient)
                    if meal.name in pair.keys():
                        pair[meal.name] += float(meal.ingredients[ingredient])
                    else:
                        pair[meal.name] = float(meal.ingredients[ingredient])
            for nutrition in meal.nutrition.keys():
                # if keyword.lower() in nutrition.lower():
                # if keyword in nutrition:
                if keyword == nutrition:
                    print(keyword, nutrition)
                    cnt +=1
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
    for i,v in enumerate(sorted(y_label)):
        ax.text(v,i, str(v),color='blue',fontweight='bold')
    if not filename:
        plt.title(str(keywords) + ' that is not ' + str(filter) + '(' + unit + ')')
    else:
        plt.title(filename + '(' + unit+ ')')

    plt.tight_layout()
    figure = plt.gcf()
    figure.set_size_inches(16,12)

    if filename:
        plt.savefig('figures/'+filename + '(' + unit + ')', dpi=200)
    else:
        plt.savefig('figures/'+str(keywords), dpi=200)

    print(' TOTAL {} FOUND '.format(cnt))
    # plt.show()

def meal_dict_to_class(meal):
    return Meal(_id = meal['_id'],name = meal['name'], ingredients = meal['ingredients'], nutrition = meal['nutrition'], type = meal['type'], supplierID = meal['supplier_id'], quantity = meal['quantity'])

def tag_dict_to_class(tag):
    return Tag(_id = tag['_id'],name = tag['name'], prior = tag['prior'], type = tag['type'], avoid = tag['avoid'],minimize = tag['minimize'])

def patient_dict_to_class(patient):
    parse_date = [int(x) for x in patient['next_order'].split('-')]
    return Patient(name = patient['name'],_id = patient['_id'],symptoms = patient['symptoms'], comorbidities = patient['comorbidities'], disease = patient['Cancers'], next_order = date(parse_date[0],parse_date[1],parse_date[2]),plan = patient['plan'])

def auto_add_meal():
    import os
    import processFoodNerd
    import processEuphebe
    from connectMongdo import drop, add_meals
    FOOD_NERD_PATH = os.path.join(os.getcwd(),'csv/FoodNerd/')
    PATH = os.path.join(os.getcwd(),'csv/Euphebe/')
    drop('meals')
    add_meals(processEuphebe.process(PATH))
    add_meals(processFoodNerd.processNutrition(FOOD_NERD_PATH + 'nutrition.csv')[0])

'''
def add_dummy_patients():
    disease = get_any('tags','name','brain')['_id']
    symptoms = get_any('tags','name',['constipation','difficulty to swallow','dry mouth','nausea'])
    comorbidities = get_any('tags','name',['hypertension'])
    treatment_drugs =[]
    # treatment_drugs = get_any('tags','name', ['docetaxel (taxotere)','carboplatin (paraplatin)','trastuzumab (herceptin)','pertuzumab (perjeta)',\
    #                                           'olanzapine (zyprexa)','prochlorperazine (compazine)','ondanstetron (zofran)','ioperamide (imodium)'])
    ONEWEEK = find_tuesday(date.today(),1)
    TWOWEEK = find_tuesday(date.today(),2)

    dummy = Patient(name = 'Stephanie', comorbidities= [x['_id'] for x in comorbidities], treatment_drugs = [x['_id'] for x in treatment_drugs], disease = disease, symptoms = [x['_id'] for x in symptoms], next_order=ONEWEEK, plan = 7)
    add_patients(dummy)

    disease = get_any('tags','name','skin')['_id']
    symptoms = get_any('tags','name',['fatigue','inflammation'])
    comorbidities = get_any('tags','name',[''])
    dummy = Patient(name = 'Sunny', comorbidities= [x['_id'] for x in comorbidities], treatment_drugs = [x['_id'] for x in treatment_drugs], disease = disease, symptoms = [x['_id'] for x in symptoms], next_order = TWOWEEK, plan = 7)
    add_patients(dummy)

    disease = get_any('tags','name','pancreas')['_id']
    symptoms = get_any('tags','name',['cough','diarrhea','difficulty chewing','dry mouth','loss of or change of taste','weight loss'])
    comorbidities = get_any('tags','name',['diabetes'])
    dummy = Patient(name = 'Min Joon', comorbidities= [x['_id'] for x in comorbidities], treatment_drugs = [x['_id'] for x in treatment_drugs], disease = disease, symptoms = [x['_id'] for x in symptoms], next_order = ONEWEEK, plan = 14)
    add_patients(dummy)

    disease = get_any('tags','name','leukemia')['_id']
    symptoms = get_any('tags','name',['constipation','loss of appetite','dry mouth'])
    comorbidities = get_any('tags','name',['hypertension'])
    dummy = Patient(name = 'Jacki', comorbidities= [x['_id'] for x in comorbidities], treatment_drugs = [x['_id'] for x in treatment_drugs], disease = disease, symptoms = [x['_id'] for x in symptoms], next_order = TWOWEEK, plan = 14)
    add_patients(dummy)
'''
def find_tuesday(curr, wk = 1):
    weekday = curr.weekday()
    while True:
        if weekday == 1:
            if wk == 1:
                break
            wk -= 1
        curr = curr + timedelta(days = 1)
        weekday = curr.weekday()
    return curr

def similar(a,b,r):
    '''
    A util function to check if two strings are 'similar', defined by the value below. This is used for mapping items to meals
    :param a: (str) string 1 to compare
    :param b: (str) string 2 to compare
    :return: True if similar, False otherwise
    '''
    return SequenceMatcher(None,a,b).ratio() > r

def add_suppliers():
    import connectMongo
    for name in ['Euphebe','FoodNerd','Veestro','FrozenGarden','FoodFlo']:
        connectMongo.db.users.insert_one({'first_name':name, 'email': name+'@example.com', 'role':'supplier'})

if __name__ == "__main__":
    # auto_add_meal()
    # from maggie import add_maggie
    # add_maggie()
    # add_dummy_patients()
    add_suppliers()
