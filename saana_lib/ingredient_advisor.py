from saana_lib.connectMongo import db


class IngredientAdvisor:

    def __init__(self):
        self._tags = None

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
        ptags = list(
            patient_c['comorbidity_id'] for patient_c in
            db.patient_comorbidities.find({"patient_id": patient_id})
        )
        ptags.extend(
            patient_s['symptom_id'] for patient_s in
            db.patient_symptoms.find({"patient_id": patient_id})
        )
        ptags.extend(
            patient_s['disease_id'] for patient_s in
            db.patient_diseases.find({"patient_id": patient_id})
        )
        return ptags

    def patient_info(self, patient_id):
        patient = db.patients.find_one({'_id': patient_id})
        if not patient:
            return '', ''

        user = db.users.find_one({'_id': patient['user_id']})
        if not user:
            return '', ''
        return user['first_name'], user['last_name']

    def ingredients_advice(self, patient_id):
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
            advice['avoid'].extend(list(t['avoid']))
        return advice


