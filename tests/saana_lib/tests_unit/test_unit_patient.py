import pytest

from datetime import datetime
from tests.conftest import assert_equal_objects, obj_id
from saana_lib.patient import Patient, PatientDisease, PatientComorbidity, \
    PatientDrug, PatientSymptom, PatientOtherRestrictions, MinimizeIngredients, \
    AvoidIngredients, PrioritizeIngredients, IngredientFilter, PatientSubscription, \
    SymptomsProgress, Nutrients


patient_id = obj_id


@pytest.fixture
def all_tags(mocker):
    return mocker.patch(
        'saana_lib.patient.PatientTags.all_tags',
        new_callable=mocker.PropertyMock,
        return_value=[
            {'avoid': ["broccoli", "flax"]},
            {'avoid': ["kale", "onion", "flax"]}
        ]
    )


@pytest.fixture
def other_restrictions(mocker):
    return mocker.patch(
        'saana_lib.patient.AvoidIngredients.other_restrictions',
        new_callable=mocker.PropertyMock,
        return_value=[]
    )


class TestCasePatient:
    """Verify that the proper exception is raised"""

    def test_patient_read_method(self):
        with pytest.raises(NotImplementedError):
            _ = Patient(patient_id()).read()

    def test_user_of_patient(self, mocker):
        user_collection = mocker.patch('saana_lib.patient.db.users')
        user_id_prop = mocker.patch('saana_lib.patient.Patient.user_id')
        _ = Patient(patient_id()).user_of_patient

        user_collection.find_one.assert_called_with({'_id': user_id_prop})

    def test_user_id(self, mocker):
        patients_collection = mocker.patch('saana_lib.patient.db.patients')
        _ = Patient(patient_id()).user_id

        patients_collection.find_one.assert_called_with({'_id': patient_id()})

    def test_user_not_found(self, mocker):
        from exceptions import UserNotFound

        mocker.patch('saana_lib.patient.db.patients')
        users = mocker.patch('saana_lib.patient.db.users')
        users.find_one.return_value = None

        with pytest.raises(UserNotFound):
            _ = Patient(patient_id()).user_of_patient

    def test_patient_not_found(self, mocker):
        from exceptions import PatientNotFound
        mocker.patch('saana_lib.patient.db.patients.find_one()', return_value=None)

        with pytest.raises(PatientNotFound):
            _ = Patient(patient_id()).patient_instance


class TestCaseReadAsTagsBehavior:
    """
    The next 4 tests verify that the proper db collections are queried
    """

    def test_patient_diseases(self, mocker):
        met = mocker.patch('saana_lib.connectMongo.db.patient_diseases')
        _ = PatientDisease(patient_id()).read_as_tags()

        met.find.assert_called_once_with({'patient_id': patient_id()})

    def test_patient_comorbidities(self, mocker):
        met = mocker.patch('saana_lib.connectMongo.db.patient_comorbidities')
        _ = PatientComorbidity(patient_id()).read_as_tags()

        met.find.assert_called_once_with({'patient_id': patient_id()})

    def test_patient_drugs(self, mocker):
        met = mocker.patch('saana_lib.connectMongo.db.patient_drugs')
        _ = PatientDrug(patient_id()).read_as_tags()

        met.find.assert_called_once_with({'patient_id': patient_id()})

    def test_patient_symptom(self, mocker):
        met = mocker.patch('saana_lib.connectMongo.db.patient_symptoms')
        _ = PatientSymptom(patient_id()).read_as_tags()

        met.find.assert_called_once_with({'patient_id': patient_id()})


