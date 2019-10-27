import pytest

from pymongo.collection import ObjectId

from tests.conftest import assert_equal_objects
from saana_lib.patient import Patient, PatientDisease, PatientComorbidity, \
    PatientDrug, PatientSymptom, PatientOtherRestrictions, MinimizeIngredients, \
    AvoidIngredients, PrioritizeIngredients, IngredientFilter


def obj_id():
    return ObjectId('5d7258c977f06d4208211eb4')


class TestCasePatient:

    def test_patient_read_method(self):
        with pytest.raises(NotImplementedError):
            _ = Patient('5d7258c977f06d4208211eb4').read()

    def test_patient_read_as_list_method(self):
        with pytest.raises(NotImplementedError):
            _ = Patient('5d7258c977f06d4208211eb4').read_as_list()

    def test_patient_read_as_tags_method(self):
        with pytest.raises(NotImplementedError):
            _ = Patient('5d7258c977f06d4208211eb4').read_as_tags()


def test_patient_diseases(mocker):
    met = mocker.patch('saana_lib.connectMongo.db.patient_diseases')
    _ = PatientDisease('5d7258c977f06d4208211eb4').read_as_tags()
    met.find.assert_called_once_with({'patient_id': obj_id()})


def test_patient_comorbidities(mocker):
    met = mocker.patch('saana_lib.connectMongo.db.patient_comorbidities')
    _ = PatientComorbidity('5d7258c977f06d4208211eb4').read_as_tags()
    met.find.assert_called_once_with({'patient_id': obj_id()})


def test_patient_drugs(mocker):
    met = mocker.patch('saana_lib.connectMongo.db.patient_drugs')
    _ = PatientDrug('5d7258c977f06d4208211eb4').read_as_tags()
    met.find.assert_called_once_with({'patient_id': obj_id()})


def test_patient_symptom(mocker):
    met = mocker.patch('saana_lib.connectMongo.db.patient_symptoms')
    _ = PatientSymptom('5d7258c977f06d4208211eb4').read_as_tags()
    met.find.assert_called_once_with({'patient_id': obj_id()})


class TestCaseTagsValues(object):
    """
    These tests have two goals. One is to verify that for each
    case the proper key is called (disease_id, drug_id, ...)
    the other is to verify that a mst_tags object is returned,
    but instead of asserting over the values itself, I check
    that the correct collection is queried (behavior test)
    """
    obj_id = '5d7258c977f06d4208211eb4'


    @pytest.fixture
    def mst_tags_mock(self, mocker):
        return mocker.patch('saana_lib.connectMongo.db.mst_tags')

    def test_patient_disease_values(self, mocker, mst_tags_mock):
        met = mocker.patch('saana_lib.connectMongo.db.patient_diseases')
        met.find.return_value = [{'disease_id': 'tag_id'},]
        _ = PatientDisease('5d7258c977f06d4208211eb4').read_as_tags()
        met.find.assert_called_once_with({'patient_id': obj_id()})
        mst_tags_mock.find.assert_called_once_with({'_id': {'$in': ['tag_id']}})

    def test_patient_comorbidity_values(self, mocker, mst_tags_mock):
        met = mocker.patch('saana_lib.connectMongo.db.patient_comorbidities')
        met.find.return_value = [{'comorbidity_id': 'tag_id'}, ]
        _ = PatientComorbidity('5d7258c977f06d4208211eb4').read_as_tags()
        met.find.assert_called_once_with({'patient_id': obj_id()})
        mst_tags_mock.find.assert_called_once_with({'_id': {'$in': ['tag_id']}})

    def test_patient_drug_values(self, mocker, mst_tags_mock):
        met = mocker.patch('saana_lib.connectMongo.db.patient_drugs')
        met.find.return_value = [{'drug_id': 'tag_id'}, ]
        _ = PatientDrug('5d7258c977f06d4208211eb4').read_as_tags()
        met.find.assert_called_once_with({'patient_id': obj_id()})
        mst_tags_mock.find.assert_called_once_with({'_id': {'$in': ['tag_id']}})

    def test_patient_symptom_values(self, mocker, mst_tags_mock):
        met = mocker.patch('saana_lib.connectMongo.db.patient_symptoms')
        met.find.return_value = [{'symptom_id': 'tag_id'}, ]
        _ = PatientSymptom('5d7258c977f06d4208211eb4').read_as_tags()
        met.find.assert_called_once_with({'patient_id': obj_id()})
        mst_tags_mock.find.assert_called_once_with({'_id': {'$in': ['tag_id']}})


