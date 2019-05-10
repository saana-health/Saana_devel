import csv
import pdb
from .. import connectMongo

def add_from_matrix(filename):
    with open(filename) as csvfile:
        reader_list = list(csv.reader(csvfile))
        herbs = [x.lower() for x in reader_list[1] if x != '' ]
    for herb in herbs:
        connectMongo.db.mst_herbs.insert_one({'name':herb})
