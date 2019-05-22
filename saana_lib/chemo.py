from . import connectMongo
import pdb

def get_chemo_dates(patient_id, date_from, date_to):
    chemo_dates = list(connectMongo.db.patient_treatment_dates.find({'patient_id':patient_id, 'treatment_date':{'$gte':date_from, '$lte':date_to}}))
    return chemo_dates

