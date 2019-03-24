import csv
import pprint
from pdb import set_trace
from model import Patient
from connectMongdo import get_any, add_patients, drop
import ast
from utils import process_mixpanel_csv
import pickle
import test

# with open('mixpanelData.csv','rb') as csvfile:
#     dic = {}
#     li = []
#     reader = csv.reader(csvfile)
#     r_list = list(reader)
#     for cell in r_list[0]:
#         li.append(cell)
#     for i in range(len(r_list[0])):
#         dic[li[i]] = r_list[1][i]
#
# te = list(get_any('tags','name','Breast'))
#
#
# # process_mixpanel_csv('maggie.csv')
# st = dic['symptoms']
# symptoms_dict = ast.literal_eval(st)
# symptoms = []
# for key in symptoms_dict.keys():
#     li = list(get_any('tags','_id',key))
#     if li != []:
#         symptoms.append(li[0])
# # symptoms = [get_any('tags','_id',x) for x in symptoms_dict.keys()]
# disease = list(get_any('tags','name','Breast'))[0]['_id']
# treatment_drugs = ast.literal_eval(dic['treatment_drugs']).keys()
#
# # maggie = Patient(name = 'Maggie', comorbidities= [], disease = disease, symptoms = symptoms )
def add_maggie():
    disease = get_any('tags','name','breast')['_id']
    symptoms = get_any('tags','name',['diarrhea','dry mouth','dry skin','fatigue','loss of appetite','mouth & throat sore','nausea','cough','stomach acidity','sleeping problems'])
    # TODO: treatment_drugs not working?
    treatment_drugs = get_any('tags','name', ['docetaxel (taxotere)','carboplatin (paraplatin)','trastuzumab (herceptin)','pertuzumab (perjeta)',\
                                              'olanzapine (zyprexa)','prochlorperazine (compazine)','ondanstetron (zofran)','ioperamide (imodium)'])
    maggie = Patient(name = 'Maggie', comorbidities= [], treatment_drugs = treatment_drugs, disease = disease, symptoms = [x['_id'] for x in symptoms])
    drop('patients')
    add_patients(maggie)

if __name__ == "__main__":
    drop('patients')
    add_maggie()

