import csv
import pickle
import pprint
import pdb
import os
from model import Meal
from difflib import SequenceMatcher
import re
from connectMongdo import add_meals, drop

'''
Processing flow
processMenu()
-> processNutrition()
-> mapToMeal()
-> manual_input()
-> combine_nutrition()
'''

PATH = os.path.join(os.getcwd(),'csv/Euphebe/')

def similar(a,b,r):
    '''
    A util function to check if two strings are 'similar', defined by the value below. This is used for mapping items to meals
    :param a: (str) string 1 to compare
    :param b: (str) string 2 to compare
    :return: True if similar, False otherwise
    '''
    return SequenceMatcher(None,a,b).ratio() > r

def processMenu(filename):
    '''
    This function loads menu.csv file (which is 'Meals' sheet of Euphebe's nutrition excel file) \
    and returns a Python list of strings for the menus

    :param filename(str): csv filename to open
    :return menu_list [menu_name(str)]

    TODO: !! not stable for 'treatment drugs' (name field contains multiple names)
    '''
    menu_list = []
    with open(filename) as csvfile:
        reader_list = list(csv.reader(csvfile))
        for i in range(1,len(reader_list)):
            menu_list.append(reader_list[i][0].strip().lower())
    return menu_list

def processNutrition(filename):
    convert_dic = pickle.load(open('euphebe_change.p','rb'))
    '''
    This function loads nutrition.csv ('nutrition sheet') and processes the info (nutrition + ingredients) into a list of Meal() objects
    TODO: full_list should be generated by a separate function, not here
    :param filename (str): to open:
    :return [Meal()]
    '''
    print(' --- processNutrition() ----')
    columns = []
    items = []
    # lookup_dict = pickle.load(open(os.path.join(os.getcwd(),'pickle/euphebeNfoodnerd.p')))

    # First row is nutrition and ingredients are all on the first column
    with open(filename) as csvfile:
        ingredients = {}
        nutritions = {}
        total_ingredients = []
        reader_list = list(csv.reader(csvfile))
        # This variable is to see if the row is an ingredient or a name of a meal
        is_name = True

        #first row, which is nutrition
        columns = [x.strip().lower() for x in list(reader_list[0])]
        # matching units for nutritions with Regex (result: ['g','mg', ...])
        units = [re.search('\(.*\)',columns[y]).group()[1:-1] if re.search('\(.*\)',columns[y]) else '' for y in range(len(columns))]

        # Remove units so that they can be converted to floats
        for i in range(len(columns)):
            name = columns[i].replace(' ('+units[i]+')','')
            if name in convert_dic.keys():
                name = convert_dic[name]
            columns[i] = name

        # loop through each row starting 3rd row to process ingredients
        for i in range(2,len(reader_list)):
            row = reader_list[i]
            name = row[0].strip().lower()

            #start of new item (ingredient or meal name?)
            if is_name:
                is_name = False
                new_item = Meal(name=name, supplierID='Euphebe')

            elif name:
                # this row is for processing nutrition info
                if name == 'total':
                    for j in range(1,len(row)):
                        # skip if empty or not a number (zero is fine)
                        if row[j] not in ['','Serving','--']:
                            try:
                                nutritions[columns[j].strip().lower()] = str(float(row[j])) + ' ' + units[j]
                            except:
                                print('Warning: {} is not a number and is not previously recognized pattern'.format(row[j]))

                #this row is for ingredient
                else:
                    if name in convert_dic.keys():
                        name = convert_dic[name]
                    # ingredients[change_name(lookup_dict,name.replace('  ',''))] = row[3]
                    ingredients[name]= row[3].strip()
                    total_ingredients.append(name)

            #empty line: update Meal()
            else:
                is_name = True
                new_item.ingredients = ingredients
                new_item.nutrition = nutritions
                if 'insoluble fiber' not in nutritions.keys():
                    pdb.set_trace()
                items.append(new_item)
                ingredients = {}
                nutritions = {}

            # last line -> update current meal
            if i == len(reader_list)-1:
                new_item.ingredients = ingredients
                new_item.nutrition = nutritions
                items.append(new_item)

    return compress(items), nutritions.keys()+list(set(total_ingredients))

