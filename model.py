class Meal:
    '''
    This class should follow the db schema designed for meal info
    '''
    def __init__(self,name = '', ingredients = [], nutrition = {}, type = '', suppliderID = '',price = 0):
        self.name = name
        self.ingredients = ingredients
        self.nutrition = nutrition
        self.type = type
        self.supplierID = suppliderID
        self.price = price

    def __str__(self):
        return str(self.name)

    def __eq__(self,other):
        return self.name == other.name

    __repr__ = __str__

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