class TestCaseReadAsTagsValues(object):
    """
    These tests have two goals. One is to verify that for each
    case the proper key is called (disease_id, drug_id, ...)
    the other is to verify that a mst_tags object is returned,
    but instead of asserting over the values itself, I check
    that the correct collection is queried (behavior test)
    """

    @pytest.fixture
    def tags_mock(self, mocker):
        return mocker.patch('saana_lib.connectMongo.db.tags')

    def test_patient_disease_values(self, mocker, tags_mock):
        met = mocker.patch('saana_lib.connectMongo.db.patient_diseases')
        met.find.return_value = [{'disease_id': 'er87g'},]

        _ = PatientDisease(patient_id()).read_as_tags()
        met.find.assert_called_once_with({'patient_id': patient_id()})
        tags_mock.find.assert_called_once_with({'tag_id': {'$in': ['er87g']}})

    def test_patient_comorbidity_values(self, mocker, tags_mock):
        met = mocker.patch('saana_lib.connectMongo.db.patient_comorbidities')
        met.find.return_value = [{'comorbidity_id': 'ry85t'}, ]

        _ = PatientComorbidity(patient_id()).read_as_tags()
        met.find.assert_called_once_with({'patient_id': patient_id()})
        tags_mock.find.assert_called_once_with({'tag_id': {'$in': ['ry85t']}})

    def test_patient_drug_values(self, mocker, tags_mock):
        met = mocker.patch('saana_lib.connectMongo.db.patient_drugs')
        met.find.return_value = [{'drug_id': 'ut64p'}, ]

        _ = PatientDrug(patient_id()).read_as_tags()
        met.find.assert_called_once_with({'patient_id': patient_id()})
        tags_mock.find.assert_called_once_with({'tag_id': {'$in': ['ut64p']}})

    def test_patient_symptom_values(self, mocker, tags_mock):
        met = mocker.patch('saana_lib.connectMongo.db.patient_symptoms')
        met.find.return_value = [{'symptom_id': 'tag_id'}, ]

        _ = PatientSymptom(patient_id()).read_as_tags()
        met.find.assert_called_once_with({'patient_id': patient_id()})
        tags_mock.find.assert_called_once_with({'tag_id': {'$in': ['tag_id']}})


class TestCaseOtherRestriction:
    """The first test verifies the behavior, the next two check
    the values being returned
    """
    @pytest.fixture
    def collection_mock(self, mocker):
        return mocker.patch('saana_lib.connectMongo.db.patient_other_restrictions')

    def test_patient_other_restrictions(self, collection_mock):
        _ = PatientOtherRestrictions(patient_id()).read_as_tags()
        collection_mock.find_one.assert_called_once_with({'patient_id': patient_id()})

    def test_patient_other_restriction_empty(self, collection_mock):
        collection_mock.find_one.return_value = {'other_restriction': ''}
        assert PatientOtherRestrictions(patient_id()).read_as_list() == []

    def test_patient_other_restriction_not_empty(self, collection_mock):
        collection_mock.find_one.return_value = {
            'other_restriction': 'Less sugar,more red meat'
        }

        assert_equal_objects(
            PatientOtherRestrictions(patient_id()).read_as_list(),
            ['less', 'sugar', 'more', 'red', 'meat']
        )


class TestCaseAvoidIngredient(object):

    def test_avoid_ingredient(self, all_tags, other_restrictions):
        assert_equal_objects(
            AvoidIngredients(patient_id()).all,
            {"broccoli", "flax", "kale", "onion"}
        )

    def test_avoid_and_other_restrictions_behavior(self, all_tags, other_restrictions):
        _ = AvoidIngredients(patient_id()).all
        all_tags.assert_called_once_with()
        other_restrictions.assert_called_once_with()

    def test_avoid_and_other_restrictions_values(self, all_tags, other_restrictions):
        other_restrictions.return_value = ['spinach']
        assert_equal_objects(
            AvoidIngredients(patient_id()).all,
            {"broccoli", "flax", "kale", "onion", "spinach"}
        )

    def test_ingredient_exists(self, mocker):
        """Verify that plurals cases return True"""
        met = mocker.patch(
            'saana_lib.patient.db.mst_food_ingredients'
        )
        met.find.return_value = [{'name': 'peppers'}, {'name': 'soy'}]

        assert AvoidIngredients(patient_id()).ingredient_exists('peppers')

    def test_ingredient_exists_tricky_case(self, mocker):
        """Mixed ingredient may match if the the ingredient name match
        the whole word. In this case is peppers.
        """
        met = mocker.patch(
            'saana_lib.patient.db.mst_food_ingredients'
        )
        met.find.return_value = [{'name': 'peppers'}, {'name': 'soy'}]

        assert AvoidIngredients(patient_id()).ingredient_exists('hot peppers')


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
    """This test shows that filter_minimize is not
    transparent in the process.
    """
    all_tags = mocker.patch(
        'saana_lib.patient.MinimizeIngredients.all_tags',
        new_callable=mocker.PropertyMock,
        return_value=[{'minimize': {'soy': 2, 'flax': 3, 'basil': 2}}]
    )
    mocker.patch(
        'saana_lib.patient.IngredientFilter.filter_minimize',
        return_value={}
    )

    assert_equal_objects(MinimizeIngredients(patient_id()).all, {})
    all_tags.assert_called_once_with()


def test_nutrients(mocker):
    all_tags = mocker.patch(
        'saana_lib.patient.Nutrients.all_tags',
        new_callable=mocker.PropertyMock,
        return_value=[{'nutrient': {1: 2, 3: 4}}]
    )

    nutrient_filter = mocker.patch(
        'saana_lib.patient.NutrientFilter.filter',
        return_value={}
    )
    _ = Nutrients(obj_id()).all
    all_tags.assert_called_once_with()
    nutrient_filter.assert_called_once_with(patient_id(), {1: 2, 3: 4})


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


