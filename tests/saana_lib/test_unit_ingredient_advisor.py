import pytest

from tests.conftest import assert_equal_objects
from saana_lib.ingredient_advisor import IngredientAdvisor


@pytest.fixture
def tags_find_patch(mocker):
    tags_mock = mocker.patch(
        'saana_lib.connectMongo.db.tags'
    )
    tags_mock.find.return_value = [{
        '_id': 'b09779e',
        'minimize': {},
        'name': 'hypertension',
        'avoid': [],
        'prior': {},
        'type': 'comorbitities',
        },{
        '_id': '5cab57647',
        'minimize': {},
        'name': 'dry mouth',
        'avoid': [],
        'prior': {},
        'type': 'symptoms',
    }]
    return tags_mock


class TestCaseIngredientAdvisor(object):

    def test_advisor_tags_method_1(self, tags_find_patch):
        tags = IngredientAdvisor().tags
        assert len(tags) == 2
        assert_equal_objects(list(tags.keys()), ['b09779e', '5cab57647'])
        assert_equal_objects(
            list(tags['5cab57647'].keys()),
            ['avoid', 'prioritize', 'minimize', 'category', 'name']
        )
        tags_find_patch.find.assert_called_once_with()

    def test_tags_query_executed_only_once(self, tags_find_patch):
        """assert that the query is executed only once"""
        obj = IngredientAdvisor()
        for i in range(3):
            x = obj.tags
        tags_find_patch.find.assert_called_once_with()

    def test_read_patient_comorbidities(self, mocker):
        patient_com_mock = mocker.patch(
            'saana_lib.connectMongo.db.patient_comorbidities'
        )
        patient_com_mock.find.return_value = dict()
        IngredientAdvisor().patient_inputs('patient-id')
        patient_com_mock.find.assert_called_once_with(
            {'patient_id': 'patient-id'}
        )

    def test_read_patient_symptoms(self, mocker):
        patient_symptoms_mock = mocker.patch(
            'saana_lib.connectMongo.db.patient_symptoms'
        )
        patient_symptoms_mock.find.return_value = dict()
        IngredientAdvisor().patient_inputs('patient-id')
        patient_symptoms_mock.find.assert_called_once_with(
            {'patient_id': 'patient-id'}
        )

    def test_read_patient_diseases(self, mocker):
        patient_diseases_mock = mocker.patch(
            'saana_lib.connectMongo.db.patient_diseases'
        )
        patient_diseases_mock.find.return_value = dict()
        IngredientAdvisor().patient_inputs('patient-id')
        patient_diseases_mock.find.assert_called_once_with(
            {'patient_id': 'patient-id'}
        )

    def test_patient_inputs_list_filled(self, mocker):
        patient_com_mock = mocker.patch(
            'saana_lib.connectMongo.db.patient_comorbidities'
        )
        patient_com_mock.find.return_value = [{'comorbidity_id': '5d834692'}]
        patient_symptoms_mock = mocker.patch(
            'saana_lib.connectMongo.db.patient_symptoms'
        )
        patient_symptoms_mock.find.return_value = [{'symptom_id': '9303fc6a'}]
        patient_diseases_mock = mocker.patch(
            'saana_lib.connectMongo.db.patient_diseases'
        )
        patient_diseases_mock.find.return_value = [{'disease_id': '4a302ff4'}]
        assert_equal_objects(
            IngredientAdvisor().patient_inputs('pid'),
            ['5d834692', '9303fc6a', '4a302ff4']
        )

    def test_ingredients_advice_1(self, mocker):
        """assert on method/property calls. Execution does not
        enters the loop
        """
        tags_mock = mocker.patch(
            'saana_lib.ingredient_advisor.IngredientAdvisor.tags',
            new_callable=mocker.PropertyMock
        )
        patient_inputs_mock = mocker.patch(
            'saana_lib.ingredient_advisor.IngredientAdvisor.patient_inputs',
            return_value=list()
        )
        IngredientAdvisor().ingredients_advice('patient-id')

        patient_inputs_mock.assert_called_once_with('patient-id')
        assert not tags_mock.called
        assert len(tags_mock.mock_calls) == 0

    def test_ingredients_advice_2(self, mocker):
        """assert on method/property calls. One loop iteration
        is performed
        """
        tags_mock = mocker.patch(
            'saana_lib.ingredient_advisor.IngredientAdvisor.tags',
            new_callable=mocker.PropertyMock
        )
        tags_mock.return_value = dict()
        patient_inputs_mock = mocker.patch(
            'saana_lib.ingredient_advisor.IngredientAdvisor.patient_inputs',
            return_value=[1]
        )
        patient_info_mock = mocker.patch(
            'saana_lib.ingredient_advisor.IngredientAdvisor.patient_info',
            return_value={'first_name': 'Donald', 'last_name': 'trump'}
        )
        IngredientAdvisor().ingredients_advice('patient-id')

        patient_inputs_mock.assert_called_once_with('patient-id')
        assert tags_mock.called
        assert len(tags_mock.mock_calls) == 1
        patient_info_mock.assert_called_once_with('patient-id')

    def test_ingredients_advice_3(self, mocker):
        """assert on result"""
        tags_mock = mocker.patch(
            'saana_lib.ingredient_advisor.IngredientAdvisor.tags',
            new_callable=mocker.PropertyMock
        )
        tags_mock.return_value = {'hypertension': {
            'minimize': {'sodium': {}},
            'name': 'hypertension',
            'avoid': ['beets'],
            'prioritize': {'carrot': 0}
        }}
        patient_inputs_mock = mocker.patch(
            'saana_lib.ingredient_advisor.IngredientAdvisor.patient_inputs',
            return_value=['hypertension']
        )
        patient_info_mock = mocker.patch(
            'saana_lib.ingredient_advisor.IngredientAdvisor.patient_info',
            return_value=('Donald', 'Trump')
        )

        assert_equal_objects(
            IngredientAdvisor().ingredients_advice('patient-id'), {
                'minimize': ['sodium'],
                'avoid': ['beets'],
                'prioritize': ['carrot'],
                'patient': 'Donald Trump'
            }
        )
        patient_inputs_mock.assert_called_once_with('patient-id')
        patient_info_mock.assert_called_once_with('patient-id')

    def test_patient_info_1(self, mocker):
        """patient is not found. User query is not performed"""
        patients_mock = mocker.patch('saana_lib.connectMongo.db.patients')
        patients_mock.find_one.return_value = None
        users_mock = mocker.patch('saana_lib.connectMongo.db.users')

        IngredientAdvisor().patient_info('patient-id')
        patients_mock.find_one.assert_called_once_with({'_id': 'patient-id'})
        users_mock.find_one.assert_not_called()

    def test_patient_info_2(self, mocker):
        """patient exists, user query is performed"""
        patients_mock = mocker.patch('saana_lib.connectMongo.db.patients')
        patients_mock.find_one.return_value = {'user_id': 'f06d420'}
        users_mock = mocker.patch('saana_lib.connectMongo.db.users')

        IngredientAdvisor().patient_info('patient-id')
        patients_mock.find_one.assert_called_once_with({'_id': 'patient-id'})
        users_mock.find_one.assert_called_once_with({'_id': 'f06d420'})

    def test_patient_info_3(self, mocker):
        """a user is found, the expected tuple is returned"""
        patients_mock = mocker.patch('saana_lib.connectMongo.db.patients')
        patients_mock.find_one.return_value = {'user_id': 'f06d420'}
        users_mock = mocker.patch('saana_lib.connectMongo.db.users')
        users_mock.find_one.return_value = {
            'first_name': 'donald',
            'last_name': 'trump'
        }
        assert_equal_objects(
            IngredientAdvisor().patient_info('patient-id'), ('donald', 'trump')
        )

    def test_patient_info_4(self, mocker):
        """user is not found. default tuple is returned"""
        patients_mock = mocker.patch('saana_lib.connectMongo.db.patients')
        patients_mock.find_one.return_value = {'user_id': 'f06d420'}
        users_mock = mocker.patch('saana_lib.connectMongo.db.users')
        users_mock.find_one.return_value = None
        assert_equal_objects(
            IngredientAdvisor().patient_info('patient-id'), ('', '')
        )

