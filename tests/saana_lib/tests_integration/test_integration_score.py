import pytest

from saana_lib.score import MinimizedScore, PrioritizedScore
from tests.conftest import PATIENT, RECIPES, TAGS, assert_equal_objects


def test_minimize_score(integration_db):
    """
    Minimize ingredients contained in Recipe[0] are:

    saury fish:  10  (ref. 10)
    cabbage:  200  (ref. 30|200 )
    fish:  30   (ref: 20 )

    formula:  saury-fish (ignored) - 60 - 30
    """
    assert MinimizedScore(RECIPES[0]['_id'], PATIENT['_id']).value == -90


def test_minimize_score_with_worsened_symptom(integration_db):
    """
    Minimize ingredients contained in Recipe[0] are:

    saury fish:  10  (ref. 10)
    cabbage:  200  (ref. 30|200 )
    fish:  30   (ref: 20 )

    this time the formula would be:
    saury-fish (ignored) - (60 * 1.5) - (30 * 1.5)
    """
    from datetime import datetime

    integration_db.patient_symptoms.insert_one({
        'symptom_id': TAGS[0]['tag_id'],
        'patient_id': PATIENT['_id'],
        'created_at': datetime(2019, 10, 15),
        'updated_at': datetime(2019, 10, 15),
        'symptoms_scale': 7
    })

    assert_equal_objects(
        MinimizedScore(RECIPES[0]['_id'], PATIENT['_id']).worsen_ingredients,
        ['saury fish', 'cabbage', 'fish', 'komatsuna', 'pak choi']
    )
    assert MinimizedScore(RECIPES[0]['_id'], PATIENT['_id']).value == -135


def test_prioritize_score(integration_db):
    """
    Only potato appears to be a minimize ingredient
    formula: potato (60 > ref: 50)
    """
    assert PrioritizedScore(RECIPES[1]['_id'], PATIENT['_id']).value == 10

