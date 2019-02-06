import csv
import pprint
import os
from connectMongdo import add_tags
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
    with open(PATH+'Food_Tags_Matrix.csv') as csvfile:
        reader_list = list(csv.reader(csvfile))
        if not columns:
            for each in reader_list[1]:
                columns.append(each)
        what_type = ''

        #loop through each row
        for i in range(1,len(reader_list)):
            row = reader_list[i]
            if row[0]:
                what_type = row[0]
            master_dict[row[1]] = {'name': row[1], 'type': what_type, 'avoid': [], 'prior': []}
            #loop through each column
            for j in range(2,len(row)):
                #avoid
                if row[j] == 'A':
                    master_dict[row[1]]['avoid'].append(columns[j])
                #prioritize
                elif row[j] == 'P':
                    master_dict[row[1]]['prior'].append(columns[j])
    return master_dict


if __name__ == "__main__":
    add_tags(processFoodMatrixCSV(''))
    pprint.pprint(processFoodMatrixCSV(''))
