import csv
from re import match

from pymongo.collection import ObjectId

from constants import constants_wrapper as constants
from exceptions import RequiredArgumentException
from saana_lib.abstract import OutIn
from saana_lib.connectMongo import db
from saana_lib.utils import similar

"""
NOTE: This function does NOT find and replace what is currently 
in the database it just appends it at the end. You have to clear 
out the database first before pushing in the new matrix
"""


class FoodMatrixException(Exception):
    """"""


class Cell:

    def __init__(self, value=None):
        self.value = value

    def read(self):
        """
        :return: the current cell's content
        """
        pass

    def delete(self):
        """
        delete's the current cell's content
        """
        pass

    def contains(self):
        """
        compares the current cell's content with the one provided
        :returns True/False
        """
        pass

    def update(self):
        """
        changes the current cell's content
        """
        pass

    def is_empty(self):
        """
        :return: True/False whether the content
        """


class Tag:

    def __init__(self, tag_id=None, content_row=list(), tag_name=None, tag_type=None):
        self.tag_id = tag_id
        if not isinstance(tag_id, ObjectId):
            self.tag_id = ObjectId(tag_id)

        self.content_row = content_row
        if tag_id:
            self.tag = db.tags.find_one({'tag_id': tag_id})
        elif tag_name and tag_type:
            self.tag = db.tags.find_one({'name': tag_name, 'type': tag_type})
        else:
            self.tag = None

        if not (self.tag or self.content_row):
            raise RequiredArgumentException("")

    def sequence(self, group_name):
        list_key = {
            'prior': 'P',
            'minimize': 'M',
            'nutrient': 'N',
        }.get(group_name)
        if self.content_row:
            self.tag[group_name] = {}
            for cell in self.content_row:
                if not len(cell) == 2:
                    continue

                quantity_rex = r'^{}-(?P<quantity>\d+(\.\d+)?)$'.format(list_key)
                range_rex = r'^{}-(?P<lower>\d+)\|(?P<upper>\d+)$'.format(list_key)
                m = match(quantity_rex, cell[1] ) or match(range_rex, cell[1])
                if m:
                    if 'quantity' in m.groupdict():
                        quantity = m.groupdict().get('quantity')
                    else:
                        quantity = m.groupdict()
                    self.tag[group_name].update({cell[0]: quantity})
        return self.tag[group_name]

    @property
    def prioritize_sequence(self):
        return self.sequence('prior')

    @property
    def minimize_sequence(self):
        return self.sequence('minimize')

    @property
    def nutrient_sequence(self):
        return self.sequence('nutrient')

    @property
    def avoid_sequence(self):
        if self.content_row:
            self.tag['avoid'] = {}
            for cell in self.content_row:
                if not len(cell) == 2:
                    continue
                m = match(r'^A-(?P<quantity>\d+(\.\d+)?)$', cell[1])
                if m:
                    quantity = m.groupdict().get('quantity')
                    self.tag['avoid'].update({cell[0]: quantity})
        return self.tag['avoid']

    def all_elements_names(self):
        if not self.tag:
            return list()

        return list(self.prioritize_sequence) + list(self.minimize_sequence) + \
            list(self.nutrient_sequence)


class Table(OutIn):
    """"""


class Matrix(OutIn):
    """"""




class TagEntity(object):

    def __init__(self):
        self.name = ''
        self.tag_type = ''
        self.avoid = list()
        self.minimize = dict()
        self.prioritize = dict()

    def to_dict(self):
        return {
            'name': self.name,
            'type': self.tag_type,
            'prior': self.prioritize,
            'minimize': self.minimize,
            'avoid': self.avoid
        }




