from .. import connectMongo
import pdb
import csv

def determine_body_type(patient_id):
    '''
    Calculates a patient's body type by getting info from db
    :param patient_id: ObjectId()
    :return: Str,Str - ex) 'C','M'
    '''
    # dictionary to store type counts
    type_dict = {'warm':0, 'cold':0, 'dry':0, 'moist':0}
    type_info = connectMongo.db.patient_body_type_questions.find_one({'patient_id':patient_id})

    #temperature
    if type_info['body_temperature'] == 'warmer_and_overheat':
        type_dict['warm'] += 1
    else:
        type_dict['warm'] -= 1

    #hearbeat
    if type_info['heartbeat'] == 'fast_and_louder':
        type_dict['warm'] += 1
    else:
        type_dict['warm'] -= 1

    # tongue
    if type_info['tongue'] == 'bright_red':
        type_dict['warm'] += 1
    elif type_info['tongue'] == 'pale_pink':
        type_dict['cold'] += 1

    # mucosal
    if type_info['mucosal_membrane'] == 'dry_eyes_dry_nose_little_earwax':
        type_dict['dry'] += 1
    elif type_info['mucosal_membrane'] == 'excess_mucus_earwax':
        type_dict['moist'] += 1

    # muscle_strain_
    if type_info['muscle_strain'] == 'yes_often':
        type_dict['dry'] += 1

    elif type_info['muscle_ache'] == 'not_sure':
        type_dict['moist'] += 1

    # others
    if 'dry_skin' in type_info['others']:
        type_dict['dry'] += 1
    if 'dry_scalp' in type_info['others']:
        type_dict['dry'] += 1
    if 'brittle_fingernails' in type_info['others']:
        type_dict['dry'] += 1
    if 'dry_mouth' in type_info['others']:
        type_dict['dry'] += 1
    if 'oily_skin' in type_info['others']:
        type_dict['moist'] += 1
    if 'oily_hair' in type_info['others']:
        type_dict['moist'] += 1
    if 'excess_perspiration' in type_info['others']:
        type_dict['moist'] += 1
    if 'runny_nose' in type_info['others']:
        type_dict['moist'] += 1

    # decide
    # TODO: right now, there is no tie-breaker, so the algorithm favors C > W, D > M if a tie
    if type_dict['cold'] >= type_dict['warm']:
        temperature = 'C'
    else:
        temperature = 'W'

    if type_dict['dry'] >= type_dict['moist']:
        type = 'D'
    else:
        type = 'M'

    return temperature, type
