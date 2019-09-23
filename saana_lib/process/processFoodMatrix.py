import csv
import os
from saana_lib import connectMongo, utils
from constants import constants_wrapper as constants

"""
NOTE: This function does NOT find and replace what is currently 
in the database it just appends it at the end. You have to clear 
out the database first before pushing in the new matrix
"""

PATH = os.path.join(os.getcwd(),'csv/')


class FoodMatrixException(Exception):
    """"""


class FoodMatrix(object):

    def __init__(self, filename):
        self.master_dict = {}
        self.ignored = []
        self.filename = filename
        self._content_iterator = None
        self.client_db = connectMongo.db
        self.cols_to_skip = 2
        self._tags = None

    def load_file(self):
        try:
            return open(self.filename, 'r')
        except (FileNotFoundError, IsADirectoryError) as e:
            raise FoodMatrixException(
                "Exception: {} occurred while handling file: {}".format(
                    e, self.filename
                )
            )

    def content_iterator(self):
        if not self._content_iterator:
            self._content_iterator = csv.reader(self.load_file())
        return list(self._content_iterator)

    def column_headers(self):
        if not self.content_iterator():
            raise FoodMatrixException("Empty file")
        headers = self.content_iterator()[0]
        return headers.split(',')

    @property
    def tags(self):
        if not self._tags:
            self._tags = dict(
                ((tag['name'], tag['type']), tag) for tag in self.client_db.tags.find()
            )
        return self._tags

    def str_to_list(self, str_row, sep=','):
        row = str_row.split(sep) if isinstance(str_row, str) else list()
        if len(row) < 3 or row[0] not in ['', None] or row[1] not in ['', None]:
            raise FoodMatrixException()
        return row

    def add_or_remove_element(self, el, _list: list, action_key):
        import pdb;pdb.set_trace()
        if action_key == constants.ELEMENT_REMOVE_ACTION_KEY:
            if el in _list:
                _list.remove(_list.index(el))
        elif action_key == constants.ELEMENT_AVOID_ACTION_KEY and el not in _list:
            _list.append(el)
        elif action_key == constants.ELEMENT_MINIMIZE_ACTION_KEY and el not in _list:
            _list.append(el)
        elif action_key == constants.ELEMENT_PRIORITIZE_ACTION_KEY and el not in _list:
            _list.append(el)

        return _list

    def updated_content_row(self, row):

        def list_name(key):
            dict(constants.ELEMENT_ACTION_KEYS).get(key)

        name, tag_type = row[0], row[1]
        current_record = self.tags.get((name, tag_type))

        errs = dict()
        for i, action_key in enumerate(row[self.cols_to_skip:]):
            if action_key not in constants.ELEMENT_ACTION_KEYS:
                if action_key:
                    errs[i] = "invalid option {}".format(action_key)
                continue

            elem_name = self.column_headers()[i]
            current_record[list_name(action_key)] = self.add_or_remove_element(
                elem_name,
                current_record.get(list_name(action_key)),
                action_key
            )

        return current_record

    def read_rows(self):
        """
        Temporarily we keep the CSV file as the input. Soon we'll
        switch to XLS files.
        """
        for p, row in self.content_iterator()[1:]:
            row = self.str_to_list(row)
            data = {
                'type': row[0],
                'name': row[1]

            }
        return



def processFoodMatrixCSV(filename):
    """
    from now the type is expected to be at pos[0] for each line
    name cannot be empty, otherwise which tag is going to be updated,
    otherwise it will be ignored

    """
    master_dict = {}
    ignored = []

    csvfile = None
    reader_list = list(csv.reader(csvfile))
    if len(reader_list) < 1:
        return master_dict, []

    # TODO whj
    columns = [row.strip().lower() for row in reader_list[0]]
    what_type = ''

    for i in range(1, len(reader_list)):
        row = reader_list[i]
        if row[0]:
            what_type = row[0].strip().lower()
        name = row[1].replace('\xc2',' ').replace('\xa0',' ').strip().lower()
        if name == 'head &  neck':
            name = 'head & neck'
        if name == '':
            continue

        tags = list(connectMongo.db.mst_diseases.find())
        tags += list(connectMongo.db.mst_comorbidities.find())
        tags += list(connectMongo.db.mst_drugs.find())
        tags += list(connectMongo.db.mst_symptoms.find())
        tag_id = None

        for tag in tags:
            if name in tag['name'].lower() or utils.similar(name, tag['name'], 0.7):
                print('{}   |   {}'.format(name, tag['name']))
                tag_id = tag['_id']

        master_dict[name] = {
            'name': name,
            'type': what_type,
            'avoid': [],
            'prior': {},
            'minimize':{},
            'tag_id': tag_id
        }

        for j in range(2,len(row)):
            if row[j] == 'A':
                master_dict[name]['avoid'].append(columns[j].strip().lower())
            # Letter 'P' basically converted into zero
            elif row[j] == 'P':
                # master_dict[name]['prior'].append(columns[j].strip().lower())
                master_dict[name]['prior'][columns[j].strip().lower()] = 0
            elif '|' in row[j]:
                split = row[j].split('|')
                min1 = split[0]
                min2 = split[1]
                master_dict[name]['minimize'][columns[j]] = {"min1": min1, "min2": min2}
            # prioritize above threshold
            elif is_number(row[j]):
                master_dict[name]['prior'][columns[j].strip().lower()] = float(row[j])

    # [x for x in list(set(columns)) if x]
    return master_dict, ignored


def is_number(num):
    try:
        float(num)
    except ValueError:
        return False
    return True
