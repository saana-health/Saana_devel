import pytest

import conf
import main
from unittest.mock import Mock


def test_config_check_1(argparse_patch):
    argparse_patch.setattr(conf, 'DATABASE_USER', None)
    spy = Mock(spec=main.ScoreboardPatient)
    argparse_patch.setattr(main, 'Optimizer', spy)
    main.run()
    assert not spy.called


def test_config_check_2(argparse_patch):
    argparse_patch.setattr(conf, 'DATABASE_PASSWORD', None)
    spy = Mock(spec=main.ScoreboardPatient)
    argparse_patch.setattr(main, 'Optimizer', spy)
    main.run()
    assert not spy.called


def test_config_check_3(argparse_patch):
    class FakeOptimizer:
        def optimize(self):
            return

    spy = Mock(spec=FakeOptimizer)
    argparse_patch.setattr(main, 'Optimizer', spy)
    main.run()
    assert spy.called


