from datetime import datetime

from tests.conftest import obj_id
from saana_lib.ranking import Ranking, RankingToDatabase, RankingToFile
from tests.conftest import assert_equal_objects


class TestCaseRanking:

    def test_ranking_compute(self, mocker):
        find_recipes = mocker.patch('saana_lib.ranking.db.mst_recipe')
        _ = Ranking(obj_id()).compute()
        find_recipes.find.assert_called_once_with()

    def test_recommendation_have_same_score(self, mocker):
        find_recipes = mocker.patch('saana_lib.ranking.db.mst_recipe')
        find_recipes.find.return_value = range(3)

        mocker.patch(
            'saana_lib.recommendation.RecipeRecommendation.score',
            new_callable=mocker.PropertyMock,
            return_value=10
        )
        _ = Ranking(obj_id()).compute()
        assert len(_[10]) == 3

    def test_ranking_default_order(self, mocker):
        find_recipes = mocker.patch('saana_lib.ranking.db.mst_recipe')
        find_recipes.find.return_value = range(3)

        m = mocker.patch(
            'saana_lib.recommendation.RecipeRecommendation.score',
            new_callable=mocker.PropertyMock,
            side_effect=range(10, 31, 10)
        )
        _ = Ranking(obj_id()).compute()
        assert list(_) == [30, 20, 10]
        assert m.call_count == 3

    def test_ranking_ascending_order(self, mocker):
        find_recipes = mocker.patch('saana_lib.ranking.db.mst_recipe')
        find_recipes.find.return_value = range(3)

        mocker.patch(
            'saana_lib.recommendation.RecipeRecommendation.score',
            new_callable=mocker.PropertyMock,
            side_effect=range(10, 31, 10)
        )
        _ = Ranking(obj_id()).compute(descending=False)
        assert list(_) == [10, 20, 30]


class TestCaseOutIn:
    klass = RankingToDatabase(obj_id())

    def test_store_elements_count_exceed_default_limit(self, mocker):
        """
        There are 5 elements for each score. Verify that the limit
        is respected although the # of elements exceed it
        """
        m = mocker.patch('saana_lib.ranking.db.patient_recipe_recommendation')
        _compute = mocker.patch('saana_lib.ranking.Ranking.compute')

        _compute.return_value = dict((i, list(range(5))) for i in range(10))
        self.klass.store()
        assert m.insert_one.call_count == 20

    def test_store_less_element_than_limit(self, mocker):
        m = mocker.patch('saana_lib.ranking.db.patient_recipe_recommendation')
        _compute = mocker.patch('saana_lib.ranking.Ranking.compute')

        _compute.return_value = dict((i, list(range(5))) for i in range(2))
        self.klass.store()
        assert m.insert_one.call_count == 10

    def test_store_order_is_preserved(self, mocker):
        from collections import OrderedDict
        m = mocker.patch('saana_lib.ranking.db.patient_recipe_recommendation')
        mocker.patch(
            'saana_lib.ranking.Ranking.compute',
            return_value=OrderedDict((i, [i]) for i in range(3, 0, -1))
        )

        self.klass.store()
        assert tuple(m.insert_one.mock_calls[0])[1][0] == 3


class TestCaseRankingToFile:

    def test_proxy_content_to_file(self, mocker):
        """mock called three times, one for the

        """
        mock = mocker.patch('saana_lib.ranking.datetime')
        mock.now.return_value = datetime(2019, 5, 18, 15, 17, 8, 132263)

        m = mocker.patch('saana_lib.ranking.out_to_xls')
        mocker.patch(
            'saana_lib.ranking.Ranking.compute',
            return_value=dict((i, [{
                'recipe_id': 'id', 'score': 1
            }]) for i in range(3, 0, -1))
        )
        RankingToFile(obj_id()).store()
        assert m.call_count == 4
        m.assert_called_with("{}-{}".format(
            obj_id().__str__(),
            '2019-05-18'
        ), ["id", "1"])

    def test_add_headers_only_once(self, mocker):
        m = mocker.patch('saana_lib.ranking.RankingToFile.write_headers')
        mocker.patch(
            'saana_lib.ranking.Ranking.compute',
            return_value=dict((i, [{}]) for i in range(3, 0, -1))
        )
        RankingToFile(obj_id()).store()
        m.assert_called_once_with()