class TagMatrix(object):

    def __init__(self, filename):
        self.master_dict = {}
        self.ignored = []
        self.filename = filename
        self._content_iterator = None
        self.client_db = db
        self.cols_to_skip = 2
        self._tags = None
        self.new = False
        self.current_record = {}

    @property
    def new_row(self):
        return {
            'type': 'cancer',
            'name': 'breast',
            'avoid': list(),
            'prior': dict(),
            'minimize': dict()
        }

    def load_file(self):
        try:
            return open(self.filename, 'r')
        except (FileNotFoundError, IsADirectoryError) as e:
            raise FoodMatrixException(
                "Exception: {} occurred while handling file: {}".format(
                    e, self.filename
                )
            )

    @property
    def content_iterator(self):
        if not self._content_iterator:
            self._content_iterator = csv.reader(self.load_file())
        return list(self._content_iterator)

    @property
    def column_headers(self):
        if not self.content_iterator:
            raise FoodMatrixException("Empty file")
        headers = self.content_iterator[0]
        return headers.split(',')

    @property
    def tags(self):
        if not self._tags:
            self._tags = dict(
                ((tag['name'], tag['type']), tag) for tag in self.client_db.tags.find()
            )
        return self._tags

    def str_to_list(self, str_row, sep=','):
        """"""
        row = str_row.split(sep) if isinstance(str_row, str) else list()
        if len(row) < 3 or row[0] in ['', None] or row[1] in ['', None]:
            raise FoodMatrixException()
        return row

    def whereis_elem(self, elem_name, current_record):
        """
        Brutally iterates over the three list/dict of the record
        and search where the element is located
        :return: if the element is in `avoid`, returns `avoid`
        and the position within the list, otherwise the name of
        the dictionary and -1, that will be correclty interpreted
        at the caller
        """
        list_name = ''
        pos = -1
        if elem_name in current_record['avoid']:
            list_name = 'avoid'
            pos = current_record['avoid'].index(elem_name)
        if elem_name in current_record['prior']:
            list_name = 'prior'
        if elem_name in current_record['minimize']:
            list_name = 'minimize'
        return list_name, pos

    def remove_element(self, elem_name, current_record):
        list_name, pos = self.whereis_elem(elem_name, current_record)
        if not list_name:
            return current_record
        elif pos < 0:
            current_record.get(list_name).pop(elem_name)
        else:
            current_record.get(list_name).pop(pos)
        return current_record

    def changed_status(self, current_record, elem, action):
        """
        :param current_record: the current DB record as dict
        :param elem: the elem under analysis
        :param action: basically it is one of the three letters
        A|M|P. The reason why this parameter was given such name
        is because it indicates which action the patient should
        attain (avoid|minimize|prioritize a certain element)
        :return: True if the element was moved to a list different
        than the one it pertains now
        """
        changed = False
        if not current_record:
            return changed
        elif action == constants.ELEMENT_AVOID_KEY:
            changed = elem not in current_record['avoid']
        elif action == constants.ELEMENT_MINIMIZE_KEY:
            changed = elem not in current_record['minimize']
        elif action == constants.ELEMENT_PRIORITIZE_KEY:
            changed = elem not in current_record['prior']
        return changed

    def updated_row(self, row, current_record, row_n):
        """
        Scan the current xls row, and updates the current record
        accordingly. For each value in row, remove/update/leave
        as it is, the corresponding value in the record.
        It might also mean moving one element from one list to
        another.
        Ex: if element X belongs to the `avoid` list (which means
        it's in current_record['avoid']) and its value in ROW is
        M (minimize) that implies it'll be moved to this list and
        removed from `avoid`.
        allowed values are any of the following patterns: '', 'M',
        'A', 'P', 'R', number or number|number. Numbers might be
        integer or internally
        are cast to float.
        :param row: a list of values
        :param current_record: dictionary
        :param row_n: this index is passed only for logging purpose
        """
        errs = dict()
        for i, row_value in enumerate(row[self.cols_to_skip:len(self.column_headers)], start=self.cols_to_skip):

            elem_name = self.column_headers[i]
            if row_value == '':
                continue

            elif row_value in constants.ELEMENT_ACTION_KEYS:
                changed_status = self.changed_status(
                    current_record, elem_name, row_value
                )
                if row_value == constants.ELEMENT_REMOVE_KEY or changed_status:
                    current_record = self.remove_element(elem_name, current_record)

                if row_value == constants.ELEMENT_AVOID_KEY:
                    if elem_name not in current_record['avoid']:
                        current_record['avoid'].append(elem_name)
                elif row_value == constants.ELEMENT_PRIORITIZE_KEY:
                    if elem_name not in current_record['prior']:
                        current_record['prior'][elem_name] = 0
                elif row_value == constants.ELEMENT_MINIMIZE_KEY:
                    if elem_name not in current_record['minimize']:
                        current_record['minimize'][elem_name] = 0

            else:
                list_name, pos = self.whereis_elem(elem_name, current_record)
                m = match(r'(?P<quantity>^\d+(\.\d+)?$)', row_value) or \
                    match(r'^(?P<range>(\d+)\|(\d+)$)', row_value)

                if not m:
                    errs[elem_name] = "Invalid value {} @cell: {}:{}".format(
                        row_value, row_n, i
                    )

                elif list_name == 'avoid':
                    errs[elem_name] = "Cannot assign a quantity value to {} " \
                              "because is in the avoid list: {}:{}".format(
                        elem_name, row_n, i
                    )

                elif m.groupdict().get('quantity'):
                    new_val = float(row_value)
                    if pos == -1:
                        current_record[list_name][elem_name] = new_val
                    else:
                        current_record[list_name][pos] = new_val
                elif m.groupdict().get('range'):
                    low, up = row_value.split("|")
                    current_record[list_name][elem_name] = {
                        'min1': float(low), 'min2': float(up)
                    }

        return current_record, errs

    def quantity_value(self, v):
        m = match(r'^(?P<list>[MP])-(?P<quantity>\d+(\.\d+)?)$', v) or \
            match(r'^(?P<list>[MP])-(?P<min1>\d+)\|(?P<min2>\d+)$', v)
        return m

    @property
    def key_mappings(self):
        return {
            constants.ELEMENT_AVOID_KEY: 'avoid',
            constants.ELEMENT_PRIORITIZE_KEY: 'prior',
            constants.ELEMENT_MINIMIZE_KEY: 'minimize'
        }

    def new_record(self, row, row_n):
        record = self.new_row
        errs = dict()
        for i, row_value in enumerate(
                row[self.cols_to_skip:len(self.column_headers)],
                start=self.cols_to_skip):
            elem_name = self.column_headers[i]
            if row_value == '':
                continue

            m = self.quantity_value(row_value)
            if m:
                list_name = self.key_mappings.get(
                    m.groupdict().get('list')
                )
                if m.groupdict().get('min1'):
                    val = {
                        'min1': float(m.groupdict().get('min1')),
                        'min2': float(m.groupdict().get('min2'))
                    }
                else:
                    val = float(m.groupdict().get('quantity'))
                record[list_name][elem_name] = val

            elif row_value in self.key_mappings:
                if row_value == constants.ELEMENT_AVOID_KEY:
                    record[self.key_mappings.get(row_value)].append(elem_name)
                else:
                    record[self.key_mappings.get(row_value)][elem_name] = 0
            else:
                errs[elem_name] = "Invalid value @cell {}:{}".format(row_n, i)

        return record, errs

    def updated_content(self):
        """
        Temporarily we keep the CSV file as the input. Soon we'll
        switch to XLS files.
        """
        content_list = list()
        errs = dict()
        for row_n, row in enumerate(self.content_iterator[1:], start=1):
            if not row:
                continue
            row = self.str_to_list(row)
            name, tag_type = row[0], row[1]
            current_record = self.tags.get((name, tag_type))
            if current_record:
                record, errs = self.updated_row(
                    row, current_record, row_n
                )
            else:
                record, errs = self.new_record(row, row_n)
            content_list.append({
                'type': tag_type,
                'name': name,
                'avoid': record['avoid'],
                'prior': record['prior'],
                'minimize': record['minimize'],
            })

        return content_list, errs

    def update(self):
        counter = 0
        content, errs = self.updated_content()
        for tag_record in content:
            result = self.client_db.tags.replace_one(
                {'name': tag_record['name']},
                tag_record,
                upsert=True
            )
            if result.modified_count or result.upserted_id:
                counter += 1

        return counter, errs


# TODO to remove
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

        tags = list(db.mst_diseases.find())
        tags += list(db.mst_comorbidities.find())
        tags += list(db.mst_drugs.find())
        tags += list(db.mst_symptoms.find())
        tag_id = None

        for tag in tags:
            if name in tag['name'].lower() or similar(name, tag['name'], 0.7):
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
