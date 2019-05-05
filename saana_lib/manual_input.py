import csv
import pdb
from . import connectMongo

def manual_input(filename):
    '''
    first line of file -> suppliers
    second line of file -> manual restrictions
    :param filename:
    :return:
    '''
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        list_supplier = list(reader)[0]
        # list_restrictions = list(reader)[1]

        suppliers = [x['_id'] for x in list(connectMongo.db.users.find({'role':'supplier','first_name':{'$in': list_supplier}},{'_id':1}))]
        return suppliers
