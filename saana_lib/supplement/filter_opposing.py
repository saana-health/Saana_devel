import pdb
import csv
from .. import connectMongo
from . import herb_matrix
from . import patient_type

def filterd_opposing(patient_id):
    herbs = list(connectMongo.db.mst_herbs.find())
    symptoms = list(set([x['symptom_id'] for x in list(connectMongo.db.patient_symptoms.find({'patient_id':patient_id}))]))
    interaction_matrix = herb_matrix.process_herb_matrix('./csv/herb_interaction_matrix.csv')
    avoid_list = []

    for symptom in symptoms:
        if symptom in interaction_matrix.keys():
            avoid_list += interaction_matrix[symptom]
        else:
            continue

    avoid_list = list(set(avoid_list))
    okay_list = [x['name'] for x in herbs if x['name'] not in avoid_list]
    return okay_list, symptoms

def match_type(patient_id):
    temperature, type = patient_type.determine_body_type(patient_id)
    parsed_type= '{}/{}'.format(temperature,type)
    print("Patient's body type is {}".format(parsed_type))

    interaction_filtered_list, symptom_ids= filterd_opposing(patient_id)
    print("Herbs that doesn't have any conflicts from herb_interaction_matrix are:")
    print(interaction_filtered_list)

    type_dict, match_count_dict = get_herb_type('./csv/herb_symptoms_matrix.csv', symptom_ids)
    type_filtered_list = type_dict[parsed_type]
    print("Herbs that have matching body type are:")
    print(type_filtered_list)

    dot_product = [x for x in interaction_filtered_list if x in type_filtered_list]
    print("Intersection between the two are:")
    print(dot_product)

    sorted_dot_product = sorted(dot_product, key = lambda herb: match_count_dict[herb], reverse=True)

    return sorted_dot_product

def get_herb_type(filename, symptom_ids):
    '''
    for 'herb_symtoms_matrix.csv'
    :param filename:
    :return:
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





