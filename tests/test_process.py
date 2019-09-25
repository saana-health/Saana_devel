import pytest

from saana_lib.process.processFoodMatrix import FoodMatrix, FoodMatrixException
from tests.conftest import assert_equal_objects, assert_equal_tuples


@pytest.fixture(name='file_mocker')
def file_opening(mocker):
    return mocker.patch('builtins.open')




@pytest.mark.usefixtures("file_mocker")
class TestCaseProcessMatrix(object):
    matrix_obj = FoodMatrix('fname')

    @pytest.fixture
    def content_iterator(self, mocker):
        m = mocker.patch(
            'saana_lib.process.processFoodMatrix.FoodMatrix.content_iterator',
        )
        return m

    @pytest.fixture
    def headers_mock(self, mocker):
        m = mocker.patch(
            'saana_lib.process.processFoodMatrix.FoodMatrix.column_headers',
            return_value=[
                'type', 'name', 'mackerel', 'seaweed', 'potato', 'spinach'
                ]
        )
        return m

    def test_file_opening(self, file_mocker):
        self.matrix_obj.load_file()
        assert file_mocker.call_count == 1
        file_mocker.assert_called_once_with('fname', 'r')

    def test_file_does_not_exists(self, file_mocker):
        file_mocker.side_effect = IsADirectoryError
        with pytest.raises(FoodMatrixException):
            self.matrix_obj.load_file()

    def test_iterator_is_loaded_once(self, file_mocker):
        file_mocker.return_value = list()
        assert self.matrix_obj.content_iterator == self.matrix_obj.content_iterator

    def test_read_empty_file(self, content_iterator):
        """Without columns"""
        content_iterator.return_value = list()
        with pytest.raises(FoodMatrixException):
            self.matrix_obj.column_headers()

    def test_file_contains_only_columns_names(self, content_iterator):
        headers = ['type', 'name', 'Oil', 'Butter', 'Onion', 'Parsley']
        content_iterator.return_value = [
            'type,name,Oil,Butter,Onion,Parsley',
        ]
        assert self.matrix_obj.column_headers() == headers

    def test_tags_property(self, mocker):
        from tests.conftest import TagsCollectionMock, connectMongo, assert_equal_objects
        mocker.patch.object(connectMongo.db, 'tags', TagsCollectionMock())
        assert_equal_objects(
            self.matrix_obj.tags.keys(), {
                ('inflammation', 'symptoms'): None,
                ('diarrhea', 'symptoms'): None}.keys()
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

    def test_updated_content_row_1(self, headers_mock):
        assert_equal_tuples(({
            'name': 'breast',
            'type': 'cancer',
            'avoid': ['seaweed'],
            'minimize': ['potato'],
            'prior': ['spinach'],
            }, {}),
            self.matrix_obj.updated_content_row(
                ['breast', 'cancer', 'R', 'A', 'M', 'P'], {
                    'name': 'breast',
                    'type': 'cancer',
                    'avoid': ['mackerel', 'seaweed'],
                    'minimize': ['potato'],
                    'prior': [],
                }
            )
        )
        assert headers_mock.call_count == 4

    def test_updated_content_row_2(self, headers_mock):
        assert_equal_tuples(({
            'name': 'breast',
            'type': 'cancer',
            'avoid': ['mackerel'],
            'minimize': ['potato'],
            'prior': ['seaweed'],
            }, {}),
            self.matrix_obj.updated_content_row(
                ['breast', 'cancer', '', 'P', '', ''], {
                    'name': 'breast',
                    'type': 'cancer',
                    'avoid': ['mackerel', 'seaweed'],
                    'minimize': ['potato'],
                    'prior': [],
                }
            )
        )
        assert headers_mock.call_count == 4

    def test_updated_content_row_3(self, headers_mock):
        assert_equal_tuples(({
            'name': 'breast',
            'type': 'cancer',
            'avoid': ['mackerel'],
            'minimize': ['potato'],
            'prior': [('spinach', 300), 'seaweed'],  # ,
            }, {}),
            self.matrix_obj.updated_content_row(
                ['breast', 'cancer', '', 'P', '', '300'], {
                    'name': 'breast',
                    'type': 'cancer',
                    'avoid': ['mackerel', 'seaweed'],
                    'minimize': ['potato'],
                    'prior': ['spinach'],
                }
            )
        )
        assert headers_mock.call_count == 4

    def test_updated_content_row_4(self, headers_mock):
        assert_equal_tuples(({
            'name': 'breast',
            'type': 'cancer',
            'avoid': ['mackerel'],
            'minimize': ['potato'],
            'prior': [('spinach', {'min1': 300, 'min2': 400}), 'seaweed'],
            }, {}),
            self.matrix_obj.updated_content_row(
                ['breast', 'cancer', '', 'P', '', '300|400'], {
                    'name': 'breast',
                    'type': 'cancer',
                    'avoid': ['mackerel', 'seaweed'],
                    'minimize': ['potato'],
                    'prior': ['spinach'],
                }
            )
        )
        assert headers_mock.call_count == 4

    def test_updated_content_row_5(self, headers_mock):
        assert_equal_tuples(({
            'name': 'breast',
            'type': 'cancer',
            'avoid': ['mackerel'],
            'minimize': ['potato'],
            'prior': ['spinach', 'seaweed'],
            }, {"spinach": "Invalid value: {}".format("300|")}),
            self.matrix_obj.updated_content_row(
                ['breast', 'cancer', '', 'P', '', '300|'], {
                    'name': 'breast',
                    'type': 'cancer',
                    'avoid': ['mackerel', 'seaweed'],
                    'minimize': ['potato'],
                    'prior': ['spinach'],
                }
            )
        )

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
        assert self.matrix_obj.changed_status(record, 'mackerel', 'A') == False

