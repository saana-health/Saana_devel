import csv
import pprint
from difflib import SequenceMatcher
import pdb
import os

PATH = os.path.join(os.getcwd(),'csv/')

def test():
    tags= []
    master_dict = {}
    with open(PATH+'Food_Tags_Matrix.csv') as csvfile:
        reader_list = list(csv.reader(csvfile))
        if not tags:
            for each in reader_list[1]:
                tags.append(each)

    with open(PATH+'/Euphebe/'+'nutrition.csv') as csvfile:
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
            if r > 0.7 and r < 0.9:
                print("< {} > and < {} > matched with ratio < {} >".format(each,each2,r))
    pdb.set_trace()

if __name__ == "__main__":
    test()
