from bson.objectid import ObjectId

class Meal:
    '''
    This class should follow the db schema designed for meal info
    '''
    def __init__(self,_id = '', name = '', ingredients = {}, nutrition = {}, type = '', supplierID = '',quantity = 0):
        self._id = _id
        self.name = name
        self.ingredients = ingredients
        self.nutrition = nutrition
        self.type = type
        self.supplierID = supplierID
        self.quantity = quantity

    def __str__(self):
        return str(self.name.encode('ascii','ignore'))

    def __eq__(self,other):
        return self.name == other.name

    def import_dict(self, dict):
        '''
        This function is for processing a dictionary response from MongoDB request into a Meal class
        :param dict:
        :return:
        '''
        self.name = dict['name']
        self.ingredients = dict['ingredients']
        self.nutrition = dict['nutrition']
        self.type = dict['type']
        self.supplierID = dict['supplierID']
        self.quantity= dict['quantity']
        self._id = dict['_id']
        return self


    __repr__ = __str__

class MealList(list):
    '''
    This class is for the sake of convenience in searching a class Meal in a list
    '''
    def find_by(self,feature_name,value):
        for meal in self:
            if getattr(meal,feature_name) == value:
                return meal

class Patient:
    def __init__(self, _id = '',name = '', comorbidities = [], disease = '', symptoms = [],weight = 0, treatment_drugs = [], disease_stage = '', feet = 0, surgery = '', next_order = '', plan = 7):
        self.name = name
        self.weight = weight
        self.treatment_drugs = treatment_drugs
        self.disease_stage = disease_stage
        self.comorbidities = comorbidities
        self.disease = disease
        self.symptoms = symptoms
        self._id = _id
        self.next_order = next_order
        self.plan = plan


class Tag:
    '''
    This class should follow the db schema designed for tag info
    '''
    def __init__(self, _id = '',name = '', minimize= {}, prior = [], type = '',avoid=[]):
        self._id = _id
        self.name = name
        self.avoid = avoid
        self.prior = prior
        self.type = type
        self.minimize = minimize

    def __str__(self):
        return str(self.name)

    def __eq__(self,other):
        return self.name == other.name

    __repr__ = __str__

class MealHistory:
    '''
    This class is for modeling 'Meal info' for writing to/ reading from Mongodb
    '''
    def __init__(self, patient_id, week_num):
        self.patient_id = patient_id
        self.week_num = week_num
        self.meal_list = {}

    def __str__(self):
        return '{} - {}wk'.format(self.patient_id, self.week_num)

    __repr__ = __str__


