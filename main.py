import argparse
from logging import getLogger

import conf
from saana_lib.scoreboard import Scoreboard


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
        parser.add_argument('mode', choices=['test', 'prod'], help='running mode')
        args = parser.parse_args()
        testing_mode = args.mode == 'test'
        Scoreboard().as_file()
    except ConfException as e:
        logger.critical(e)


if __name__ == "__main__":
    run()