def compress(items):
    temp = []
    for each in items:
        if each not in temp:
            temp.append(each)
    return temp

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

    :param menus: [menu_name(str)] - this is from menu.csv ex) mushroom soup with oat crumble
    :param items: [Meal()] - this is from nutrition.csv ex) mushroom soup
    :return: { str: [Meal()]}
    '''

    print(' --- mapToMeal() ----')
    bucket = [x for x in items]
    mapped = {}
    not_found = []
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
                if similar(item.name,menu,0.9):
                    temp.append(menu_full)
                    # an item mapped to multiple menus - this is possible
                    if found:
                        # print('>> While processing menu {}, {} mapped with {}'.format(menu_full, item.name,temp))
                        cnt2 += 1
                    try:
                        if item not in mapped[menu_full]:
                            mapped[menu_full].append(item)
                    except:
                        mapped[menu_full] = [item]
                    found = True
        # an item mapped to nothing - this is wrong.
        if not found:
            # print('Following ITEM not found: {}'.format(item.name))
            not_found.append(item)
            cnt +=1

    # print number of one to many mapped items and unmapped items
    # print('{}/{} not found'.format(cnt,len(items)))
    # print('{}/{} found twice'.format(cnt2,len(items)))
    for item_li in mapped.values():
        for item in item_li:
            if 'insoluble fiber' not in item.nutrition.keys():
                print(item)
    return mapped, not_found

def manual_input(menus, not_found, mapped, filename = ''):
    '''
    string sequence matching criteria for ratio() > 0.5 still works for ALL current Euphebe meal list. So this simply maps not_found meals to menus by 0.5 limit
    :param menus: [str] - menus
    :param not_found: [Meal()] - not actual menu meal but meal component
    :param mapped: [Meal()] - already mapped meals
    :return: [Meal()] - newly mapped meals including previously mapped and newly mapped
    '''
    manual_map = {}
    left_over = not_found[:]
    if filename:
        manual_map = pickle.load(open(filename,'rb'))
    else:
        for each in not_found:
            for menu in menus:
                if SequenceMatcher(None,menu,each.name).ratio() > 0.5:
                    # if menu in manual_map and each in manual_map[menu]:
                    #     continue
                    # Below for matching for the first time
                    print('----------------------')
                    x = input('Is "{}" part of "{}"? [Yes: 1 / No: 0]: '.format(each, menu))
                    if x:
                        try:
                            manual_map[menu].append(each)
                        except:
                            manual_map[menu] = [each]
                    else:
                        continue
                else:
                    for parsed in menu.replace(' and ',' with ').replace(' & ', ' with ').replace(' w/ ',' with ').split(' with '):
                        if similar(each.name, parsed, 0.76):
                            print('----------------------')
                            x = input('Is "{}" part of "{}"? [Yes: 1 / No: 0]: '.format(each, menu))
                            if x:
                                try:
                                    manual_map[menu].append(each)
                                except:
                                    manual_map[menu] = [each]
                            else:
                                continue
        pickle.dump(manual_map,open('euphebe_manualMap.p','wb'))

    for each in manual_map.keys():
        if each not in menus:
            continue
        try:
            mapped[each] += manual_map[each]
        except:
            mapped[each] = manual_map[each]
        if each in [x.name for x in left_over]:
            [left_over.remove(item) for item in manual_map[each]]
        # print('{} now part of {}'.format(manual_map, each))
    if left_over:
        print("{} still not found".format(left_over))
    return mapped

def combine_nutrition(mapped):
    '''
    This function looks at return val of mapToMeal() and combines .ingredients and .nutrition values of mapped items \
    into one Meal() object, and returns a list of Meal() objects

    :param mapped: {menu_name(str): [Meal()]}
    :return: [Meals()]
    '''
    #
    for item_li in mapped.values():
        for item in item_li:
            if 'insoluble fiber' not in item.nutrition.keys():
                print(item)

    #

    print(' --- combine_nutrition ---')
    new_list = []
    # loop through
    for menu_name in mapped.keys():
        new_meal = Meal(name = menu_name, supplierID = 'Euphebe')
        new_nutrition = {}
        new_ingredients = {}
        for item in mapped[menu_name]:
            for ingredient in item.ingredients.keys():
                if ingredient not in new_ingredients.keys():
                    new_ingredients[ingredient] = float(item.ingredients[ingredient])
                else:
                    new_ingredients[ingredient] += float(item.ingredients[ingredient])

            for nutrition in item.nutrition.keys():
                val = item.nutrition[nutrition]
                # Add value if already exist
                if nutrition in new_nutrition.keys():
                    new_nutrition[nutrition] = str(float(new_nutrition[nutrition].split(' ')[0]) + float(val.split(' ')[0])) + ' ' +val.split(' ')[1]
                else:
                    new_nutrition[nutrition] = val
                ######## ERROR ###########
                # try:
                #     # pdb.set_trace()
                #     new_nutrition[nutrition] += str(float(new_nutrition[nutrition].split[0]) + float(item.split(' ')[0])) + item.split(' ')[1]
                # # Create a new key/value if doesnt exist
                # except:
                #     new_nutrition[nutrition] = item.nutrition[nutrition]
            for each in new_nutrition:
                if 'insoluble fiber' not in new_nutrition.keys():
                    # pdb.set_trace()
                    if 'insoluble fiber' not in item.nutrition.keys():
                        pdb.set_trace()
        new_meal.nutrition = new_nutrition
        new_meal.ingredients = new_ingredients
        new_list.append(new_meal)
    ## saves into .p file
    #pickle.dump(new_list, open('EuphebeMealInfo.p','wb'))

    return new_list

def process():
    from matchNames import change_name
    menus = processMenu(PATH+'menu315.csv')
    items, columns = processNutrition(PATH+'test2.csv')
    mapped, not_found = mapToMeal(menus, items)
    newly_mapped = manual_input(menus,not_found,mapped,'euphebe_manualMap.p')
    # newly_mapped = manual_input(menus,not_found,mapped)
    combined = combine_nutrition(newly_mapped)
    return combined
    # pdb.set_trace()

    # from utils import create_histogram_insoluble
    # create_histogram_insoluble(combined)

    # add_meals(combined)


if __name__ == "__main__":
    combined = process()
    # from matchNames import change_name
    # menus = processMenu(PATH+'menu0313.csv')
    # items, columns = processNutrition(PATH+'test2.csv')
    # mapped, not_found = mapToMeal(menus, items)
    # newly_mapped = manual_input(menus,not_found,mapped,'euphebe_manualMap.csv')
    # # newly_mapped = manual_input(menus,not_found,mapped)
    # pprint.pprint(newly_mapped)
    # combined = combine_nutrition(newly_mapped)
    # # pdb.set_trace()
    #
    # from utils import create_histogram_insoluble, create_histogram
    # # create_histogram_insoluble(combined)
    # create_histogram(combined,['totfib'])
    #
    drop('meals')
    add_meals(combined)
