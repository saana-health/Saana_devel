from . import connectMongo
import pdb

# Parent object class for easily converting between dict and class
class MongoObject:
    def dict_to_class(self,dict):
        for attr in [attr for attr in dir(self) if not attr.startswith('__') and not callable(getattr(self,attr))]:
            if attr in dict.keys():
                setattr(self,attr,dict[attr])

    def class_to_dict(self):
        dic = {}
        for attr in [attr for attr in dir(self) if not attr.startswith('__') and not callable(getattr(self,attr))]:
            if attr == '_id':
                continue
            if attr == 'ingredients':
                dic[attr] = connectMongo.get_ingredient(self.ingredients)
                continue
            dic[attr] = getattr(self,attr)
        return dic

# inheriting classes from MongoObject

class Meal(MongoObject):
    '''
    This class should follow the db schema designed for meal info
    '''
    def __init__(self,_id = '', name = '', ingredients = {}, nutrition = {}, type = '', supplierID = '',quantity = 0, image = ''):
        '''

        :param _id: ObjectId()
        :param name: Str
        :param ingredients: {str: str}
        :param nutrition: {str: str}
        :param type: str
        :param supplierID: ObjectId()
        :param quantity: int
        :param image: str
        '''
        self._id = _id
        self.name = name
        self.ingredients = ingredients
        self.nutrition = nutrition
        self.type = type
        self.supplier_id = supplierID
        self.quantity = quantity
        self.image = image

    def __str__(self):
        if self.name != '':
            return str(self.name.encode('ascii','ignore'))
        else:
            return 'Meal Object (no name)'

    def __eq__(self,other):
        return self.name == other.name

    __repr__ = __str__

class Patient(MongoObject):
    def __init__(self, _id = '',name = '', comorbidities = [], disease = '', symptoms = [],weight = 0, treatment_drugs = [], disease_stage = '', feet = 0, surgery = '', plan = 7):
        '''

        :param _id:  ObjectId()
        :param name: str
        :param comorbidities: [ObjectId()]
        :param disease: ObjectId()
        :param symptoms: [ObjectId()]
        :param weight: int
        :param treatment_drugs: [ObjectId]
        :param disease_stage:
        :param feet:
        :param surgery:
        :param plan:
        '''
        self.name = name
        self.weight = weight
        self.treatment_drugs = treatment_drugs
        self.disease_stage = disease_stage
        self.comorbidities = comorbidities
        self.disease = disease
        self.symptoms = symptoms
        self._id = _id
        self.plan = plan

    def __str__(self):
        return str(self._id)

    __repr__ = __str__

class Tag(MongoObject):
    '''
    This class should follow the db schema designed for tag info
    '''
    def __init__(self, _id = '',name = '', minimize= {}, prior = [], type = '',avoid=[]):
        '''

        :param _id: ObjectId()
        :param name: str
        :param minimize: {ObjectId(): float}
        :param prior: {ObjectId(): float}
        :param type: str
        :param avoid: {ObjectId(): float}
        '''
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

class Order(MongoObject):
    def __init__(self,patient_id = '', patient_meal_id = [], herb_id=[], week_start_date= '', week_end_date= ''):
        '''

        :param patient_id: ObjectId()
        :param patient_meal_id: [ObjectId()]
        :param herb_id: [ObjectId()]
        :param week_start_date: datetime.datetime()
        :param week_end_date: datetime.datetime()
        '''
        self.patient_id = patient_id
        self.patient_meal_id = patient_meal_id
        self.herb_id = herb_id
        self.week_start_date = week_start_date
        self.week_end_date = week_end_date

    def __str__(self):
        return str(self.patient_id) + ' |  '+ str(self.week_start_date)

    __repr__ = __str__

class Patient_meal(MongoObject):
    def __init__(self, patient_id = '', meal_id = '', status= '', shippping_date= ''):
        self.patient_id = patient_id
        self.meal_id = meal_id
        self.status = status
        self.shipping_date = shippping_date

    def __str__(self):
        return str(self.patient_id) + ' | ' + str(self.meal_id)
