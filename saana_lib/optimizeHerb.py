import pdb

from .supplement import filter_opposing

def optimizeHerb(patient_id):
    return filter_opposing.match_type(patient_id)[0]