@pytest.fixture(name='avoid_all_tags')
def avoid_ingredients_all_tags_mock(other_restrictions, mocker):
    return mocker.patch(
        'saana_lib.patient.AvoidIngredients.all_tags',
        new_callable=mocker.PropertyMock,
    )


class TestCaseIngredientsRepeatedExecution(object):
    """
    These test-case verify that despite multiple consecutive
    execution, `all_tags` property is only run once.
    """
    def test_minimize(self, minimize_all_tags_mock, mocker):
        mocker.patch('saana_lib.patient.IngredientFilter.filter_minimize')

        obj = MinimizeIngredients(patient_id())
        for i in range(3):
            _ = obj.all

        minimize_all_tags_mock.assert_called_once_with()

    def test_prioritize(self, prioritize_all_tags_mock, mocker):
        mocker.patch('saana_lib.patient.IngredientFilter.filter_prioritize')

        obj = PrioritizeIngredients(patient_id())
        for i in range(3):
            _ = obj.all

        prioritize_all_tags_mock.assert_called_once_with()

    def test_avoid(self, avoid_all_tags):
        obj = AvoidIngredients(patient_id())
        for i in range(3):
            _ = obj.all

        avoid_all_tags.assert_called_once_with()


class TestCaseIngredientFilter(object):

    def test_filter_prioritize(self, mocker):
        mocker.patch(
            'saana_lib.patient.PrioritizeIngredients.all_tags',
            new_callable=mocker.PropertyMock,
            return_value=[{'prior': {'soy': 0, 'flax': 2}}]
        )
        filter_prioritize = mocker.patch(
            'saana_lib.patient.IngredientFilter.filter_prioritize'
        )

        _ = PrioritizeIngredients(patient_id()).all
        filter_prioritize.assert_called_once_with(obj_id(), {'soy': 0, 'flax': 2})

    def test_filter_minimize(self, mocker):
        mocker.patch(
            'saana_lib.patient.MinimizeIngredients.all_tags',
            new_callable=mocker.PropertyMock,
            return_value=[{
                'minimize': {"insoluble fiber": {"min1": "10", "min2": "15"}}}
            ]
        )
        filter_minimize = mocker.patch(
            'saana_lib.patient.IngredientFilter.filter_minimize'
        )

        _ = MinimizeIngredients(patient_id()).all
        filter_minimize.assert_called_once_with(
            patient_id(), {"insoluble fiber": {"min1": "10", "min2": "15"}}
        )

    def test_filter_prioritize_values_case_1(self, avoid_all_tags):
        avoid_all_tags.return_value = [{'avoid': ['soy', 'flax']}]
        assert_equal_objects(
            IngredientFilter.filter_prioritize(
                patient_id(), {'beets': 0, 'flax': 1, 'carrot': 2}
            ), {'beets': 0, 'carrot': 2}
        )

    def test_filter_prioritize_values_case_2(self, avoid_all_tags, mocker):
        avoid_all_tags.return_value = [{'avoid': ['soy', 'flax']}]
        mocker.patch(
            'saana_lib.patient.MinimizeIngredients.all',
            new_callable=mocker.PropertyMock,
            return_value={'carrot': 1}
        )

        assert_equal_objects(
            IngredientFilter.filter_prioritize(
                patient_id(), {'beets': 0, 'flax': 1, 'carrot': 2}
            ), {'beets': 0}
        )

    def test_filter_minimize_values_case_1(self, avoid_all_tags):
        avoid_all_tags.return_value = [{'avoid': ['soy', 'flax']}]
        assert_equal_objects(
            IngredientFilter.filter_minimize(
                patient_id(), {'soy': 0, 'flax': 1, 'carrot': {'min1': 2, 'min2': 30}}
            ), {'carrot': {'min1': 2, 'min2': 30}}
        )


class TestCaseSubscription:
    """The next three tests check the logic circuit,
    testing almost each possible flow
    """
    @pytest.fixture
    def subscription(self, mocker):
        return mocker.patch(
            'saana_lib.patient.db.patient_subscriptions',
        )

    def test_subscription_exists(self, subscription):
        subscription.find_one.return_value = None
        assert not PatientSubscription(patient_id()).exists

    def test_inactive_subscription(self, subscription):
        subscription.find_one.return_value = {'status': 'inactive'}
        assert not PatientSubscription(patient_id()).is_active

    def test_weekly_order(self, subscription, mocker):
        subscription.find_one.return_value = {'subscription_id': 1}
        met = mocker.patch(
            'saana_lib.patient.db.mst_subscriptions',
        )
        met.find_one.return_value = {'interval_count': 1}
        assert PatientSubscription(patient_id()).weekly_order

    def test_patient_has_subscription(self, mocker):
        mocker.patch(
            'saana_lib.patient.PatientSubscription.exists',
            new_callable=mocker.PropertyMock
        )
        mocker.patch(
            'saana_lib.patient.PatientSubscription.is_active',
            new_callable=mocker.PropertyMock
        )
        assert PatientSubscription(patient_id()).patient_has_subscription


