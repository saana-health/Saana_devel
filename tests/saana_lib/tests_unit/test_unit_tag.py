import pytest

from exceptions import RequiredArgumentException
from saana_lib.tag import Cell, Tag
from tests.conftest import assert_equal_objects, assert_equal_tuples, obj_id


@pytest.fixture
def headers_mock(mocker):
    headers = mocker.patch(
        'saana_lib.process.processFoodMatrix.FoodMatrix.column_headers',
        new_callable=mocker.PropertyMock,
    )
    headers.return_value=[
        'type', 'name', 'mackerel', 'seaweed', 'potato', 'spinach'
    ]
    return headers


class TestCaseTag:

    def test_tag_initialisation_with_tag_id(self, mocker):
        m = mocker.patch('saana_lib.tag.db.tags')
        _ = Tag(tag_id=obj_id())
        m.find_one.assert_called_once_with({'tag_id': obj_id()})

    def test_tag_initialisation_with_tag_name(self, mocker):
        m = mocker.patch('saana_lib.tag.db.tags')
        _ = Tag(tag_name='breast', tag_type='cancer')
        m.find_one.assert_called_once_with({'name': 'breast', 'type': 'cancer'})

    def test_tag_initialisation_with_content_row(self, mocker):
        m = mocker.patch('saana_lib.tag.db.tags')
        _ = Tag(content_row=[['cell-1'], ['cell-2']])
        m.find_one.assert_not_called()

    def test_tag_initialisation_requires_one_argument(self):
        with pytest.raises(RequiredArgumentException):
            _ = Tag()

    def test_tag_prioritize_sequence_single_quantity(self):
        tag = Tag(content_row=[['flax', 'P-20']])
        assert {'flax': '20'} == tag.prioritize_sequence

    def test_tag_prioritize_sequence_quantity_range(self):
        tag = Tag(content_row=[['flax', 'P-200|300']])
        assert_equal_objects(
            {'flax': {'lower': '200', 'upper': '300'}},
            tag.prioritize_sequence
        )

    def test_tag_prioritize_invalid_cell_value(self):
        tag = Tag(content_row=[['flax', 'P-200|']])
        assert tag.prioritize_sequence == {}

    def test_tag_minimize_sequence_single_quantity(self):
        tag = Tag(content_row=[['flax', 'M-10']])
        assert {'flax': '10'} == tag.minimize_sequence

    def test_sequence_content_parsing(self):
        tag = Tag(content_row=[
            ['flax', 'A-10'], ['broccoli', 'P-0'], ['sodium', 'N-300']
        ])
        assert {'flax': '10'} == tag.avoid_sequence
        assert {} == tag.minimize_sequence
        assert {'broccoli': '0'} == tag.prioritize_sequence
        assert {'sodium': '300'} == tag.nutrient_sequence


