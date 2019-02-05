import csv
import pprint
from difflib import SequenceMatcher
import pdb
import os
import pickle

PATH = os.path.join(os.getcwd(),'csv/')
def test(filename):
    items = []

    with open(filename) as csvfile:
        ingredients = []
        nutritions = {}
        reader_list = list(csv.reader(csvfile))
        is_name = True

        #first row
        euphebe = [x for x in list(reader_list[0])]

        for i in range(2,len(reader_list)):
            row = reader_list[i]
            name = row[0].replace('  ','')
            if name != '' and name not in euphebe:
                euphebe.append(name)


    tags= []
    master_dict = {}
    with open(PATH+'Food_Tags_Matrix.csv') as csvfile:
        reader_list = list(csv.reader(csvfile))
        for each in reader_list[1]:
            if each != '':
                tags.append(each)

    nutrition_map = {}
    for each in euphebe:
        for x in [' (mg)',' (g)',' (mcg)',' (IU)']:
            each = each.replace(x,'')
        for tag in tags:
            r = SequenceMatcher(None,each.lower(),tag.lower()).ratio()
            if r > 0.6:
                inp = input('Is "{}" identical to "{}"? [Yes: 1 / No: 0]: '.format(each,tag))
                if inp:
                    nutrition_map[tag] = each
    pickle.dump(nutrition_map, open('nutritionMap.p','wb'))


if __name__ == "__main__":
    test(PATH+'Euphebe/nutrition.csv')