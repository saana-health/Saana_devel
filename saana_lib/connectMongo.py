from pymongo import MongoClient
from urllib.parse import quote_plus
import conf


client = MongoClient('mongodb://{}:{}@{}:{}'.format(
    quote_plus(conf.DATABASE_USER),
    quote_plus(conf.DATABASE_PASSWORD),
    quote_plus(conf.DATABASE_ADDRESS),
    quote_plus(conf.DATABASE_PORT),
))

db = client.saana_db


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
    if meal_dictionaries:
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
        user_id = db.users.insert_one({'first_name':patient.name, 'role':'patient'}
        ).inserted_id
        patient_id = db.patients.insert_one({'user_id': user_id}).inserted_id
        subscription_id = db.mst_subscriptions.find_one({'interval_count': 2})['_id']
        patient_subscription_id = db.patient_subscription.insert_one({
            'patient_id':patient_id,
            'subscription_id':subscription_id,
            'status':'active'}
        )
        comos = []
        drugs = []
        symps = []
        for como in patient.comorbidities:
            doc = {'patient_id': patient_id, 'comorbidity_id': como}
            comos.append(doc)
        for drug in patient.treatment_drugs:
            doc = {'patient_id': patient_id, 'drug_id': drug}
            drugs.append(doc)
        for symp in patient.symptoms:
            doc= {'patient_id': patient_id, 'symptom_id': symp}
            symps.append(doc)
        db.patient_diseases.insert_one({'patient_id':patient_id, 'disease_id':patient.disease})
        if drugs != []:
            db.patient_drugs.insert_many(drugs)
        if comos!= []:
            db.patient_comorbidities.insert_many(comos)
        if symps!= []:
            db.patient_symptoms.insert_many(symps)

# GET

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

def get_subscription(patient_id):
    '''
    Gets subscription - 7 for 'interval_count == 2' and 15 for ' == 1'
    :param patient_id: ObjectId()
    :return: 7 or 15
    '''
    sub = list(db.patient_subscription.find({'patient_id':patient_id}))
    # Should be only one or no subscription
    assert len(sub) < 2

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
        obj = db.mst_food_ingredients.find_one({'name':ingredient})
        if obj is None:
            return_dict['food_ingredient_id'] = db.mst_food_ingredients.insert_one({'name':ingredient}).inserted_id
        else:
            return_dict['food_ingredient_id'] = obj['_id']
        return_dict['quantity'] = quantity
        ingredients_field.append(return_dict)
    return ingredients_field
