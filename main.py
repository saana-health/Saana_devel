import argparse
from logging import getLogger

import conf
from exceptions import SaanaBaseException, DatabaseConfException
from saana_lib.ranking import RankingToDatabase
from saana_lib.recommendation import Recommendation, AllRecommendations


logger = getLogger(__name__)


def bootstrap_check():
    if not conf.DATABASE_USER:
        raise DatabaseConfException(
            "Please set the DATABASE_USER environment variable"
        )
    if conf.DATABASE_PASSWORD is None:
        raise DatabaseConfException(
            "Please set the DATABASE_PASSWORD environment variable"
        )


def run():
    print('Start of the process')
    bootstrap_check()
    parser = argparse.ArgumentParser()
    parser.add_argument('patient_id', type=str, help='Patient id')
    args = parser.parse_args()
    if args.patient_id:
        AllRecommendations(patient_id=args.patient_id).store()
        #RankingToDatabase(patient_id=args.patient_id).store()


if __name__ == "__main__":
    try:
        run()
    except SaanaBaseException as e:
        logger.critical(e)

