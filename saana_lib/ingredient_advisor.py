from saana_lib.connectMongo import db


class IngredientAdvisor:

    def __init__(self):
        self._tags = None
        self._restrictions = None

    @property
    def tags(self):
        tags_dict = dict()
        if not self._tags:
            for t in db.tags.find():
                tags_dict[t['_id']] = {
                    'category': t['type'],
                    'minimize': list(t['minimize'].keys()),
                    'prioritize': list(t['prior'].keys()),
                    'avoid': t['avoid'],
                    'name': t['name']
                }
            self._tags = tags_dict
        return self._tags

    def patient_inputs(self, patient_id):
        """
        Collect in one single list all the symptoms/comorbidities/
        diseases that the user filled in the questionnaire.
        :param patient_id:
        :return: a list of Object Id
        """
        ptags = list(
            patient_c['comorbidity_id'] for patient_c in
            db.patient_comorbidities.find({"patient_id": patient_id})
        )
        ptags.extend(
            patient_s['symptom_id'] for patient_s in
            db.patient_symptoms.find({"patient_id": patient_id})
        )
        ptags.extend(
            patient_d['disease_id'] for patient_d in
            db.patient_diseases.find({"patient_id": patient_id})
        )
        return ptags

    def other_restrictions(self, patient_id):
        """
        Retrieve the string inserted by the user when asked if she/he
        had any additional food restrictions.
        :param patient_id:
        :return: a list of strings
        """
        restrictions = list()
        if not self._restrictions:
            patient_restrictions = db.patient_other_restrictions.find_one(
                {'_id': patient_id}
            )
            if not patient_restrictions:
                return list()

            patient_restrictions = patient_restrictions['other_restriction']
            patient_restrictions = patient_restrictions.replace('\n', ',')

            for word in patient_restrictions.split(','):
                word = word.strip().lower()
                if word:
                    restrictions.append(word)
            self._restrictions = restrictions
        return self._restrictions

    def patient_info(self, patient_id):
        patient = db.patients.find_one({'_id': patient_id})
        if not patient:
            return '', ''

        user = db.users.find_one({'_id': patient['user_id']})
        if not user:
            return '', ''
        return user['first_name'], user['last_name']

    # TODO: refactor this method
    def ingredients_advice(self, patient_id):
        """

        :param patient_id:
        :return:
        """
        name, last_name = self.patient_info(patient_id)
        advice = {
            'patient': "{} {}".format(name, last_name),
            'prioritize': list(),
            'minimize': list(),
            'avoid': list()
        }
        for _id in self.patient_inputs(patient_id):
            t = self.tags.get(_id)
            if not t:
                continue
            advice['minimize'].extend(list(t['minimize'].keys()))
            advice['prioritize'].extend(list(t['prioritize'].keys()))
            advice['avoid'].extend(
                list(set(t['avoid'] + self.other_restrictions(patient_id)))
            )

        to_remove = list()
        for ing in advice['prioritize']:
            for e in advice['avoid']:
                if ing in e:
                    to_remove.append(ing)
        advice['prioritize'] = list(
            set(advice['prioritize']).difference(set(to_remove))
        )

        for ing in advice['minimize']:
            for e in advice['avoid']:
                if ing in e:
                    to_remove.append(ing)
        advice['minimize'] = list(
            set(advice['minimize']).difference(set(to_remove))
        )
        return advice


