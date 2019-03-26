import pdb
import csv
import pprint
from pdb import set_trace
from model import Patient
from connectMongdo import get_any, add_patients, drop
import ast
from utils import process_mixpanel_csv
import pickle
import test

def add_maggie():
    disease = get_any('tags','name','breast')['_id']
    symptoms = get_any('tags','name',['diarrhea','dry mouth','dry skin','fatigue','loss of appetite','mouth & throat sore','nausea','cough','stomach acidity','sleeping problems'])
    treatment_drugs = get_any('tags','name', ['docetaxel (taxotere)','carboplatin (paraplatin)','trastuzumab (herceptin)','pertuzumab (perjeta)',\
                                              'olanzapine (zyprexa)','prochlorperazine (compazine)','ondanstetron (zofran)','ioperamide (imodium)'])
    maggie = Patient(name = 'Maggie', comorbidities= [], treatment_drugs = [x['_id'] for x in treatment_drugs], disease = disease, symptoms = [x['_id'] for x in symptoms])
    drop('patients')
    add_patients(maggie)

if __name__ == "__main__":
    add_maggie()