def test_patient_other_restrictions(mocker):
    met = mocker.patch('saana_lib.connectMongo.db.patient_other_restrictions')
    _ = PatientOtherRestrictions('5d7258c977f06d4208211eb4').read_as_tags()
    met.find_one.assert_called_once_with({'patient_id': obj_id()})


def test_patient_other_restriction_empty(mocker):
    db_mock = mocker.patch(
        'saana_lib.connectMongo.db.patient_other_restrictions',
    )
    db_mock.find_one.return_value = {'other_restriction': ''}

    assert PatientOtherRestrictions('5d7258c977f06d4208211eb4').read_as_list() == []


def test_patient_other_restriction_not_empty(mocker):
    db_mock = mocker.patch(
        'saana_lib.connectMongo.db.patient_other_restrictions',
    )
    db_mock.find_one.return_value = {'other_restriction': 'Less sugar,more red meat'}

    assert_equal_objects(
        PatientOtherRestrictions('5d7258c977f06d4208211eb4').read_as_list(),
        ['less', 'sugar', 'more', 'red', 'meat']
    )


class TestCaseAvoidIngredient(object):

    def test_avoid_ingredient(self, mocker):
        all_tags = mocker.patch(
            'saana_lib.patient.PatientTags.all_tags',
            new_callable=mocker.PropertyMock,
            return_value=[
                {'avoid': ["broccoli", "flax"]},
                {'avoid': ["kale", "onion", "flax"]}
            ]
        )

        mocker.patch(
            'saana_lib.patient.PatientOtherRestrictions.read',
            return_value=list()
        )

        assert_equal_objects(
            AvoidIngredients(obj_id()).all,
            {"broccoli", "flax", "kale", "onion"}
        )
        all_tags.assert_called_once_with()

    def test_avoid_and_other_restrictions_behavior(self, mocker):
        all_tags = mocker.patch(
            'saana_lib.patient.PatientTags.all_tags',
            new_callable=mocker.PropertyMock,
            return_value=[
                {'avoid': ["broccoli", "flax"]},
                {'avoid': ["onion", "flax"]}
            ]
        )

        restrictions = mocker.patch(
            'saana_lib.patient.PatientOtherRestrictions.read',
            return_value=list()
        )

        _ = AvoidIngredients(obj_id()).all

        all_tags.assert_called_once_with()
        restrictions.assert_called_once_with()

    def test_avoid_and_other_restrictions_values(self, mocker):
        all_tags = mocker.patch(
            'saana_lib.patient.PatientTags.all_tags',
            new_callable=mocker.PropertyMock,
            return_value=[
                {'avoid': ["broccoli", "flax"]},
                {'avoid': ["onion", "flax"]}
            ]
        )

        restrictions = mocker.patch(
            'saana_lib.patient.PatientOtherRestrictions.read',
            return_value=['kale']
        )

        assert_equal_objects(
            AvoidIngredients(obj_id()).all,
            {"broccoli", "flax", "kale", "onion"}
        )

        all_tags.assert_called_once_with()
        restrictions.assert_called_once_with()

    def test_ingredient_exists(self, mocker):
        """Verify that plurals cases return True"""
        met = mocker.patch(
            'saana_lib.patient.db.mst_food_ingredients'
        )
        met.find.return_value = [{'name': 'peppers'}, {'name': 'soy'}]
        assert AvoidIngredients(obj_id()).ingredient_exists('peppers')

    def test_ingredient_does_not_exists(self, mocker):
        """Mixed ingredient may match if the the ingredient match
        the whole word
        """
        met = mocker.patch(
            'saana_lib.patient.db.mst_food_ingredients'
        )
        met.find.return_value = [{'name': 'peppers'}, {'name': 'soy'}]
        assert AvoidIngredients(obj_id()).ingredient_exists('hot peppers')


def test_prioritize_ingredients(mocker):
    all_tags = mocker.patch(
        'saana_lib.patient.PatientTags.all_tags',
        new_callable=mocker.PropertyMock,
        return_value=[{
            'prior': {
                "broccoli": 0,
                "flax": 21,
                }
            }, {
            'prior': {
                "kale": 0,
                "onion": 1,
                "flax": 2
                }
            }
        ]
    )

    mocker.patch(
        'saana_lib.patient.IngredientFilter.filter_prioritize',
        return_value={"broccoli": 0, "flax": 21, "kale": 0, "onion": 1}
    )
    assert_equal_objects(
        PrioritizeIngredients(obj_id()).all,
        {"broccoli": 0, "flax": 21, "kale": 0, "onion": 1}
    )
    all_tags.assert_called_once_with()


