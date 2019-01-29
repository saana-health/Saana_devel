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