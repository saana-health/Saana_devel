# from mixpanel_api import Mixpanel
import logging
import csv
from datetime import date, timedelta
from difflib import SequenceMatcher

from saana_lib import connectMongo
from saana_lib.model import Meal, Tag, Patient


logger = logging.getLogger(__name__)


def create_histogram(combined,keywords,filter = [],filename = ''):
    '''
    Creates a histogram
    :param combined: [Meal()]
    :param keywords: [str]
    :param filter: [str]
    :param filename: str
    :return: None
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

def tag_dict_to_class(dict):
    new_tag = Tag()
    new_tag.dict_to_class(dict)
    return new_tag


def patient_dict_to_class(patient):
    '''
    Convert dict to Patient()
    :param patient:
    :return: Patient()
    '''
    parse_date = [int(x) for x in patient['next_order'].split('-')]
    return Patient(name = patient['name'],_id = patient['_id'],symptoms = patient['symptoms'], comorbidities = patient['comorbidities'], disease = patient['Cancers'], next_order = date(parse_date[0],parse_date[1],parse_date[2]),plan = patient['plan'])

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
    '''
    Get the next coming tuesday (Today if today is tuesday)
    :param curr: datetime.datetime()
    :param wk: int
    :return: datetime.datetime()
    '''

    weekday = curr.weekday()
    while True:
        if weekday == 1:
            if wk == 1:
                break
            wk -= 1
        curr = curr + timedelta(days = 1)
        weekday = curr.weekday()
    return curr


def similar(s1, s2, _ratio):
    """
    A util function to check if two strings are 'similar',
    defined by the value below. This is used for mapping
    items to meals
    """
    return SequenceMatcher(None, s1, s2).ratio() > _ratio


def add_suppliers():
    '''
    Util func for adding suppliers
    :return: None
    '''
    for name in ['Euphebe','FoodNerd','Veestro','FrozenGarden','FoodFlo']:
        connectMongo.db.users.insert_one({'first_name':name, 'email': name+'@example.com', 'role':'supplier'})


def csv_writer(filename, rows):
    logger.info("Writing to csv file: {}".format(filename))
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    logger.info("Successfully wrote to a csv file")


if __name__ == "__main__":
    add_suppliers()
