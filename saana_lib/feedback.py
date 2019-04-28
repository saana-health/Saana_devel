import connectMongo
import pprint
import pdb
from bson import ObjectId

def get_lateset_symptoms(patient_id):
    '''
    Return a dictionary of worsened and alleviated symptoms

    :param patient_id: patient of interest
    :return: dict - {'worsen':[ObjectId()], 'better':[ObjectId()]}
    '''
    # symptoms - [ObjectId()]
    symptom_ids = connectMongo.db.patient_symptoms.distinct('symptom_id',{'patient_id':patient_id})
    dict = {'worsen':[], 'better':[]}
    for symptom_id in symptom_ids:
        recent_logs = list(connectMongo.db.patient_symptoms.find({'symptom_id':symptom_id}).sort([('created_at',-1)]).limit(2))
        if recent_logs[0]['symptoms_scale'] - recent_logs[1]['symptoms_scale'] >= 0:
            dict['worsen'].append(symptom_id)
        else:
            dict['better'].append(symptom_id)
    return dict

if __name__ == "__main__":
    get_lateset_symptoms(ObjectId('5cabf2ad37c87f3ac00e8701'))
