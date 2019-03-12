import csv
import pprint
import os
import pdb
from connectMongdo import add_tags
from model import Tag
PATH = os.path.join(os.getcwd(),'csv/')


def processFoodMatrixCSV(filename):
    '''
    This function opens the CSV file and processes the tag matrix so that return python dictionary that will be fed into MongoDB
    MongoDB schema: {name: 'cancer1', type: 'cancer', avoid: ['a',b'], prior: ['c','d']}

    :param filename (str): csv filename to open
    :return: master_dict (dictionary): { <str:name>: {'name': (str), 'type': (str), 'avoid': (list[str]), 'prior': (list[str]) } }

    !! not stable for 'treatment drugs' (name field contains multiple names)
    '''
    columns= []
    master_dict = {}
    with open(PATH+filename) as csvfile:
        reader_list = list(csv.reader(csvfile))
        if not columns:
            for each in reader_list[1]:
                columns.append(each.strip().lower())
        what_type = ''

        #loop through each row
        for i in range(1,len(reader_list)):
            row = reader_list[i]
            if row[0]:
                what_type = row[0]
            name = row[1].replace('\xc2',' ').replace('\xa0',' ')
            master_dict[name] = {'name': name, 'type': what_type, 'avoid': [], 'prior': [], 'minimize':{}}
            #loop through each column
            for j in range(2,len(row)):
                #avoid
                if row[j] == 'A':
                    master_dict[name]['avoid'].append(columns[j])
                #prioritize
                elif row[j] == 'P':
                    master_dict[name]['prior'].append(columns[j])
                #TODO: minimize
                elif '|' in row[j]:
                    split = row[j].split('|')
                    min1 = split[0]
                    min2 = split[1]
                    master_dict[name]['minimize'][columns[j]] = {"min1":min1, "min2":min2}
    return master_dict, columns

if __name__ == "__main__":
    master_dict, columns = processFoodMatrixCSV('Euphebe/new.csv')
    # generate_keyword(columns)
    add_tags(master_dict)
    # pprint.pprint(processFoodMatrixCSV(''))
    # pdb.set_trace()