class TestCaseSymptomsProgress:

    @pytest.fixture
    def sorted_symptoms_mock(self, mocker):
        return mocker.patch(
            'saana_lib.patient.SymptomsProgress.symptoms_sorted_by_date',
            new_callable=mocker.PropertyMock,
        )

    def test_symptoms_sorted_by_date(self, mocker):
        symptoms_mock = mocker.patch('saana_lib.patient.db.patient_symptoms')
        _ = SymptomsProgress(patient_id()).symptoms_sorted_by_date
        symptoms_mock.find.assert_called_once_with({'patient_id': patient_id()})

    def test_symptoms_better(self, sorted_symptoms_mock, mocker):
        sorted_symptoms_mock.return_value = {patient_id().__str__(): [1, 2]}
        m = mocker.patch('saana_lib.tag.db.tags')
        m.find_one.return_value = {'prior': [], 'minimize': [], 'nutrient': []}
        assert list(SymptomsProgress(patient_id()).better) == [[]]

    """
    Note:
    worsen/better return a list. The easiest way to execute the 
    generator is calling list() but this would result in two nested
    lists [[]], so I had to fetch the element at index 0
    """

    def test_symptoms_worsen(self, sorted_symptoms_mock, mocker):
        sorted_symptoms_mock.return_value = {patient_id().__str__(): [2, 1]}
        m = mocker.patch('saana_lib.tag.db.tags')
        m.find_one.return_value = {
            'prior': {'burdock': 0},
            'minimize': {'spinach': 0},
            'avoid': {'okra': 0},
            'nutrient': {'vitamin': 0}
        }
        assert_equal_objects(
            SymptomsProgress(patient_id()).worsen,
            ['burdock', 'spinach', 'vitamin']
        )

    def test_symptoms_scales_are_constants(self, sorted_symptoms_mock, mocker):
        """If the symptoms scale remain constant, they will be
        considered a good sign.
        """
        sorted_symptoms_mock.return_value = {patient_id().__str__(): [2, 2]}
        m = mocker.patch('saana_lib.tag.db.tags')
        m.find_one.return_value = {
            'prior': {'burdock': 0},
            'minimize': {'spinach': 0},
            'avoid': {'okra': 0},
            'nutrient': {'vitamin': 0}
        }
        assert_equal_objects(
            list(SymptomsProgress(patient_id()).better)[0],
            ['burdock', 'spinach', 'vitamin']
        )

    def test_worsen_multiplier_ingredients(self, sorted_symptoms_mock, mocker):
        worsen = mocker.patch(
            'saana_lib.patient.SymptomsProgress.worsen',
            new_callable=mocker.PropertyMock,
        )
        _ = SymptomsProgress(patient_id()).worsen_multiplier_ingredients
        worsen.assert_called_once_with()

    def test_better_multiplier_ingredients(self, sorted_symptoms_mock, mocker):
        better = mocker.patch(
            'saana_lib.patient.SymptomsProgress.better',
            new_callable=mocker.PropertyMock,
        )
        _ = SymptomsProgress(patient_id()).better_multiplier_ingredients
        better.assert_called_once_with()

    def test_multiplier_ingredients_values(self, sorted_symptoms_mock, mocker):
        tags = mocker.patch('saana_lib.patient.db.tags')
        tags.find.return_value = [{'prior': {'milk': 2}}, {'prior': {'nuts': 0}}]
        sorted_symptoms_mock.return_value = {patient_id().__str__(): [1, 1]}
        assert_equal_objects(
            SymptomsProgress(patient_id()).better_multiplier_ingredients,
            ['milk', 'nuts']
        )

    def test_multiplier_ingredients_values_2(self, sorted_symptoms_mock, mocker):
        tags = mocker.patch('saana_lib.patient.db.tags')
        tags.find.return_value = [{'minimize': {'milk': 2}}, {'minimize': {'nuts': 0}}]
        sorted_symptoms_mock.return_value = {patient_id().__str__(): [2, 1]}
        assert_equal_objects(
            SymptomsProgress(patient_id()).worsen_multiplier_ingredients,
            ['milk', 'nuts']
        )


