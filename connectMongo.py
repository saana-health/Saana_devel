from pymongo import MongoClient
import pickle
import pdb
import pprint
import os
import urllib.parse
from model import Meal, MealHistory,MealList

DATABASE_USER = os.environ.get("DATABASE_USER",'')
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD",'')

username = urllib.parse.quote_plus(DATABASE_USER)
password = urllib.parse.quote_plus(DATABASE_PASSWORD)

client = MongoClient('mongodb://{}:{}@127.0.0.1'.format(username,password), authSource='saana_db')
db = client.saana_db

def insert_meal(meals):
    '''
    insert meals onto DB
    :param meals: Meal() object
    :return: True/False on success/fail
    '''
    meal_dictionaries = []
    for meal in meals:
        if db.meal_infos.find({'name':meal.name}).count() > 0:
            continue
        meal_dic = {}
        meal_dic['name'] =  meal.name
        meal_dic['nutrition'] = meal.nutrition
        meal_dic['type'] = meal.type
        meal_dic['quantity'] = meal.quantity
        meal_dic['ingredients'] = get_ingredient(meal.ingredients)
        meal_dic['supplier_id'] = meal.supplierID
        meal_dic['image'] = meal.image
        meal_dictionaries.append(meal_dic)
    if meal_dictionaries != []:
        db.meal_infos.insert_many(meal_dictionaries)

def get_ingredient(ingredients):
    '''
    get ingredient id and quantity by its name
    :param ingredients: [str]
    :return: [{_id, quantity}]
    '''
    ingredients_field = []
    for ingredient in ingredients.keys():
        return_dict = {}
        quantity = ingredients[ingredient]
        obj = get_any('mst_food_ingredients','name',ingredient)
        if obj is None:
            return_dict['food_ingredient_id'] = add_ingredient(ingredient)
        else:
            return_dict['food_ingredient_id'] = obj['_id']
        return_dict['quantity'] = quantity
        ingredients_field.append(return_dict)
    return ingredients_field

def add_ingredient(ingredient):
    '''
    add a new ingredient into db and return id
    :param ingredient: str
    :return: Objectid()
    '''
    id = db.mst_food_ingredients.insert_one({'name':ingredient}).inserted_id
    return id

def get_any(collection, attr, val):
    '''

    :param collection: str - name of the collection
    :param attr: str - name of an attribute
    :param val: ? - value
    :return: ObjectId()/None -  found/not found
    '''
    parser = getattr(db,collection)
    if isinstance(val,(list,)):
        return list(parser.find({attr:{"$in":val}}))
    x = list(parser.find({attr:val}))
    if len(x) > 0:
        return x[0]
    else:
        return None

def get_comorbidities(patient_id):
    li = list(db.patient_comorbidities.find({'patient_id':patient_id},{'comorbidity_id':1, '_id':0}))
    return [list(x.values())[0] for x in li]

def get_disease(patient_id):
    li = list(db.patient_diseases.find({'patient_id':patient_id},{'disease_id':1, '_id':0}))
    return [list(x.values())[0] for x in li]

def get_symptoms(patient_id):
    li = list(db.patient_symptoms.find({'patient_id':patient_id},{'symptom_id':1, '_id':0}))
    return [list(x.values())[0] for x in li]

def get_drugs(patient_id):
    li = list(db.patient_drugs.find({'patient_id':patient_id},{'drug_id':1, '_id':0}))
    return [list(x.values())[0] for x in li]

def get_all_meals():
    return list(db.meal_infos.find())

def add_order(order,id):
    db.orders.insert_one(order.to_dic())

def get_order(patient_id,week_start_date):
    '''

    :param patient_id: ObjectId()
    :param week_start_date: date.date()
    :return:
    '''
    # pdb.set_trace()
    return list(db.orders.find({'patient_id':patient_id, 'week_start_date':week_start_date},{'patient_meal_id':1, '_id':0}))

def add_patients(patients):
    if not isinstance(patients,(list,)):
        patients = [patients]

    for patient in patients:
        user_id = db.users.insert_one({'name':patient.name, 'role':'patient'}).inserted_id
        patient_id = db.patients.insert_one({'user_id':user_id}).inserted_id
        subscription_id = db.mst_subscriptions.find_one({'interval_count':2})['_id']
        patient_subscription_id = db.patient_subscription.insert_one({'patient_id':patient_id, 'subscription_id':subscription_id,\
                                                                      'status':'active'})


        comos = []
        drugs = []
        symps = []
        for como in patient.comorbidities:
            row = {'patient_id':patient_id, 'comorbidity_id':como}
            comos.append(row)
        for drug in patient.treatment_drugs:
            row = {'patient_id':patient_id, 'drug_id':drug}
            drugs.append(row)
        for symp in patient.symptoms:
            row= {'patient_id': patient_id, 'symptom_id':symp}
            symps.append(row)
        db.patient_diseases.insert_one({'patient_id':patient_id, 'disease_id':patient.disease})
        if drugs != []:
            db.patient_drugs.insert_many(drugs)
        if comos!= []:
            db.patient_comorbidities.insert_many(comos)
        if symps!= []:
            db.patient_symptoms.insert_many(symps)

def get_subscription(patient_id):
    sub = list(db.patient_subscription.find({'patient_id':patient_id}))
    if sub == []:
        return False
    subscription_id = sub[0]['subscription_id']
    interval = list(db.mst_subscriptions.find({'_id':subscription_id}))[0]['interval_count']
    if interval == 2:
        return 7
    elif interval == 1:
        return 15
    print('wrong subscription')
    assert False

def get_next_order(patient_id):
    patient = db.patients.find({'_id':patient_id})[0]
    if 'next_order' not in patient.keys():
        return None
    return patient['next_order']

def update_next_order(patient_id, next_order):
    parser = db.patients.find()
    return db.patients.update({'_id':patient_id},{'$set':{'next_order':next_order}})

def get_all_patients():
    return db.patients.find()

def add_supplier(name):
    return db.users.insert_one({'first_name':name, 'role':'supplier'})

def get_supplier(name):
    return db.users.find_one({'first_name':name})

################## OLD ##################33

def add_tags(tag_dict):
    '''
    This function adds tag_dict into a db on MongoDB atlas
    :param tag_dict: return dictionary of processFoodMatrix.processFoodMatrixCSV
    :return: True/False based on successfulness
    '''
    tags = db.tags
    result = tags.insert_many(tag_dict.values())
    return True

def get_mealinfo_by_patient(id):
    mealinfo = db.mealInfo.find_one({'patient_id': id})
    return mealinfo

def get_all_tags():
    return db.tags.find()

def drop(collection):
    parser = getattr(db,collection)
    return parser.drop()

def update_quantity():
    import random
    parser = db.meals.find()
    for each in parser:
        db.meals.update({'_id': each['_id']},{'$set':{'quantity':random.randint(0,10)}})



if __name__ == "__main__":
    # test = get_any('mst_food_ingredients','name','shallots, fresh, chodpped')
    test = add_ingredient('abc')
    pdb.set_trace()
