import csv
import pprint
import pdb
from difflib import SequenceMatcher

def similar(a,b):
    return SequenceMatcher(None,a,b).ratio() > 0.75

class Meal:
    def __init__(self,name = '', ingredients = [], nutrition = {}, type = '', suppliderID = '',price = 0):
        self.name = name
        self.ingredients = ingredients
        self.nutrition = nutrition
        self.type = type
        self.supplierID = suppliderID
        self.price = price

def processMenu(filename):
    '''

    :param filename (str): csv filename to open
    :return:

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


            #empty line
            elif name:
                if name == 'Total':
                    for j in range(1,len(row)):
                        nutritions[columns[j]] = row[j]
                else:
                    ingredients.append(name.replace('  ',''))

            #ingredient
            else:
                is_name = True
                new_item.ingredients = ingredients
                new_item.nutrition = nutritions
                items.append(new_item)
                ingredients = []
                nutritions = {}
    return items

def mapToMeal(menus,items):
    bucket = [x for x in items]
    mapped = {}
    cnt = 0
    cnt2 = 0
    for item in items:
        found = False
        temp = []
        for menu_temp in menus:
            for menu in menu_temp.split(' with | and | & '):

                if similar(item.name,menu):
                    temp.append(menu)
                    if found:
                        print('>> {} mapped with {}'.format(item.name,temp))
                        cnt2 += 1
                    try:
                        mapped[menu].append(item)
                    except:
                        mapped[menu] = [item]
                    found = True
        if not found:
            print('Following item not found: {}'.format(item.name))
            cnt +=1
    print('{}/{} not found'.format(cnt,len(items)))
    print('{}/{} found twice'.format(cnt2,len(items)))
    pdb.set_trace()
    return mapped




if __name__ == "__main__":
    menus = processMenu('menu.csv')
    items = processNutrition('nutrition.csv')
    mapToMeal(menus, items)
