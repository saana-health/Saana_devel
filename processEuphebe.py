import csv
import pickle
import pprint
import pdb
from difflib import SequenceMatcher

def similar(a,b):
    return SequenceMatcher(None,a,b).ratio() > 0.76

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

def processMenu(filename):
    '''
    This function loads menu.csv file (which is 'Meals' sheet of Euphebe's nutrition excel file) \
    and returns a Python list of strings for the menus

    :param filename(str): csv filename to open
    :return menu_list [menu_name(str)]

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
    This function loads nutrition.csv ('nutrition sheet') and processes the info into a list of Meal() objects

    :param filename (str): to open:
    :return [Meal()]
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

        # loop through each row starting 3rd row
        for i in range(2,len(reader_list)):
            row = reader_list[i]
            name = row[0]

            #start of new item
            if is_name:
                is_name = False
                new_item = Meal(name=name, suppliderID='Euphebe')

            #ingredient
            elif name:
                #this row is for processing nutrition info
                if name == 'Total':
                    for j in range(1,len(row)):
                        nutritions[columns[j]] = row[j]
                #this row is for ingredient
                else:
                    ingredients.append(name.replace('  ',''))

            #empty line: update Meal()
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
    This function looks at return values of processMenu(='menu_list)' and processNutrition(='items') functions and maps which 'item' belongs to a menu \
    based on how an item name is similar to a menu name. Similarity value is tuned for 0.76 and almost correctly maps items to menus.

    One technique is used to map better: menus names are often concatenation of item names, with 'with', 'and'. '&' or 'w/' keywords. \
    Thus menu names are broken down into a list of phrases using .split(). As a result, occasionally item with such keywords are not mappend. \
    Redunancy is taken care of.
    #TODO: print mapped values and allow user input to test if they are correct and if anything is missing
    #TODO: print unmapped values and allow user input to manually map
    #TODO: permutation of 'and', '&'
    #TODO: if a menu should include more than what is already included
    :param menus: [menu_name(str)]
    :param items: [Meal()]
    :return: { str: [Meal()]}
    '''

    bucket = [x for x in items]
    mapped = {}
    cnt = 0
    cnt2 = 0

    #loop through items
    for item in items:
        found = False
        temp = []
        #loop through the menu list for a match/matches
        for menu_full in menus:
            #split up the menu name by concat keywords
            for menu in menu_full.replace(' and ',' with ').replace(' & ', ' with ').replace(' w/ ',' with ').split(' with '):
                # similar string
                if similar(item.name,menu):
                    temp.append(menu_full)
                    # an item mapped to multiple menus - this is possible
                    if found:
                        print('>> {} mapped with {}'.format(item.name,temp))
                        cnt2 += 1
                    try:
                        if item not in mapped[menu_full]:
                            mapped[menu_full].append(item)
                    except:
                        mapped[menu_full] = [item]
                    found = True
        # an item mapped to nothing - this is wrong.
        if not found:
            print('Following item not found: {}'.format(item.name))
            cnt +=1

    # print number of one to many mapped items and unmapped items
    print('{}/{} not found'.format(cnt,len(items)))
    print('{}/{} found twice'.format(cnt2,len(items)))
    return mapped

def combine_nutrition(mapped):
    '''
    This function looks at return val of mapToMeal() and combines .ingredients and .nutrition values of mapped items \
    into one Meal() object, and returns a list of Meal() objects

    :param mapped: {menu_name(str): [Meal()]}
    :return: [Meals()]
    '''
    new_list = []
    # loop through
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

    pickle.dump(new_list, open('EuphebeMealInfo.p','wb'))
    return new_list

if __name__ == "__main__":
    menus = processMenu('menu.csv')
    items = processNutrition('nutrition.csv')
    mapped = mapToMeal(menus, items)
    combined = combine_nutrition(mapped)



