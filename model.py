class Meal:
    '''
    This class should follow the db schema designed for meal info
    '''
    def __init__(self,name = '', ingredients = [], nutrition = {}, type = '', supplierID = '',price = 0):
        self.name = name
        self.ingredients = ingredients
        self.nutrition = nutrition
        self.type = type
        self.supplierID = supplierID
        self.price = price

    def __str__(self):
        return str(self.name.encode('ascii','ignore'))

    def __eq__(self,other):
        return self.name == other.name

    __repr__ = __str__

class Patient:
    def __init__(self, name = '', weight = 0, treatment_drugs = [], disease_stage = '', feet = 0, surgery = ''):
        pass

class Tag:
    '''
    This class should follow the db schema designed for tag info
    '''
    def __init__(self, name = '', avoid = [], prior = [], type = ''):
        self.name = name
        self.avoid = avoid
        self.prior = prior
        self.type = type

    def __str__(self):
        return str(self.name)

    def __eq__(self,other):
        return self.name == other.name

    __repr__ = __str__

class MealHistory:
    def __init__(self, patient_id, week_num):
        self.patient_id = patient_id
        self.week_num = week_num
        self.meal_list = []

    def __str__(self):
        return '{} - {}wk'.format(self.patient_id, self.week_num)

    __repr__ = __str__


