from djongo.models import CheckConstraint, Q
from djongo import models
from pymongo.read_concern import ReadConcern


class Tags(models.Model):
    _id = models.ObjectIdField()
    avoid = models.ArrayField()
    prioritize = models.ArrayField()
    minimize = models.ArrayField()

    class Meta:
        constraints = [
        ]