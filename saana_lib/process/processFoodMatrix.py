import csv
from re import match
from saana_lib import connectMongo, utils
from constants import constants_wrapper as constants

"""
NOTE: This function does NOT find and replace what is currently 
in the database it just appends it at the end. You have to clear 
out the database first before pushing in the new matrix
"""



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

    def whereis_elem(self, elem_name, current_record):
        list_name = ''
        pos = 0
        if elem_name in current_record['avoid']:
            list_name = 'avoid'
            pos = current_record['avoid'].index(elem_name)
        if elem_name in current_record['prior']:
            list_name = 'prior'
            pos = current_record['prior'].index(elem_name)
        if elem_name in current_record['minimize']:
            list_name = 'minimize'
            pos = current_record['minimize'].index(elem_name)
        return list_name, pos

    def remove_element(self, elem_name, current_record):
        list_name, pos = self.whereis_elem(elem_name, current_record)
        if not list_name:
            return current_record

        current_record.get(list_name).pop(pos)
        return current_record

    def changed_status(self, current_record, elem, action):
        changed = False
        if action == constants.ELEMENT_AVOID_ACTION_KEY:
            changed = elem not in current_record['avoid']
        elif action == constants.ELEMENT_MINIMIZE_ACTION_KEY:
            changed = elem not in current_record['minimize']
        elif action == constants.ELEMENT_PRIORITIZE_ACTION_KEY:
            changed = elem not in current_record['prior']
        return changed

    def updated_content_row(self, row, current_record, row_n):
        errs = dict()
        for i, row_value in enumerate(row[self.cols_to_skip:], start=self.cols_to_skip):
            elem_name = self.column_headers()[i]
            if row_value in constants.ELEMENT_ACTION_KEYS:
                changed_status = self.changed_status(
                    current_record, elem_name, row_value
                )
                if row_value == constants.ELEMENT_REMOVE_ACTION_KEY or changed_status:
                    current_record = self.remove_element(elem_name, current_record)

                if row_value == constants.ELEMENT_AVOID_ACTION_KEY:
                    if elem_name not in current_record['avoid']:
                        current_record['avoid'].append(elem_name)
                elif row_value == constants.ELEMENT_PRIORITIZE_ACTION_KEY:
                    if elem_name not in current_record['prior']:
                        current_record['prior'].append(elem_name)
                elif row_value == constants.ELEMENT_MINIMIZE_ACTION_KEY:
                    if elem_name not in current_record['minimize']:
                        current_record['minimize'].append(elem_name)

            elif match(r'^\d+$', row_value):
                new_val = (elem_name, float(row_value))
                list_name, pos = self.whereis_elem(elem_name, current_record)
                if not list_name:
                    continue
                current_record[list_name][pos] = new_val
            elif match(r'^(\d+)\|(\d+)$', row_value):
                low, up = row_value.split("|")
                list_name, pos = self.whereis_elem(elem_name, current_record)
                if not list_name:
                    continue
                current_record[list_name][pos] = (
                    elem_name, {'min1': float(low), 'min2': float(up)}
                )
            else:
                errs[elem_name] = "Invalid value for cell: {}:{}".format(row_n, i)

        return current_record, errs

    def read_rows(self):
        """
        Temporarily we keep the CSV file as the input. Soon we'll
        switch to XLS files.
        """
        for row_n, row in self.content_iterator()[1:]:
            row = self.str_to_list(row)
            name, tag_type = row[0], row[1]
            data = {
                'type': tag_type,
                'name': name,
            }
            current_record = self.tags.get((name, tag_type))
            updated_record, errs = self.updated_content_row(row, current_record, row_n)

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
