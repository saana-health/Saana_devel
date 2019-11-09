import argparse
from logging import getLogger

import conf
from saana_lib.ranking import Scoreboard
from saana_lib.recommendation import IngredientAdvisor


logger = getLogger(__name__)


class ConfException(Exception):
    """"""


def bootstrap_check():
    if conf.DATABASE_USER is None:
        raise ConfException("Please set the env DATABASE_USER as variable")
    if conf.DATABASE_PASSWORD is None:
        raise ConfException("Please set the env DATABASE_PASSWORD as variable")


def run():
    try:
        bootstrap_check()
        parser = argparse.ArgumentParser()
        parser.add_argument('patient_id', type=str, help='Patient id')
        args = parser.parse_args()
        if args.patient_id:
            print(args.patient_id)
            res = IngredientAdvisor().ingredients_advice(args.patient_id)
            print(res)
        else:
            pass
            #Scoreboard().as_file()
    except ConfException as e:
        logger.critical(e)


if __name__ == "__main__":
    run()
