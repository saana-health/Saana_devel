from pymongo.collection import ObjectId

from saana_lib.connectMongo import db
from exceptions import PatientNotFound, UserNotFound


class User:

    def __init__(self, user_id):
        if not isinstance(user_id, ObjectId):
            self.user_id = ObjectId(user_id)
        else:
            self.user_id = user_id

    @property
    def user(self):
        u = db.users.find_one({'_id': self.user_id})
        if not u:
            raise UserNotFound(
                "User with `id`: {} does not exists".format(self.user_id)
            )
        return u

    @property
    def patient_of_user(self):
        p = db.patients.find_one({'user_id': self.user['_id']})
        if not p:
            raise PatientNotFound(
                "Patient with `user_id`: {} does not exists".format(self.user['user_id'])
            )

        return p

    @property
    def email(self):
        return self.user['email']

    @property
    def name(self):
        return self.user['first_name']

