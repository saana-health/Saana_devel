from pymongo.collection import ObjectId

from saana_lib.connectMongo import db


class Patient:
    tag_field = ''

    def __init__(self, patient_id):
        self._patient_id = ObjectId(patient_id)

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
        return list(db.mst_tags.find({'_id': {'$in': list_of_tags_id}}))


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
    def all_tags(self):
        return PatientDisease(self.patient_id).read_as_tags() + \
               PatientComorbidity(self.patient_id).read_as_tags() + \
               PatientDrug(self.patient_id).read_as_tags() + \
               PatientSymptom(self.patient_id).read_as_tags()

    @property
    def all(self):
        if not self.ingredient_list_name:
            return set()

        if self._container is None:
            self._container = dict()
            for tag in self.all_tags:
                self._container.update(
                    dict((k, v) for k, v in tag[self.ingredient_list_name].items()
                         if k not in self._container)
                )

            func = getattr(
                IngredientFilter,
                "filter_{}".format(
                    'prioritize' if self.ingredient_list_name == 'prior' else 'minimize'
                )
            )
            self._container = func(self.patient_id, self._container)
        return self._container


class MinimizeIngredients(PatientTags):
    ingredient_list_name = 'minimize'


class PrioritizeIngredients(PatientTags):
    ingredient_list_name = 'prior'


class AvoidIngredients(PatientTags):
    ingredient_list_name = 'avoid'

    @property
    def all(self):
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

    @classmethod
    def filter_minimize(cls, patient_id, ingredients: dict):
        avoid_ingredients = AvoidIngredients(patient_id).all
        filtered_ingredients = dict()

        for ingr, quantity in ingredients.items():
            if ingr in avoid_ingredients:
                continue
            filtered_ingredients[ingr] = quantity
        return filtered_ingredients

    @classmethod
    def filter_prioritize(cls, patient_id, ingredients: dict):
        avoid_ingredients = AvoidIngredients(patient_id).all
        minimize_ingredients = MinimizeIngredients(patient_id).all
        filtered_ingredients = dict()

        for ingr, quantity in ingredients.items():
            if ingr in avoid_ingredients or ingr in minimize_ingredients:
                continue
            filtered_ingredients[ingr] = quantity
        return filtered_ingredients