@pytest.mark.skip('')
class TestCaseTagMatrix(object):

    @pytest.fixture
    def content_iterator(self, mocker):
        m = mocker.patch(
            'saana_lib.process.processFoodMatrix.FoodMatrix.content_iterator',
            new_callable=mocker.PropertyMock
        )
        return m

    @pytest.fixture
    def tags_mock(self, mocker):
        from tests.conftest import TAGS_DATA
        tags = mocker.patch('saana_lib.connectMongo.db.tags')
        tags.find.return_value = TAGS_DATA
        return tags

    def test_file_opening(self, file_opening):
        self.matrix_obj.load_file()
        assert file_opening.call_count == 1
        file_opening.assert_called_once_with('fname', 'r')

    def test_file_does_not_exists(self, file_opening):
        file_opening.side_effect = IsADirectoryError
        with pytest.raises(FoodMatrixException):
            self.matrix_obj.load_file()

    def test_iterator_is_loaded_once(self, mocker, file_opening):
        """
        Mind that the matrix object has to be initialized outside
        the range loop, otherwise at every iteration the inner
        _tags attribute will be create anew and the db method called
        at every iteration, that does not resemble the real case
        """
        csv_mock = mocker.patch('csv.reader')
        matrix = FoodMatrix('f')
        for i in range(2):
            _ = matrix.content_iterator

        csv_mock.assert_called_once_with(file_opening())

    def test_read_empty_file(self, content_iterator):
        """Without columns"""
        content_iterator.return_value = list()
        with pytest.raises(FoodMatrixException):
            self.matrix_obj.column_headers()

    def test_tags_property_call_count(self, tags_mock):
        """
        same as for test `test_iterator_is_loaded_once`
        """
        matrix = FoodMatrix('file')
        for i in range(3):
            _ = matrix.tags
        tags_mock.find.assert_called_once_with()

    def test_whereis_method_avoid(self):
        assert_equal_tuples(
            ('avoid', 0),
            self.matrix_obj.whereis_elem('seaweed', {
                'avoid': ['seaweed'],
                'minimize': {'potato': 2},
                'prior': {'spinach': 0},
            })
        )

    def test_whereis_method_prioritize(self):
        assert_equal_tuples(
            ('minimize', -1),
            self.matrix_obj.whereis_elem('potato', {
                'avoid': ['seaweed'],
                'minimize': {'potato': 2},
                'prior': {'spinach': 0},
            })
        )

    def test_remove_element(self):
        assert_equal_objects(
            self.matrix_obj.remove_element('potato', {
                'avoid': ['seaweed'],
                'minimize': {'potato': 2},
                'prior': {'spinach': 0},
            }), {
                'avoid': ['seaweed'],
                'minimize': {},
                'prior': {'spinach': 0},
            }
        )

    def test_str_to_list_1(self):
        with pytest.raises(FoodMatrixException):
            self.matrix_obj.str_to_list(['a', '', ''])

    def test_str_to_list_2(self):
        with pytest.raises(FoodMatrixException):
            self.matrix_obj.str_to_list(['', ''])

    def test_str_to_list_3(self):
        with pytest.raises(FoodMatrixException):
            self.matrix_obj.str_to_list([None, ''])

    def test_change_status_method_1(self):
        record = {
            'name': 'breast',
            'type': 'cancer',
            'avoid': ['mackerel', 'seaweed'],
            'minimize': ['potato'],
            'prior': [],
        }
        assert self.matrix_obj.changed_status(record, 'mackerel', 'P')

    def test_change_status_method_2(self):
        record = {
            'name': 'breast',
            'type': 'cancer',
            'avoid': ['mackerel', 'seaweed'],
            'minimize': ['potato'],
            'prior': [],
        }
        assert not self.matrix_obj.changed_status(record, 'mackerel', 'A')

    def test_change_status_method_3(self):
        """Record does not exists. Tag is new"""
        assert not self.matrix_obj.changed_status({}, 'mackerel', 'A')

    def test_is_quantity_value_case_1(self):
        m = self.matrix_obj.quantity_value('M-20')
        assert m
        assert m.groupdict().get('list') == 'M'
        assert m.groupdict().get('quantity') == '20'

    def test_is_quantity_value_case_2(self):
        m = self.matrix_obj.quantity_value('50|20')
        assert m is None

    def test_is_quantity_value_case_3(self):
        m = self.matrix_obj.quantity_value('M-10|20')
        assert m
        assert m.groupdict().get('list') == 'M'
        assert m.groupdict().get('min1') == '10'
        assert m.groupdict().get('min2') == '20'

    def test_is_quantity_value_case_4(self):
        assert not self.matrix_obj.quantity_value('M-|20')

    def test_is_quantity_value_case_5(self):
        assert not self.matrix_obj.quantity_value('M-|20')

    def test_update_content_existing_tag(self, content_iterator, tags_mock):
        content_iterator.return_value = [
            'type,name,mackerel,seaweed,potato,spinach',
            '',
            'inflammation,symptoms,R,A,M,P',
        ]
        tags_mock.find.return_value = [{
            'name': 'inflammation',
            'type': 'symptoms',
            'avoid': ['mackerel', 'seaweed'],
            'minimize': {'potato': 0},
            'prior': {},
            }
        ]
        assert_equal_tuples(([{
            'name': 'inflammation',
            'type': 'symptoms',
            'avoid': ['seaweed'],
            'minimize': {'potato': 0},
            'prior': {'spinach': 0},
            }], {}),
            self.matrix_obj.updated_content()
        )

    def _test_update_content_new_tag(self, content_iterator, tags_mock):
        content_iterator.return_value = [
            'type,name,mackerel,seaweed,potato,spinach',
            '',
            'inflammation,symptoms,R,A,M,P',
        ]
        tags_mock.find.return_value = []
        assert_equal_tuples(([{
            'name': 'inflammation',
            'type': 'symptoms',
            'avoid': ['seaweed'],
            'minimize': {'potato': 0},
            'prior': {'spinach': 0},
            }], {}),
            self.matrix_obj.updated_content()
        )


