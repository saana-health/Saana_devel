import pytest
from pymongo.collection import ObjectId

from saana_lib.user import User
from exceptions import PatientNotFound, UserNotFound


def obj_id():
    return ObjectId('5d7258c977f06d4208211eb4')


def test_patient_of_user(mocker):
    patients = mocker.patch('saana_lib.user.db.patients')
    users = mocker.patch('saana_lib.user.db.users')
    _ = User(obj_id()).patient_of_user
    patients.find_one.assert_called_with({'user_id': users.find_one()['user_id']})


def test_patient_not_found(mocker):
    mocker.patch('saana_lib.user.db.patients.find_one()', return_value=None)
    users = mocker.patch('saana_lib.user.db.users')
    users.find_one.return_value={'_id': 1, 'user_id': 2}
    with pytest.raises(PatientNotFound):
        _ = User(obj_id()).patient_of_user

    users.find_one.assert_called_with({'_id': obj_id()})


def test_user_not_found(mocker):
    mocker.patch('saana_lib.user.db.users.find_one()', return_value=None)
    with pytest.raises(UserNotFound):
        _ = User(obj_id()).user

