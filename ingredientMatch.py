import csv
import pprint
from difflib import SequenceMatcher
import pdb

def test():
    '''
    This function opens the CSV file and processes the tag matrix so that return python dictionary that will be fed into MongoDB
    MongoDB schema: {name: 'cancer1', type: 'cancer', avoid: ['a',b'], prior: ['c','d']}

    :param filename (str): csv filename to open
    :return: master_dict (dictionary): { <str:name>: {'name': (str), 'type': (str), 'avoid': (list[str]), 'prior': (list[str]) } }

    !! not stable for 'treatment drugs' (name field contains multiple names)
    '''
    tags= []
    master_dict = {}
    with open('Food Tags Matrix.csv') as csvfile:
        reader_list = list(csv.reader(csvfile))
        if not tags:
            for each in reader_list[1]:
                tags.append(each)

    what_type = ''
    nutritions = []
    items = []
    ingredients = []
    with open('nutrition.csv') as csvfile:
        ingredients = []
        nutritions = {}
        reader_list = list(csv.reader(csvfile))
        is_name = True

        #first row
        nutritions = [x for x in list(reader_list[0])]
        for row in reader_list:
            x = row[0].replace('  ','')
            if x not in nutritions:
                nutritions.append(x)

    for each in nutritions:
        for each2 in tags:
            r = SequenceMatcher(None,each.lower(),each2.lower()).ratio()
            if r > 0.65 and r < 0.9:
                print("< {} > and < {} > matched with ratio < {} >".format(each,each2,r))
    pdb.set_trace()

if __name__ == "__main__":
    test()
