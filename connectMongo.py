from pymongo import MongoClient
import pdb
import os
import urllib.parse

# DB Keys
DATABASE_USER = os.environ.get("DATABASE_USER",'')
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD",'')

# cast to the correct object
username = urllib.parse.quote_plus(DATABASE_USER)
password = urllib.parse.quote_plus(DATABASE_PASSWORD)

# Connect to DB
client = MongoClient('mongodb://{}:{}@127.0.0.1'.format(username,password), authSource='saana_db')
db = client.saana_db

# ADD

def insert_meal(meals):
    '''
    Insert meals onto DB. A meal already exists, skip
    :param meals: [Meal()]
    :return: None
    '''
    meal_dictionaries = []
    for meal in meals:
        # Skip if a meal already exists in the DB
       if db.meal_infos.find({'name':meal.name}).count() > 0:
            continue
       meal_dictionaries.append(meal.class_to_dict())
    if meal_dictionaries != []:
        db.meal_infos.insert_many(meal_dictionaries)

def add_patients(patients):
    '''
    Util function for adding dummy patients
    > creates User with patient.name
    > creates Patient with user_id
    > creates Subscription with
    > adds patient_[como,symp,drug] to DB
    :param patients: [Patient()] or Patient()
    :return: None
    '''
    if not isinstance(patients,(list,)):
        patients = [patients]

    for patient in patients:
        user_id = db.users.insert_one({'first_name':patient.name, 'role':'patient'}).inserted_id
        patient_id = db.patients.insert_one({'user_id':user_id}).inserted_id
        subscription_id = db.mst_subscriptions.find_one({'interval_count':2})['_id']
        patient_subscription_id = db.patient_subscription.insert_one({'patient_id':patient_id, 'subscription_id':subscription_id,\
                                                                      'status':'active'})
        comos = []
        drugs = []
        symps = []
        for como in patient.comorbidities:
            doc = {'patient_id':patient_id, 'comorbidity_id':como}
            comos.append(doc)
        for drug in patient.treatment_drugs:
            doc = {'patient_id':patient_id, 'drug_id':drug}
            drugs.append(doc)
        for symp in patient.symptoms:
            doc= {'patient_id': patient_id, 'symptom_id':symp}
            symps.append(doc)
        db.patient_diseases.insert_one({'patient_id':patient_id, 'disease_id':patient.disease})
        if drugs != []:
            db.patient_drugs.insert_many(drugs)
        if comos!= []:
            db.patient_comorbidities.insert_many(comos)
        if symps!= []:
            db.patient_symptoms.insert_many(symps)

def add_tags(tag_dict):
    '''
    This function adds tag_dict into a db on MongoDB atlas
    :param tag_dict: return dictionary of processFoodMatrix.processFoodMatrixCSV
    :return: True/False based on successfulness
    '''
    tags = db.tags
    result = tags.insert_many(tag_dict.values())
    return True

# GET

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
    pdb.set_trace()
    return [list(x.values())[0] for x in li]

def get_drugs(patient_id):
    li = list(db.patient_drugs.find({'patient_id':patient_id},{'drug_id':1, '_id':0}))
    return [list(x.values())[0] for x in li]

def get_all_meals():
    return list(db.meal_infos.find())

def get_order(patient_id,week_start_date):
    '''

    :param patient_id: ObjectId()
    :param week_start_date: date.date()
    :return:
    '''
    # pdb.set_trace()
    return list(db.orders.find({'patient_id':patient_id, 'week_start_date':week_start_date},{'patient_meal_id':1, '_id':0}))

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

def get_all_patients():
    return db.patients.find()

def get_supplier(name):
    return db.users.find_one({'first_name':name})

def get_many(collection, attr, val):
    '''

    :param collection: str - name of the collection
    :param attr: str - name of an attribute
    :param val: ? - value
    :return: ObjectId()/None -  found/not found
    '''
    parser = getattr(db,collection)
    x = list(parser.find({attr:val}))
    return x

# Update

def update_next_order(patient_id, next_order):
    parser = db.patients.find()
    return db.patients.update({'_id':patient_id},{'$set':{'next_order':next_order}})

def get_all_tags():
    return db.tags.find()

# Delete

def drop(collection):
    parser = getattr(db,collection)
    return parser.drop()

if __name__ == "__main__":
    # test = get_any('mst_food_ingredients','name','shallots, fresh, chodpped')
    pdb.set_trace()
