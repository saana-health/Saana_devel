from datetime import datetime, timedelta

from pymongo.collection import ObjectId
from pymongo import ASCENDING, DESCENDING

from constants import constants_wrapper as constants
from exceptions import PatientNotFound, UserNotFound
from saana_lib.connectMongo import db
from saana_lib.tag import Tag


class Patient:
    tag_field = ''

    def __init__(self, patient_id):
        if not isinstance(patient_id, ObjectId):
            self._patient_id = ObjectId(patient_id)
        else:
            self._patient_id = patient_id

    @property
    def pid(self):
        return self._patient_id

    def read(self):
        raise NotImplementedError()

    def read_as_list(self):
        return list(self.read())

    def read_as_tags(self):
        list_of_tags_id = list(
            e[self.tag_field] for e in self.read() if e.get(self.tag_field)
        )
        return list(db.tags.find({'tag_id': {'$in': list_of_tags_id}}))

    @property
    def patient_instance(self):
        obj = db.patients.find_one({'_id': self.pid})
        if not obj:
            raise PatientNotFound()
        return obj

    @property
    def user_id(self):
        return self.patient_instance.get('user_id')

    @property
    def user_of_patient(self):
        u = db.users.find_one({'_id': self.user_id})
        if not u:
            raise UserNotFound()

        return u


"""
Few notes on these classes. The reason I implemented a read() 
method which, as today, is not called directly, but consumed 
by read_as_tags(), was because I thought in the future I might 
need to access to the object itself.
The read as tags might be also implemented in this way:

list(
    db.tags.find({'tag_id': 
        {'$in': map(lambda e: e[self.tag_field], self.read()) }}
    )
)
"""


class PatientDisease(Patient):
    tag_field = 'disease_id'

    def read(self):
        for disease in db.patient_diseases.find({'patient_id': self.pid}):
            yield disease


class PatientComorbidity(Patient):
    tag_field = 'comorbidity_id'

    def read(self):
        for comorbidity in db.patient_comorbidities.find(
                {"patient_id": self.pid}):
            yield comorbidity


class PatientDrug(Patient):
    tag_field = 'drug_id'

    def read(self):
        for drug in db.patient_drugs.find({"patient_id": self.pid}):
            yield drug


class PatientSymptom(Patient):
    tag_field = 'symptom_id'

    def read(self):
        for symptom in db.patient_symptoms.find({"patient_id": self.pid}):
            yield symptom


class PatientOtherRestrictions(Patient):
    """
    the string inserted by the user when asked if she/he
    had any additional food restrictions.
    """
    def read(self):
        space_sep = ' '
        restriction = db.patient_other_restrictions.find_one(
            {"patient_id": self.pid}
        )

        patient_restriction = restriction['other_restriction']
        patient_restriction = patient_restriction.replace('\n', space_sep)
        patient_restriction = patient_restriction.replace(',', space_sep)

        for word in patient_restriction.split(space_sep):
            word = word.strip().lower()
            if word:
                yield word

    def read_as_tags(self):
        return self.read_as_list()


class PatientTags:
    ingredient_list_name = ''

    def __init__(self, patient_id):
        if not isinstance(patient_id, ObjectId):
            self.patient_id = ObjectId(patient_id)
        else:
            self.patient_id = patient_id
        self._container = None

    @property
    def filter_func(self):
        raise NotImplementedError()

    @property
    def all_tags(self):
        return PatientDisease(self.patient_id).read_as_tags() + \
               PatientComorbidity(self.patient_id).read_as_tags() + \
               PatientDrug(self.patient_id).read_as_tags() + \
               PatientSymptom(self.patient_id).read_as_tags()

    @property
    def all(self) -> dict:
        """
        :return: a dictionary with name/quantity of each ingredient/nutrient
        to be minimized/prioritized for the patient
        """
        if not self.ingredient_list_name:
            return dict()

        if self._container is None:
            self._container = dict()
            for tag in self.all_tags:
                self._container.update(
                    dict((k, v) for k, v in tag[self.ingredient_list_name].items()
                         if k not in self._container)
                )

            func = self.filter_func
            self._container = func(self.patient_id, self._container)
        return self._container


"""
The reason why the following classes are stored in this file
is because ingredients pertain to the user, not to the 
recommendation.
"""


class MinimizeIngredients(PatientTags):
    ingredient_list_name = 'minimize'

    @property
    def filter_func(self):
        return getattr(IngredientFilter, "filter_minimize")


class PrioritizeIngredients(PatientTags):
    ingredient_list_name = 'prior'

    @property
    def filter_func(self):
        return getattr(IngredientFilter, "filter_prioritize")


class Nutrients(PatientTags):
    """
    Inside each Tags, I expect the Nutrients array to have this
    schema. In this way the

    {'nutrient': [
        { 'ObjectId: {
            'type': 'min/pri/avoid',   (minimized or prioritized)
            'name': 'sodium',
            'quantity': 2,
            'units': 'g'}
            }
        ]
    }

    so all() property will return a dict with ObjectId(s) as keys
    """
    ingredient_list_name = 'nutrient'

    # TODO: to be implemented
    @property
    def filter_func(self):
        return getattr(NutrientFilter, 'filter')


