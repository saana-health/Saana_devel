from tests.conftest import obj_id, PATIENT, RECIPES
from saana_lib.ranking import RankingToDatabase


patient_id = obj_id
recipe_id = obj_id


def test_ranking_for_a_patient(integration_db):
    """
    Results explained:

    recipe[0] ingredients:

    name           quantity         ref

    saury fish       10              40      M
    fish             30              50      M
    cabbage          200           30|200    M
    pak choi          -               -      A
    komatsuna        10              34      P
    asparagus        10              30      P

    ==> 100 - 60 (avoid) - 90 (fish, cabbage) + 0 == -50

    recipe[1] ingredients:

    name           quantity         ref

    green beans     30              40      P
    potato          60              50      P
    ginger          -               -       A
    carrot          -               -       A
    zucchini        14             2|20     M
    seaweed         10            15|35     M

    ==> 100 - 120 (avoid) - 30 (zucchini) + 10 (potato) == -40

    """

    RankingToDatabase(PATIENT['_id']).store()

    assert integration_db.patient_recipe_recommendation.find_one(
        {'recipe_id': RECIPES[0]['_id']}
    )['score'] == -50
    assert integration_db.patient_recipe_recommendation.find_one(
        {'recipe_id': RECIPES[1]['_id']}
    )['score'] == -40