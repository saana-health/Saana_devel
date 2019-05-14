import pdb
import csv
from .. import connectMongo
from bson import ObjectId

def process_herb_matrix(filename):
    '''
    for 'herb_interaction_matrix.csv'
    :param filename:
    :return:
    '''
    herb_dict = {}
    with open(filename) as csvfile:
        reader_list = list(csv.reader(csvfile))
        columns = [x.lower() for x in reader_list[0]]

        ###
        symptoms = list(connectMongo.db.mst_symptoms.find())
        for ind in range(len(columns)):
            column = columns[ind]
            for symptom in symptoms:
                if symptom['name'].lower() == column.lower() or symptom['name'].lower() in column.lower():
                    columns[ind] = symptom['_id']

        ###
        for column in columns:
            if column == '':
                continue
            herb_dict[column] = []
        for row_num in range(1,len(reader_list)):
            herb_name = reader_list[row_num][0].lower()
            for cell_num in range(1,len(reader_list[row_num])):
                if reader_list[row_num][cell_num] != '':
                    herb_dict[columns[cell_num]].append(herb_name)
    return herb_dict