class AvoidIngredients(PatientTags):
    ingredient_list_name = 'avoid'

    @property
    def all(self) -> set:
        if self._container is None:
            self._container = list()
            for tag in self.all_tags:
                self._container.extend(tag['avoid'])

            self._container += self.other_restrictions
        return set(self._container)

    @property
    def all_ingredients_names(self):
        return map(lambda d: d['name'], db.mst_food_ingredients.find(
                {}, {'name': 1, '_id': 0}))

    def ingredient_exists(self, ingredient_name):
        return any(True for name in self.all_ingredients_names
                   if ingredient_name in name or name in ingredient_name)

    @property
    def other_restrictions(self):
        return list(
            name for name in PatientOtherRestrictions(self.patient_id).read()
            if self.ingredient_exists(name)
        )


class IngredientFilter:
    """Only minimize and prioritize containers are
    filtered. That's because avoid has higher precedence
    so if an ingredient is both in avoid and minimize
    it will be removed from the former list
    """

    @classmethod
    def filter_minimize(cls, patient_id, ingredients: dict):
        """An ingredient can belong to minimize if it does
        not pertain to avoid
        :returns a filtered ingredients list, in the form
        of a dictionary
        """
        avoid_ingredients = AvoidIngredients(patient_id).all
        filtered_ingredients = dict()

        for ingr_name, quantity in ingredients.items():
            if ingr_name in avoid_ingredients:
                continue
            filtered_ingredients[ingr_name] = quantity
        return filtered_ingredients

    @classmethod
    def filter_prioritize(cls, patient_id, ingredients: dict):
        """An ingredient can be in prioritize list if it is not
        contained either in avoid and minimize
        """
        avoid_ingredients = AvoidIngredients(patient_id).all
        minimize_ingredients = MinimizeIngredients(patient_id).all
        filtered_ingredients = dict()

        for ingr_name, quantity in ingredients.items():
            if ingr_name in avoid_ingredients or ingr_name in minimize_ingredients:
                continue
            filtered_ingredients[ingr_name] = quantity
        return filtered_ingredients


class NutrientFilter:

    """
    TODO: to be implemented
    being that nutrients should be a distinct set (not overlapped)
    with ingredients and the idea would be to filter out nutrients
    by comparing them with other-restrictions and with
    better/worsen elements
    """
    def filter(self, nutrients: dict):
        return nutrients


class PatientSubscription(Patient):

    @property
    def subscription(self):
        return db.patient_subscriptions.find_one(
            {'patient_id': self.pid}
        )

    @property
    def today(self):
        return datetime.now()

    @property
    def exists(self):
        return self.subscription is not None

    @property
    def is_active(self):
        return self.subscription['status'] == 'active'

    @property
    def weekly_order(self):
        return db.mst_subscriptions.find_one(
                {'_id': self.subscription['subscription_id']}
        )['interval_count'] == constants.SUBSCRIPTION_WEEKLY_INTERVAL

    @property
    def no_order_last_week(self):
        return db.orders.find_one({
            'patient_id': self.pid,
            'week_start_date': self.today + timedelta(weeks=-1)}
        ) is None

    @property
    def patient_has_subscription(self):
        if not self.exists or not self.is_active:
            return False

        # if self.weekly_order:
        #     return True
        #
        # return self.no_order_last_week
        return True


class SymptomsProgress(PatientSymptom):
    """
    The idea behind this class is to provide a list of IDs
    of symptoms of the patient being processed, that that got
    worse/better over the time and this would impact the
    calculation of the recipes rankings
    Note that a symptom is a tag [symptom_id ==> tag_id in tags]
    """

    @property
    def worsen(self):
        """if the scale of the symptom being considered has increased
        over the time, then it got worst.
        :returns the list of all elements (avoid, nutrients, minimize
        and prioritize) that belong to that this symptom
        """
        for symptom_id, symptom_scale in self.symptoms_sorted_by_date.items():
            if len(symptom_scale) < 2:
                continue

            if symptom_scale[0] - symptom_scale[1] > 0:
                yield Tag(symptom_id).all_elements_names()

    @property
    def better(self):
        """opposite of the method above. If the intensity of the
        symptom has decrease, its ingredients should be prioritized
        """
        for symptom_id, symptom_scale in self.symptoms_sorted_by_date.items():
            if len(symptom_scale) < 2:
                continue

            if symptom_scale[0] - symptom_scale[1] <= 0:
                yield Tag(symptom_id).all_elements_names()

    @property
    def symptoms_sorted_by_date(self):
        """Cannot use the read() method of the parent class
        because it is a generator and cannot be sorted using
        the pymongo.collection sort()
        """
        sorted_symptoms = dict()
        cursor = db.patient_symptoms.find({'patient_id': self.pid})
        for symptom in cursor.sort('created_at', DESCENDING):
            if symptom['symptom_id'] not in sorted_symptoms:
                sorted_symptoms[symptom['symptom_id']] = list()
            sorted_symptoms[symptom['symptom_id']].append(symptom['symptoms_scale'])

        return sorted_symptoms

    @property
    def worsen_multiplier_ingredients(self):
        cursor = db.tags.find(
            {'tag_id': {'$in': list(self.worsen)}}, {'minimize': 1, '_id': 0}
        )
        ingredients = list()
        for ingredient in cursor:
            ingredients.extend(list(ingredient['minimize']))
        return ingredients

    @property
    def better_multiplier_ingredients(self):
        cursor = db.tags.find(
            {'tag_id': {'$in': list(self.better)}}, {'prior': 1, '_id': 0}
        )
        ingredients = list()
        for ingredient in cursor:
            ingredients.extend(list(ingredient['prior']))
        return ingredients

