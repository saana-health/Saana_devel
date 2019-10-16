import pytest

from tests.conftest import assert_equal_objects
from saana_lib.process.processFoodMatrix import FoodMatrix, FoodMatrixException


@pytest.fixture
def content_iterator_mock(mocker):
    iterator = mocker.patch(
        'saana_lib.process.processFoodMatrix.FoodMatrix.content_iterator',
        new_callable=mocker.PropertyMock,
    )
    return iterator


def test_record_is_modified(integration_setup, content_iterator_mock):
    headers = 'type,name,saury fish,fish,cabbage,pak choi,komatsuna'
    content_iterator_mock.return_value = [headers, '', 'diarrhea,symptoms,,M,,,']
    test_db = integration_setup

    matrix = FoodMatrix('')
    updated_counter = matrix.update()
    assert updated_counter == (1, {})
    diarrhea = test_db.tags.find_one({'name': 'diarrhea'})
    assert_equal_objects(
        diarrhea['minimize'],
        {'insoluble fiber': {
            'min2': '15',
            'min1': '10'
        }, 'fish': 0}
    )


def test_one_update_one_upsert(integration_setup, content_iterator_mock):
    headers = 'type,name,saury fish,fish,cabbage,pak choi,komatsuna'
    content_iterator_mock.return_value = [
        headers,
        '',
        'diarrhea,symptoms,,M,,,',
        'breast,cancer,A,A,A,P-20,P-40|500',
    ]
    test_db = integration_setup

    matrix = FoodMatrix('')
    updated_counter = matrix.update()

    assert updated_counter == (2, {})
    breast_cancer = test_db.tags.find_one({'name': 'breast', 'type': 'cancer'})
    assert_equal_objects(
        breast_cancer['avoid'],
        ['saury fish', 'fish', 'cabbage']
    )
    assert_equal_objects(
        breast_cancer['prior'],
        {'pak choi': 20.0, 'komatsuna': {'min1': 40.0, 'min2': 500.0}}
    )


