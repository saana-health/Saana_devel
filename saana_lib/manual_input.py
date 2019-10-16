import csv
from saana_lib import connectMongo


def manual_input(filename):
    """
    first line of file -> suppliers
    second line of file -> emails of patients to run algorithm on
    :param filename:
    :return: suppliers IDs and patients email addresses
    """
    suppliers = []
    # restrictions = [] # feature needs to be added in later
    patients = []
    with open(filename) as csvfile:
        reader = list(csv.reader(csvfile))
        # list_restrictions = list(reader)[1]

        if len(reader) >= 1:
            list_supplier = reader[0]
            suppliers = [
                x['_id'] for x in connectMongo.db.users.find(
                    {'role':'supplier','first_name': {'$in': list_supplier}},
                    {'_id':1})
            ]
        if len(reader) >= 2:
            patients = reader[1]

    return suppliers, patients



