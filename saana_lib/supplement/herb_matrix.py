import pdb
import csv
from .. import connectMongo
from bson import ObjectId

def process_herb_matrix(filename):
    '''
    Returns a dictionary of herbs to AVOID for each symptom
    :param filename: str - 'herb_interaction_matrix.csv'
    :return: {ObjectId()(/str) :[str]} - ObjectId being symptom._id and [str] being a list of herbs
    # TODO: herbs need to be based on _id, not name
    '''
    herb_dict = {}
    with open(filename) as csvfile:
        reader_list = list(csv.reader(csvfile))
        # symptoms from the csv file
        columns = [x.lower() for x in reader_list[0]]

        symptoms = list(connectMongo.db.mst_symptoms.find())
        for ind in range(len(columns)):
            column = columns[ind]
            for symptom in symptoms:
                # replace the name with ObjectId if a symptom from the csv file exists in db by string matching,
                if symptom['name'].lower() == column.lower() or symptom['name'].lower() in column.lower():
                    columns[ind] = symptom['_id']

        # skip first two empty columns
        for column in columns:
            if column == '':
                continue
            herb_dict[column] = []

        # loop through each row and find non-empty cells ('A')
        for row_num in range(1,len(reader_list)):
            herb_name = reader_list[row_num][0].lower()
            for cell_num in range(1,len(reader_list[row_num])):
                if reader_list[row_num][cell_num] != '':
                    herb_dict[columns[cell_num]].append(herb_name)
    return herb_dict