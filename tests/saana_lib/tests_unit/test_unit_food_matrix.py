import pytest

from saana_lib.process.processFoodMatrix import FoodMatrix, FoodMatrixException
from tests.conftest import assert_equal_objects, assert_equal_tuples


@pytest.fixture(name='file_mocker')
def file_opening(mocker):
    fopen_mock = mocker.patch('builtins.open')
    return fopen_mock


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


@pytest.mark.usefixtures("file_mocker")
class TestCaseFoodMatrix(object):

    @property
    def matrix_obj(self):
        return FoodMatrix('fname')

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

    def test_file_opening(self, file_mocker):
        self.matrix_obj.load_file()
        assert file_mocker.call_count == 1
        file_mocker.assert_called_once_with('fname', 'r')

    def test_file_does_not_exists(self, file_mocker):
        file_mocker.side_effect = IsADirectoryError
        with pytest.raises(FoodMatrixException):
            self.matrix_obj.load_file()

    def test_iterator_is_loaded_once(self, mocker, file_mocker):
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

        csv_mock.assert_called_once_with(file_mocker())

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


@pytest.mark.usefixtures('file_mocker', 'headers_mock')
class TestCaseUpdateContentRow(object):

    @property
    def matrix_obj(self):
        return FoodMatrix('fname')

    def test_updated_content_row_1(self):
        assert_equal_tuples(({
            'name': 'breast',
            'type': 'cancer',
            'avoid': ['seaweed'],
            'minimize': {'potato': 0},
            'prior': {'spinach': 0},
            }, {}),
            self.matrix_obj.updated_content_row(
                ['breast', 'cancer', 'R', 'A', 'M', 'P'], {
                    'name': 'breast',
                    'type': 'cancer',
                    'avoid': ['mackerel', 'seaweed'],
                    'minimize': {'potato': 0},
                    'prior': {},
                }, 1
            )
        )

    def test_updated_content_row_2(self):
        assert_equal_tuples(({
            'name': 'breast',
            'type': 'cancer',
            'avoid': ['mackerel'],
            'minimize': {'potato': 0},
            'prior': {'seaweed': 0},
            }, {}),
            self.matrix_obj.updated_content_row(
                ['breast', 'cancer', '', 'P', '', ''], {
                    'name': 'breast',
                    'type': 'cancer',
                    'avoid': ['mackerel', 'seaweed'],
                    'minimize': {'potato': 0},
                    'prior': {},
                }, 1
            )
        )

    def test_updated_content_row_3(self):
        assert_equal_tuples(
            self.matrix_obj.updated_content_row(
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

    def test_updated_content_row_4(self):
        """Verify lower/upper range values are correctly parsed"""
        assert_equal_tuples(({
            'name': 'breast',
            'type': 'cancer',
            'avoid': ['mackerel'],
            'minimize': {'potato': 2},
            'prior': {'spinach': {'min1': 600.0, 'min2': 700.0}, 'seaweed': 0},
            }, {}),
            self.matrix_obj.updated_content_row(
                ['breast', 'cancer', '', 'P', '', '600|700'], {
                    'name': 'breast',
                    'type': 'cancer',
                    'avoid': ['mackerel', 'seaweed'],
                    'minimize': {'potato': 2},
                    'prior': {'spinach': 0},
                }, 1
            )
        )

    def test_updated_content_row_5(self):
        assert_equal_tuples(({
            'name': 'breast',
            'type': 'cancer',
            'avoid': ['mackerel'],
            'minimize': {'potato': 2},
            'prior': {'spinach': 0, 'seaweed': 0},
            }, {"spinach": "Invalid value 300| for cell: 1:5"}),
            self.matrix_obj.updated_content_row(
                ['breast', 'cancer', '', 'P', '', '300|'], {
                    'name': 'breast',
                    'type': 'cancer',
                    'avoid': ['mackerel', 'seaweed'],
                    'minimize': {'potato': 2},
                    'prior': {'spinach': 0},
                }, 1
            )
        )

    def test_updated_content_row_6(self):
        assert_equal_tuples(
            self.matrix_obj.updated_content_row(
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

    def _test_updated_content_row_7(self):
        """Record is None, because tags has to be created"""
        assert_equal_tuples(
            self.matrix_obj.updated_content_row(
                ['breast', 'cancer', '20', 'P', '', ''], None, 1
            ), ({
                'name': 'breast',
                'type': 'cancer',
                'avoid': ['mackerel'],
                'minimize': {'potato': 2},
                'prior': {'spinach': 0, 'seaweed': 0},
            }, {})
        )