def test_minimize_ingredients(mocker):
    all_tags = mocker.patch(
        'saana_lib.patient.PatientTags.all_tags',
        new_callable=mocker.PropertyMock,
        return_value=[{'minimize': {}}]
    )
    mocker.patch(
        'saana_lib.patient.IngredientFilter.filter_minimize',
        return_value={}
    )

    assert_equal_objects(MinimizeIngredients(obj_id()).all, dict())
    all_tags.assert_called_once_with()


@pytest.fixture(name='minimize_all_tags_mock')
def minimize_ingredients_all_tags_mock(mocker):
    return mocker.patch(
        'saana_lib.patient.MinimizeIngredients.all_tags',
        new_callable=mocker.PropertyMock,
    )


@pytest.fixture(name='prioritize_all_tags_mock')
def prioritize_ingredients_all_tags_mock(mocker):
    return mocker.patch(
        'saana_lib.patient.PrioritizeIngredients.all_tags',
        new_callable=mocker.PropertyMock,
    )


@pytest.fixture(name='avoid_all_tags_mock')
def avoid_ingredients_all_tags_mock(mocker):
    mocker.patch(
        'saana_lib.patient.AvoidIngredients.other_restrictions',
        new_callable=mocker.PropertyMock,
        return_value=list()
    )

    return mocker.patch(
        'saana_lib.patient.AvoidIngredients.all_tags',
        new_callable=mocker.PropertyMock,
    )


class TestCaseIngredientsRepeatedExecution(object):
    """
    These test-case verify the all_tags property is run only
    once.
    """
    def test_minimize(self, minimize_all_tags_mock, mocker):
        mocker.patch(
            'saana_lib.patient.IngredientFilter.filter_minimize'
        )
        obj = MinimizeIngredients(obj_id())
        for i in range(3):
            _ = obj.all
        minimize_all_tags_mock.assert_called_once_with()

    def test_prioritize(self, prioritize_all_tags_mock, mocker):
        mocker.patch(
            'saana_lib.patient.IngredientFilter.filter_prioritize'
        )
        obj = PrioritizeIngredients(obj_id())
        for i in range(3):
            _ = obj.all
        prioritize_all_tags_mock.assert_called_once_with()

    def test_avoid(self, avoid_all_tags_mock):
        obj = AvoidIngredients(obj_id())
        for i in range(3):
            _ = obj.all
        avoid_all_tags_mock.assert_called_once_with()


class TestCaseIngredientFilter(object):

    def test_filter_prioritize_ingredient(self,
                                          prioritize_all_tags_mock,
                                          mocker):
        prioritize_all_tags_mock.return_value = [
            {'prior': {'soy': 0, 'flax': 2}}
        ]

        prioritize_filter_mock = mocker.patch(
            'saana_lib.patient.IngredientFilter.filter_prioritize'
        )

        _ = PrioritizeIngredients(obj_id()).all
        prioritize_filter_mock.assert_called_once_with(
            obj_id(), {'soy': 0, 'flax': 2}
        )

    def test_filter_minimize_ingredient(self,
                                        minimize_all_tags_mock,
                                        mocker):
        minimize_all_tags_mock.return_value = [
            {'minimize': {'soy': 0, 'flax': 2}}
        ]

        minimize_filter_mock = mocker.patch(
            'saana_lib.patient.IngredientFilter.filter_minimize'
        )

        _ = MinimizeIngredients(obj_id()).all
        minimize_filter_mock.assert_called_once_with(
            obj_id(), {'soy': 0, 'flax': 2}
        )

    def test_filter_prioritize_values_case_1(self, avoid_all_tags_mock):
        avoid_all_tags_mock.return_value = [{'avoid': ['soy', 'flax']}]

        assert_equal_objects(
            IngredientFilter.filter_prioritize(
                obj_id(), {'beets': 0, 'flax': 1, 'carrot': 2}
            ), {'beets': 0, 'carrot': 2}
        )

    def test_filter_prioritize_values_case_2(self,
                                             avoid_all_tags_mock,
                                             mocker):
        avoid_all_tags_mock.return_value = [{'avoid': ['soy', 'flax']}]

        mocker.patch(
            'saana_lib.patient.MinimizeIngredients.all',
            new_callable=mocker.PropertyMock,
            return_value={'carrot': 1}
        )


        assert_equal_objects(
            IngredientFilter.filter_prioritize(
                obj_id(), {'beets': 0, 'flax': 1, 'carrot': 2}
            ), {'beets': 0}
        )

    def test_filter_minimize_values_case_1(self, avoid_all_tags_mock):
        avoid_all_tags_mock.return_value = [{'avoid': ['soy', 'flax']}]

        assert_equal_objects(
            IngredientFilter.filter_minimize(
                obj_id(), {'soy': 0, 'flax': 1, 'carrot': 2}
            ), {'carrot': 2}
        )

