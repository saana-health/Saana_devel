from pymongo import MongoClient
import pickle
import pdb
import pprint
from model import Meal, MealHistory,MealList

client = MongoClient()
db = client.saana_db
################ NEW ################a

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

# def add_user()

# def add_order(slots,id,start_date,end_date):
#     '''
#
#     :param order: [Meal()] - slots
#     :param id:
#     :return:
#     '''
#     meal_id = []
#     for meal in slots:
#         meal_id.append(meal._id)


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
    li = list(db.patient_drug.find({'patient_id':patient_id},{'drug_id':1, '_id':0}))
    return [list(x.values())[0] for x in li]

def get_all_meals():
    return list(db.meal_infos.find())
    # cursor = db.meal_infos.find()
    # meals = MealList()
    # for meal in cursor:
    #     # meals.append(Meal().import_dict(meal))
    #     meals.append(meal)
    #
    # return meals

def add_order(order,id):
    db.orders.insert_one(order.to_dic())
    # existing_history = db.mealInfo.find_one({'patient_id': id})
    # if existing_history is None:
    #     meal_history_dict = {}
    #     meal_history_dict['patient_id'] = meal_history.patient_id
    #     meal_history_dict['week_' + str(meal_history.week_num)] = {'meal_list': meal_history.meal_list}
    #     db.mealInfo.insert_one(meal_history_dict)
    # else:
    #     db.mealInfo.update({'patient_id':id},{'$set': {'week_'+str(meal_history.week_num): {'meal_list':meal_history.meal_list}}})
    # return True
################## OLD ##################33

def add_patients(patients):
    if not isinstance(patients,(list,)):
        patients = [patients]
    collection_patients = db.patients
    pa = [{'name':x.name, 'treatment_drugs': x.treatment_drugs, 'Cancers':x.disease, 'symptoms':x.symptoms, 'comorbidities':x.comorbidities, 'next_order': str(x.next_order), 'plan': x.plan} for x in patients]
    result = collection_patients.insert_many(pa)

def add_tags(tag_dict):
    '''
    This function adds tag_dict into a db on MongoDB atlas
    :param tag_dict: return dictionary of processFoodMatrix.processFoodMatrixCSV
    :return: True/False based on successfulness
    '''
    tags = db.tags
    result = tags.insert_many(tag_dict.values())
    return True

def add_meals(meal_list = [],pickle_name = ''):
    '''

    :param pickle_name: (str)name of the pickle
    :return: True
    '''
    if not meal_list:
        meal_list = pickle.load( open(pickle_name,'rb'))
    meals = db.meals

    l = []
    for each in meal_list:
        new_dict = {}
        new_dict['name'] = each.name
        new_dict['nutrition'] = each.nutrition
        new_dict['ingredients'] = each.ingredients
        new_dict['supplierID'] = each.supplierID
        new_dict['quantity'] = each.quantity
        new_dict['type'] = each.type
        l.append(new_dict)
    meals.insert_many(l)
    return True



def get_mealinfo_by_patient(id):
    mealinfo = db.mealInfo.find_one({'patient_id': id})
    return mealinfo

def get_all_tags():
    return db.tags.find()

def get_all_patients():
    return db.patients.find()

def drop(collection):
    parser = getattr(db,collection)
    return parser.drop()

def update_quantity():
    import random
    parser = db.meals.find()
    for each in parser:
        db.meals.update({'_id': each['_id']},{'$set':{'quantity':random.randint(0,10)}})

def update_next_order(patient_id, next_order):
    parser = db.patients.find()
    return db.patients.update({'_id':patient_id},{'$set':{'next_order':str(next_order)}})

if __name__ == "__main__":
    # test = get_any('mst_food_ingredients','name','shallots, fresh, chodpped')
    test = add_ingredient('abc')
    pdb.set_trace()