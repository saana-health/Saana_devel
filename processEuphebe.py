import csv
import pprint
import pdb
from difflib import SequenceMatcher

def similar(a,b):
    return SequenceMatcher(None,a,b).ratio() > 0.76

class Meal:
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

def processMenu(filename):
    '''

    :param filename (str): csv filename to open
    :return: [str]

    !! not stable for 'treatment drugs' (name field contains multiple names)
    '''
    menu_list = []
    with open(filename) as csvfile:
        reader_list = list(csv.reader(csvfile))

        for i in range(1,len(reader_list)):
            menu_list.append(reader_list[i][0])
    return menu_list

def processNutrition(filename):
    '''

    :param filename:
    :return: [Meal()]
    '''
    columns = []
    items = []

    with open(filename) as csvfile:
        ingredients = []
        nutritions = {}
        reader_list = list(csv.reader(csvfile))
        is_name = True

        #first row
        columns = [x for x in list(reader_list[0])]

        for i in range(2,len(reader_list)):
            row = reader_list[i]
            name = row[0]

            #start of new item
            if is_name:
                is_name = False
                new_item = Meal(name=name)

            #ingredient
            elif name:
                if name == 'Total':
                    for j in range(1,len(row)):
                        nutritions[columns[j]] = row[j]
                else:
                    ingredients.append(name.replace('  ',''))

            #empty line
            else:
                is_name = True
                new_item.ingredients = ingredients
                new_item.nutrition = nutritions
                items.append(new_item)
                ingredients = []
                nutritions = {}
    return items

def mapToMeal(menus,items):
    '''

    :param menus: [str]
    :param items: [Meal()]
    :return: { str: [Meal()]}
    '''
    #TODO: permutation of 'and', '&'
    #TODO: if a menu should include more than what is already included
    bucket = [x for x in items]
    mapped = {}
    cnt = 0
    cnt2 = 0
    for item in items:
        found = False
        temp = []
        for menu_full in menus:
            for menu in menu_full.replace(' and ',' with ').replace(' & ', ' with ').replace(' w/ ',' with ').split(' with '):
                #print(menu)
                if similar(item.name,menu):
                    temp.append(menu_full)
                    if found:
                        print('>> {} mapped with {}'.format(item.name,temp))
                        cnt2 += 1
                    try:
                        if item not in mapped[menu_full]:
                            mapped[menu_full].append(item)
                    except:
                        mapped[menu_full] = [item]
                    found = True
        if not found:
            print('Following item not found: {}'.format(item.name))
            cnt +=1
    print('{}/{} not found'.format(cnt,len(items)))
    print('{}/{} found twice'.format(cnt2,len(items)))
    return mapped

def combine_nutrition(mapped):
    '''

    :param mapped: {menu_name(str): [Meal()]}
    :return: [Meals()]
    '''
    #TODO: figure out return and input val
    new_list = []
    for menu_name in mapped.keys():
        new_meal = Meal(name = menu_name)
        new_nutrition = {}
        new_ingredients = []
        for item in mapped[menu_name]:
            for ingredient in item.ingredients:
                if ingredient not in new_ingredients:
                    new_ingredients.append(ingredient)
            for nutrition in item.nutrition.keys():
                try:
                    new_nutrition[nutrition] += float(item.nutrition[nutrition])
                except:
                    try:
                        new_nutrition[nutrition] = float(item.nutrition[nutrition])
                    except:
                        pass
        new_meal.nutrition = new_nutrition
        new_meal.ingredients = new_ingredients
        new_list.append(new_meal)
    return new_list

if __name__ == "__main__":
    menus = processMenu('menu.csv')
    items = processNutrition('nutrition.csv')
    mapped = mapToMeal(menus, items)
    combined = combine_nutrition(mapped)
    pdb.set_trace()



