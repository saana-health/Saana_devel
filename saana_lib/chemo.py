from . import connectMongo
import pdb

def get_chemo_dates(patient_id, date_from, date_to):
    chemo_dates = list(connectMongo.db.patient_treatment_dates.find({'patient_id':patient_id, 'treatment_date':\
        {'$gte':date_from, '$lte':date_to}}))
    treatment_dates = [x['treatment_date'] for x in chemo_dates]
    delta_dates = [(treatment_date - date_from).days for treatment_date in treatment_dates]
    pdb.set_trace()
    return delta_dates

def reorder_chemo(slots, patient_id, start_date, end_date):
    delta_dates = get_chemo_dates(patient_id, start_date, end_date)
    return slots