@pytest.mark.skip('')
@pytest.mark.usefixtures('file_opening', 'headers_mock')
class TestCaseUpdateContentRow(object):

    @property
    def matrix_obj(self):
        return FoodMatrix('fname')

    def test_updated_row_1(self):
        assert_equal_tuples(({
            'name': 'breast',
            'type': 'cancer',
            'avoid': ['seaweed'],
            'minimize': {'potato': 0},
            'prior': {'spinach': 0},
            }, {}),
            self.matrix_obj.updated_row(
                ['breast', 'cancer', 'R', 'A', 'M', 'P'], {
                    'name': 'breast',
                    'type': 'cancer',
                    'avoid': ['mackerel', 'seaweed'],
                    'minimize': {'potato': 0},
                    'prior': {},
                }, 1
            )
        )

    def test_updated_row_2(self):
        assert_equal_tuples(({
            'name': 'breast',
            'type': 'cancer',
            'avoid': ['mackerel'],
            'minimize': {'potato': 0},
            'prior': {'seaweed': 0},
            }, {}),
            self.matrix_obj.updated_row(
                ['breast', 'cancer', '', 'P', '', ''], {
                    'name': 'breast',
                    'type': 'cancer',
                    'avoid': ['mackerel', 'seaweed'],
                    'minimize': {'potato': 0},
                    'prior': {},
                }, 1
            )
        )

    def test_updated_row_3(self):
        assert_equal_tuples(
            self.matrix_obj.updated_row(
                ['breast', 'cancer', '', 'P', '', '300.42'],
                {
                    'name': 'breast',
                    'type': 'cancer',
                    'avoid': ['mackerel', 'seaweed'],
                    'minimize': {'potato': 2},
                    'prior': {'spinach': 0},
                }, 1), (
                {
                    'name': 'breast',
                    'type': 'cancer',
                    'avoid': ['mackerel'],
                    'minimize': {'potato': 2},
                    'prior': {'spinach': 300.42, 'seaweed': 0}
                }, {}
            )
        )

    def test_updated_row_4(self):
        """Verify lower/upper range values are correctly parsed"""
        assert_equal_tuples(({
            'name': 'breast',
            'type': 'cancer',
            'avoid': ['mackerel'],
            'minimize': {'potato': 2},
            'prior': {'spinach': {'min1': 600.0, 'min2': 700.0}, 'seaweed': 0},
            }, {}),
            self.matrix_obj.updated_row(
                ['breast', 'cancer', '', 'P', '', '600|700', '20'], {
                    'name': 'breast',
                    'type': 'cancer',
                    'avoid': ['mackerel', 'seaweed'],
                    'minimize': {'potato': 2},
                    'prior': {'spinach': 0},
                }, 1
            )
        )

    def test_updated_row_5(self):
        assert_equal_tuples(({
            'name': 'breast',
            'type': 'cancer',
            'avoid': ['mackerel'],
            'minimize': {'potato': 2},
            'prior': {'spinach': 0, 'seaweed': 0},
            }, {"spinach": "Invalid value 300| @cell: 1:5"}),
            self.matrix_obj.updated_row(
                ['breast', 'cancer', '', 'P', '', '300|'], {
                    'name': 'breast',
                    'type': 'cancer',
                    'avoid': ['mackerel', 'seaweed'],
                    'minimize': {'potato': 2},
                    'prior': {'spinach': 0},
                }, 1
            )
        )

    def test_updated_row_6(self):
        assert_equal_tuples(
            self.matrix_obj.updated_row(
                ['breast', 'cancer', '20', 'P', '', ''], {
                    'name': 'breast',
                    'type': 'cancer',
                    'avoid': ['mackerel', 'seaweed'],
                    'minimize': {'potato': 2},
                    'prior': {'spinach': 0},
                }, 1
            ), ({
                'name': 'breast',
                'type': 'cancer',
                'avoid': ['mackerel'],
                'minimize': {'potato': 2},
                'prior': {'spinach': 0, 'seaweed': 0},
            }, {"mackerel": "Cannot assign a quantity value to mackerel "
                            "because is in the avoid list: 1:2"})
        )


@pytest.mark.usefixtures("file_opening")
class TestCaseTagFile(object):
    pass


@pytest.mark.skip('')
@pytest.mark.usefixtures('file_opening', 'headers_mock')
class TestCaseNewContentRow(object):

    @property
    def matrix_obj(self):
        return FoodMatrix('fname')

    def test_new_record_1(self):
        assert_equal_tuples(
            self.matrix_obj.new_record(
                ['breast', 'cancer', 'A-20', 'P', '30', ''], 1
            ), ({
                'name': 'breast',
                'type': 'cancer',
                'avoid': [],
                'minimize': {},
                'prior': {'seaweed': 0},
            }, {'mackerel': 'Invalid value @cell 1:2',
                'potato': 'Invalid value @cell 1:4'})
        )

    def test_new_record_2(self):
        assert_equal_tuples(
            self.matrix_obj.new_record(
                ['breast', 'cancer', 'M-20', 'P', 'R', ''], 1
            ), ({
                'name': 'breast',
                'type': 'cancer',
                'avoid': [],
                'minimize': {'mackerel': 20.0},
                'prior': {'seaweed': 0},
            }, {'potato': 'Invalid value @cell 1:4'})
        )

    def test_new_record_3(self):
        assert_equal_tuples(
            self.matrix_obj.new_record(
                ['breast', 'cancer', 'M-30|300', 'P', 'A', 'M'], 1
            ), ({
                'name': 'breast',
                'type': 'cancer',
                'avoid': ['potato'],
                'minimize': {'mackerel': {'min1': 30.0, 'min2': 300.0}, 'spinach': 0},
                'prior': {'seaweed': 0},
            }, {})
        )

    def test_new_record_4(self):
        assert_equal_tuples(
            self.matrix_obj.new_record(
                ['breast', 'cancer', 'M-30|300', 'P', 'A', 'M', 'R'], 1
            ), ({
                'name': 'breast',
                'type': 'cancer',
                'avoid': ['potato'],
                'minimize': {'mackerel': {'min1': 30.0, 'min2': 300.0}, 'spinach': 0},
                'prior': {'seaweed': 0},
            }, {})
        )
