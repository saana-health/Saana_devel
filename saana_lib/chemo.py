from datetime import datetime, timedelta

from saana_lib.connectMongo import db


class Chemo:

    def __init__(self, patient_id):
        self.patient_id = patient_id

    @property
    def today(self):
        return datetime.now()

    @property
    def next_tuesday(self):
        curr = self.today
        for i in range(7):
            if curr.weekday() == 1:
                break
            curr += timedelta(days=1)
        return curr

    @property
    def _treatment_dates_ahead(self):
        return any(
            x['treatment_date'] for x in db.patient_treatment_dates.find({
                'patient_id': self.patient_id,
                'treatment_date': {'$gte': self.today, '$lte': self.next_tuesday()}
                }, {'treatment_date': 1, '_id': 0}
            )
        )

    def recipes(self, score_board, slots):
        if not self._treatment_dates_ahead:
            return slots

        chemo_meals = [recipe for recipe in slots if 'soup' in recipe.name]

        for score in score_board:
            if len(chemo_meals) >= 3:
                return chemo_meals
            recipe_list = score_board[score]
            for recipe in recipe_list:
                if 'soup' in recipe.name:
                    chemo_meals.append(recipe)
        return chemo_meals

