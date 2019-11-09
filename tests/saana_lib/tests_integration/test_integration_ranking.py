from datetime import datetime

from tests.conftest import obj_id
from saana_lib.ranking import RankingToDatabase


def test_recipe_recommendation_store_format(integration_setup, mocker):
    test_db = integration_setup
    mocker.patch('saana_lib.ranking.db', test_db)
    mocker.patch(
        'saana_lib.ranking.Ranking.compute',
        return_value={1: [{
            'patient_id': obj_id(),
            'recipe_id': obj_id(),
            'score': 100,
            'is_like': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }]}
    )
    RankingToDatabase(obj_id()).store()

    rr = test_db.patient_recipe_recommendation.find_one(
        {'patient_id': obj_id(), 'recipe_id': obj_id()}
    )
    assert rr['score'] == 100

