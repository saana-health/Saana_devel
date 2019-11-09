from datetime import datetime

from pymongo.collection import ObjectId
import pytest

from saana_lib.patient import SymptomsProgress
from tests.conftest import assert_equal_objects


@pytest.fixture
def symptoms_progress_test_db(integration_setup, mocker):
    test_db = integration_setup

    patient_id = ObjectId('5cabf2ad37c87f3ac00e8701')
    symptom_id_1 = ObjectId('5cab584074e88f0cb0977a0f')
    symptom_id_2 = ObjectId('5cabf2ad37c87f3ac00e870d')
    test_db.patient_symptoms.insert_many([
        {'symptom_id': symptom_id_1,
         'created_at': datetime(2019, 4, 2, 1),
         'updated_at': datetime(2019, 4, 2, 1),
         'patient_id': patient_id,
         'symptoms_scale': 3},
        {'symptom_id': symptom_id_2,
         'created_at': datetime(2019, 3, 12, 1),
         'updated_at': datetime(2019, 3, 12, 1),
         'patient_id': patient_id,
         'symptoms_scale': 5},
        {'symptom_id': symptom_id_1,
         'created_at': datetime(2019, 10, 10, 1),
         'updated_at': datetime(2019, 10, 10, 1),
         'patient_id': patient_id,
         'symptoms_scale': 8},
        {'symptom_id': symptom_id_2,
         'created_at': datetime(2019, 7, 20, 1),
         'updated_at': datetime(2019, 7, 20, 1),
         'patient_id': patient_id,
         'symptoms_scale': 1},
        {'symptom_id': symptom_id_1,
         'created_at': datetime(2019, 5, 15, 1),
         'updated_at': datetime(2019, 5, 15, 1),
         'patient_id': patient_id,
         'symptoms_scale': 2},
        ]
    )
    mocker.patch('saana_lib.patient.db', test_db)
    yield patient_id, symptom_id_1, symptom_id_2
    test_db.patient_symptoms.drop()


def test_symptoms_sorted_by_date(symptoms_progress_test_db):
    patient_id, symptom_id_1, symptom_id_2 = symptoms_progress_test_db

    assert_equal_objects(
        SymptomsProgress(patient_id).symptoms_sorted_by_date,
        {symptom_id_1: [8, 2, 3], symptom_id_2: [1, 5]}
    )


