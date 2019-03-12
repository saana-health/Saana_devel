import csv
import pprint
from pdb import set_trace
from model import Patient
from connectMongdo import find_disease, get_any, add_patients
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

disease = get_any('tags','name','Breast')['_id']
symptoms = get_any('tags','name',['Diarrhea','Dry mouth  ','Dry skin','Fatigue','Loss of appetite','Mouth & throat sore'])
# treatment_drugs = get_any('tags','name')

maggie = Patient(name = 'Maggie', comorbidities= [], disease = disease, symptoms = [x['_id'] for x in symptoms])

add_patients(maggie)

set_trace()

