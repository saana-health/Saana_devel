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

    def test_load_tags(self, mocker):
        from tests.conftest import TagsCollectionMock, connectMongo, assert_equal_objects
        mocker.patch.object(connectMongo.db, 'tags', TagsCollectionMock())
        tags = self.matrix_obj.load_tags()
        assert_equal_objects(tags.keys(), {'inflammation': None, 'diarrhea': None}.keys())

    def test_tags_are_loaded_from_db(self, mocker):
        load_tags_mock = mocker.patch(
            'saana_lib.process.processFoodMatrix.FoodMatrix.load_tags',
        )
        mocker.patch(
            'saana_lib.process.processFoodMatrix.FoodMatrix.column_headers',
        )
        self.matrix_obj.read_rows()
        assert load_tags_mock.call_count == 1

    def test_parse_elements_row_1(self):
        with pytest.raises(FoodMatrixException):
            self.matrix_obj.parse_elements_row(['a', '', ''])

    def test_parse_elements_row_2(self):
        with pytest.raises(FoodMatrixException):
            self.matrix_obj.parse_elements_row(['', ''])

    def test_parse_elements_row_3(self):
        with pytest.raises(FoodMatrixException):
            self.matrix_obj.parse_elements_row([None, ''])

    def test_str_to_list(self):
        assert self.matrix_obj.str_to_list(None) == []

    def test_row_processed_1(self):
        row = ['cancer', 'breast', 'P', '', 'A', 'M']
        assert_equal_tuples(
            self.matrix_obj.row_processed(row),
            ([(0, 'P'), (2, 'A'), (3, 'M')], {})
        )

    def test_row_processed_2(self):
        row = ['cancer', 'breast', 'T', '', 'A', 'M']
        assert_equal_tuples(
            self.matrix_obj.row_processed(row),
            ([(2, 'A'), (3, 'M')], {0: 'invalid option T'})
        )



"""
        current_element = {
            'name': 'breast',
            'type': 'cancer',
            'avoid': ['mackerel', 'saury fish', 'seaweed'],
            'prior': ['green beans'],
            'minimize': ['"Peppers, Hot"', 'Potato', 'Sweet Potato'],
            'tag_id': None
        }

"""


