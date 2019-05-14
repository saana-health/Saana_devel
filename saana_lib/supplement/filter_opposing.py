import pdb
import csv
from .. import connectMongo
from . import herb_matrix
from . import patient_type

def filter_avoids(patient_id):
    '''
    Get rid of herbs with avoid tags
    :param patient_id: ObjectId()
    :return: [str], [ObjectId()] - [str] being a list of appropriate herbs and [ObjectId()] being a list of symptoms of a patient
    '''
    # get all herbs
    herbs = list(connectMongo.db.mst_herbs.find())
    # get _id of all symptoms of a patient
    symptoms = list(set([x['symptom_id'] for x in list(connectMongo.db.patient_symptoms.find({'patient_id':patient_id}))]))
    # get avoid dictionary
    interaction_matrix = herb_matrix.process_herb_matrix('./csv/herb_interaction_matrix.csv')
    avoid_list = []

    # based on the patient's symptoms, generate a list of avoid herbs
    for symptom in symptoms:
        if symptom in interaction_matrix.keys():
            avoid_list += interaction_matrix[symptom]
        else:
            continue
    # compress
    avoid_list = list(set(avoid_list))

    # non-avoid list (appropriate herbs)
    okay_list = [x['name'] for x in herbs if x['name'] not in avoid_list]
    return okay_list, symptoms

def optimize_herb(patient_id):
    '''
    Return a list of herbs sorted by how well each match with a patient's body type, symptoms
    :param patient_id: ObjectId()
    :return: [str] - sorted list of herbs
    '''
    # Get body type
    temperature, type = patient_type.determine_body_type(patient_id)
    parsed_type= '{}/{}'.format(temperature,type)
    print("Patient's body type is {}".format(parsed_type))

    # get appropriate herbs based on herb_interaction_matrix (non-avoids)
    interaction_filtered_list, symptom_ids= filter_avoids(patient_id)
    print("Herbs that doesn't have any conflicts from herb_interaction_matrix are:")
    print(interaction_filtered_list)

    # get herbs that match patient's body type
    type_dict, match_count_dict = get_herb_type('./csv/herb_symptoms_matrix.csv', symptom_ids)
    type_filtered_list = type_dict[parsed_type]
    print("Herbs that have matching body type are:")
    print(type_filtered_list)

    # get the intersection of the above two lists
    dot_product = [x for x in interaction_filtered_list if x in type_filtered_list]
    print("Intersection between the two are:")
    print(dot_product)

    # sort by the number of matching symptoms
    sorted_dot_product = sorted(dot_product, key = lambda herb: match_count_dict[herb], reverse=True)

    return sorted_dot_product

def get_herb_type(filename, symptom_ids):
    '''
    Get a dictionary of lists of herbs corresponding to different body types
    :param filename: str = 'herb_symptoms_matrix.csv'
    :return: {str: [str]}, {str: int} - where the first dictionary's keys are body types and values are the list of corresponding herbs
                                        second dictionary's keys are herbs and values are # of patient's symptoms covered by each herb
            ex)
            {'C/W':['Aloe']}, {'Aloe':3}
    '''

    with open(filename) as csvfile:
        reader_list = list(csv.reader(csvfile))
        columns = [x.lower() for x in reader_list[1]]
        type_dict = {}
        match_count = {}
        for ind in range(2,len(columns)):
            # print('---{}---'.format(ind))
            column = columns[ind]
            match_count[column] = 0
            # 26th, 27th row each corresponds to c/w and m/d (subject to change)
            patient_type = '{}/{}'.format(reader_list[26][ind], reader_list[27][ind])
            if patient_type in type_dict.keys():
                type_dict[patient_type].append(column)
            else:
                type_dict[patient_type] = [column]

            for row_ind in range(2,len(reader_list)):
                row = reader_list[row_ind]
                if row[1] =='':
                    break
                symptom_id = connectMongo.db.mst_symptoms.find_one({'name':row[1]})['_id']
                if symptom_id in symptom_ids and row[ind] != '':
                    match_count[column] += 1
    return type_dict, match_count





