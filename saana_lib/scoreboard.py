from logging import getLogger
import itertools
from datetime import datetime, timedelta
from pymongo.errors import PyMongoError

import conf
from saana_lib import model, connectMongo, utils, chemo
from saana_lib.manual_input import manual_input
from constants import constants_wrapper as constants
from saana_lib.utils import csv_writer


logger = getLogger(__name__)


class ScoreboardException(Exception):
    """"""


class ScoreboardPatientException(Exception):
    """"""


class ScoreboardPatient:
    """
    This is an
    """

    def __init__(self, patient, testing_mode=conf.DEV_ENV):
        """
        By default manual_input returns two lists
        :param test:
        """
        self.testing_mode = testing_mode
        self.db_client = connectMongo.db
        self.today = datetime.now()
        self._meals = None

        self._id = patient['_id']
        self.user_id = patient['user_id']

    @property
    def user_of_patient(self):
        u = self.db_client.users.find_one({'_id': self.user_id})
        if not u:
            raise ScoreboardPatientException(
                "There is not user object for patient: {}".format(self._id)
            )
        return u

    @property
    def email(self):
        return self.user_of_patient['email']

    @property
    def name(self):
        return self.user_of_patient['email']

    @property
    def _comorbidities(self):
        return list(
            o['_id'] for o in self.db_client.patient_comorbidities.find(
                {'patient_id': self._id}
            )
        )

    @property
    def _diseases(self):
        return list(
            o['_id'] for o in self.db_client.patient_diseases.find(
                {'patient_id': self._id}
            )
        )

    @property
    def _symptoms(self):
        return list(
            o['_id'] for o in self.db_client.patient_symptoms.find(
                {'patient_id': self._id}
            )
        )

    @property
    def _treatment_drugs(self):
        return list(
            o['_id'] for o in self.db_client.patient_drugs.find(
                {'patient_id': self._id}
            )
        )

    @property
    def _other_restriction(self):
        return list()

    @property
    def has_active_subscription(self):
        """Checks subscription status"""
        if self.testing_mode:
            return True

        patient_subscription = self.db_client.patient_subscriptions.find_one(
            {'patient_id': self._id}
        )
        if not patient_subscription or \
            (patient_subscription and patient_subscription['status'] != 'active'):
                return False

        # Weekly order
        if self.db_client.mst_subscriptions.find_one(
                {'_id': patient_subscription['subscription_id']}
        )['interval_count'] == constants.SUBSCRIPTION_WEEKLY_INTERVAL:
            return True

        # order if not ordered last week
        return self.db_client.orders.find_one({
            'patient_id': self._id,
            'week_start_date': self.today + timedelta(weeks=-1)}
        ) is None

    @property
    def tags(self):
        return self.db_client.tags.find(
            {'tag_id': {
                '$in': self._symptoms + self._diseases +
                       self._treatment_drugs + self._comorbidities
                }
            }
        )

    @property
    def avoid(self):
        return list(set(
            itertools.chain(*[utils.tag_dict_to_class(tag).avoid for tag in self.tags])
        ))

    @property
    def minimize(self):
        d = dict()
        for t in self.tags:
            d.update(t['minimize'])
        return d

    @property
    def prioritize(self):
        d = dict()
        for t in self.tags:
            d.update(t['prior'])
        return d


class Scoreboard:

    def __init__(self):
        self.db_client = connectMongo.db
        self.today = datetime.now()
        self._meals = None
        self.single_patient_email = ''

    def get_ingredient_name(self, ingredient_id):
        ing = self.db_client.mst_food_ingredients.find_one({'_id': ingredient_id})
        return ing['name'] if ing else ''

    @property
    def all_patients(self):
        """
        TODO: instead of querying for the patients, filter out
        those users whose email is not in self.patients email.

        this is a generator. at each iteration return one
        ScoreboardPatient object
        """
        for patient in self.db_client.patients.find():
            patient = ScoreboardPatient(patient)
            if not patient.has_active_subscription:
                continue

            yield patient

    @property
    def meals(self):
        """
        TODO: fix inner loop (has no sense). Making N queries to retrieve
        only one information (the name) that might be already stored
        inside the meal dict

        NOTE:
        If an ingredient is not found then it should not be added to
        :return: a list of Meal object
        """
        if not self._meals:
            meals = dict()
            for meal in self.db_client.meal_infos.find():
                ingredients = {}
                for ingredient in meal['ingredients']:
                    name = self.get_ingredient_name(ingredient['food_ingredient_id'])
                    if name:
                        ingredients[name] = ingredient['quantity']

                meal['ingredients'] = ingredients
                new_meal = model.Meal()
                new_meal.dict_to_class(meal)
                meals[meal['_id']] = new_meal
            self._meals = meals
        return self._meals

    @property
    def tags(self):
        hash_tag = {}
        for tag in self.db_client.tags.find():
            new_tag = model.Tag()
            new_tag.dict_to_class(tag)
            hash_tag[tag['_id']] = new_tag
        return hash_tag

    def patients(self, patient_email=''):
        if patient_email:
            user = self.db_client.users.find_one({"email": patient_email})
            patient = self.db_client.patients.find_one({'user_id': user['_id']})
            if not (user and patient):
                return list()
            return [ScoreboardPatient(patient)]

        return self.all_patients

    def as_file(self, patient_email=''):
        for patient in self.patients(patient_email):
            filename = constants.SCOREBOARD_CSV_FILE_NAME_PATTERN.format(
                constants.SCOREBOARD_FOLDER,
                patient.name,
                self.today
            )

            patient_name, csv_list = self.scoreboard_to_csv_rows(
                self.get_score_board(patient), patient._id
            )
            csv_writer(filename, csv_list)

    def as_dict(self, patient_email=''):
        """
        """
        # TODO to uncomment
        #subscription_meals = connectMongo.get_subscription(patient._id)
        subscription_meals = 0
        board = dict()
        for patient in self.patients(patient_email):
            try:
                score_board, repeat_one_week = self.get_score_board(patient)
                slots, supplierIds = self.choose_meal(score_board, repeat_one_week)
                slots = self.reorder_slots(slots)

                if subscription_meals == 7:
                    end_date = utils.find_tuesday(self.today, 2)
                else:
                    end_date = utils.find_tuesday(self.today, 3)

                slots = chemo.reorder_chemo(
                    slots,
                    patient._id,
                    self.today,
                    end_date,
                    score_board,
                    supplierIds
                )

                # TODO uncomment in the next days
                # self.to_mongo(slots, patient._id, self.today, end_date)
                # self.write_csv(slots,patient._id, self.today)

            except ScoreboardPatientException:
                logger.error(
                    "Error while generating meals for {}".format(patient.name)
                )
        return board

    def choose_chemo_meals(self, score_board, slots, supplierIds):
        # first look at current meals and choose more from the score_board
        chemo_meals = []
        for meal in slots:
            if 'soup' in meal['meal'].type:
                chemo_meals.append(meal['meal'])

        if len(chemo_meals) >= 3:
            return chemo_meals

        for score in score_board:
            meals = score_board[score]
            for meal in meals:
                # SKIP if not one of the suppliers we already chose
                if meal['meal'].supplier_id not in supplierIds:
                    continue
                if 'soup' in meal['meal'].type:
                    chemo_meals.append(meal['meal'])

                if len(chemo_meals) >= 3:
                    return chemo_meals

        return chemo_meals

    def choose_meal(self, score_board, repeat_one_week):
        """
        :param score_board:
        :param repeat_one_week:
        :return:
        """
        num_repeat = 0
        suppliers = list(connectMongo.db.users.find({'role': 'supplier'}))

        # manual matching suppliers with their ID (ObjectId)
        Veestro = [obj['_id'] for obj in suppliers if obj['first_name'] == 'Veestro'][0]
        Euphebe = [obj['_id'] for obj in suppliers if obj['first_name'] == 'Euphebe'][0]
        FoodNerd = [obj['_id'] for obj in suppliers if obj['first_name'] == 'FoodNerd'][0]
        FrozenGarden = [obj['_id'] for obj in suppliers if obj['first_name'] == 'FrozenGarden'][0]

        bucket = dict((x['_id'], list()) for x in suppliers)
        restart = False
        subscription_meals = 15
        five_meal_supplier = None
        ten_meal_supplier = None

        while True:
            # Check if two suppliers can be chosen
            if len(bucket[Veestro]) == 15:
                five_meal_supplier = Veestro
                ten_meal_supplier = Veestro
                slots = bucket[Veestro]
                break
            if five_meal_supplier is None:
                if len(bucket[FoodNerd]) == 5:
                    five_meal_supplier = FoodNerd
                elif len(bucket[FrozenGarden]) == 5:
                    five_meal_supplier = FrozenGarden
            if ten_meal_supplier is None:
                if len(bucket[Veestro]) == 10:
                    ten_meal_supplier = Veestro
                elif len(bucket[Euphebe]) == 10:
                    ten_meal_supplier = Euphebe
            if five_meal_supplier and ten_meal_supplier:
                slots = bucket[five_meal_supplier][:5] + bucket[ten_meal_supplier][:10]
                break

            sorted_scores = sorted(score_board.keys(), reverse=True)
            for score in sorted_scores:

                if restart:
                    restart = False
                    break

                for meal in score_board[score]:

                    supplier = meal['meal'].supplier_id
                    if 'breakfast' in meal['meal'].type:
                        continue

                    bucket[supplier].append(meal)
                    # Update score board just for the selected meal
                    score_board[score].remove(meal)
                    new_score = score + constants.REPEAT_ZERO
                    if new_score in score_board.keys():
                        score_board[new_score].append(meal)
                    else:
                        score_board[new_score] = [meal]

                    # Update score board2 - penalize more as more repetition
                    if meal['meal'] in repeat_one_week:
                        num_repeat += 1
                        for score_ in sorted_scores:
                            for repeat in repeat_one_week:
                                for each_meal in score_board[score_]:
                                    if each_meal['meal'] == repeat:
                                        score_board[score_].remove(each_meal)
                                        deduct_pnt = constants.REPEAT_CUM * num_repeat
                                        if score_ + deduct_pnt in score_board.keys():
                                            score_board[score_ + deduct_pnt].append(each_meal)
                                        else:
                                            score_board[score_ + deduct_pnt] = [each_meal]


                    restart = True
                    break

        # slots filled up
        assert len(slots) == subscription_meals

        ## OPTIONAL - how many repetition from past 2 weeks?
        repeat_cnt = 0
        repeat_same_week = {}
        for each in slots:
            if repeat_one_week is not None and each['meal'] in repeat_one_week:
                repeat_cnt += 1
            if each['meal'].name in repeat_same_week.keys():
                repeat_same_week[each['meal'].name] += 1
            else:
                repeat_same_week[each['meal'].name] = 1

        return slots, [five_meal_supplier, ten_meal_supplier]

    def minimize_score(self,
                       current_score,
                       minimize_elements,
                       meal_info,
                       multiplier=list()):
        """
        Very intricate method. The two any() are used to perform
        some kind of rough substring matching. That is motivated by
        the fact that a minimize item might be a substring of a
        meal's ingredient name.

        The following any() performs the same kind of substring
        matching, but also checks the minimize name against the
        precomputed set of multiplier ingredients, those whose
        presence imply an higher deduction


        :param current_score: is the current score value of the meal
        being considered at this iteration
        :param minimize_elements: a dictionary of string:dict. Those
        are the elements that the patient should take in small
        quantities
        :param meal_info: the DB record as it is fetched (dict)
        :param multiplier: a list of string names
        :return: the updated score and the list of minimize
        """
        minimize_list = list()
        multiplier_factor = 1
        multiplier_ingredients = set(multiplier).intersection(set(meal_info.keys()))

        for item_name, min_item in minimize_elements.items():
            item_name = item_name.lower()
            if not isinstance(min_item, dict):
                logger.warning(
                    "Minimize element {} is not of type dict".format(item_name)
                )
                continue

            if any([item_name in k for k in meal_info.keys()]):
                if any([item_name in e for e in multiplier_ingredients]):
                    multiplier_factor = 1.5

                if not isinstance(meal_info[item_name], (float,)) and \
                        not isinstance(meal_info[item_name], int):
                    contain_val = float(meal_info[item_name].split(' ')[0])
                else:
                    contain_val = float(meal_info[item_name])

                if contain_val > float(min_item.get('min2', 0)):
                    current_score += constants.DEDUCT_GR_MIN2 * multiplier_factor
                    minimize_list.append(item_name)
                elif contain_val > float(min_item.get('min1', 0)):
                    current_score += constants.DEDUCT_LT_MIN2 * multiplier_factor
                    minimize_list.append(item_name)
                elif contain_val <= float(min_item.get('min1', 0)):
                    pass
                    """
                    Do we deduct points for {value} < min1 ? No
                    if meal.supplier_id == connectMongo.db.users.find_one(
                    {'first_name':'Veestro'})['_id']:
                        score += DEDUCT_LT_MIN1_VEESTRO*multiplier_factor
                    else:
                        score += DEDUCT_LT_MIN1*multiplier_factor
                    """
                else:
                    raise ValueError(
                        "Error while minimizing score for meal: {}".format(
                            meal_info.get('name'))
                    )

        return current_score, minimize_list

    def value_to_float(self, v):
        try:
            return float(v)
        except ValueError:
            return 0

    def adjust_score_according_to_calories(self, cals_quantity, ref):
        score = 0
        cals_quantity = self.value_to_float(cals_quantity)

        if isinstance(ref, str) and "|" in ref:
            low, up = ref.split("|")
            if cals_quantity > self.value_to_float(up):
                score += constants.ADD_CALORIES * 2
            elif cals_quantity <= self.value_to_float(low):
                score -= constants.DEDUCT_CALORIES
            else:
                score += constants.ADD_CALORIES

        else:
            ref = self.value_to_float(ref)
            if not (cals_quantity or ref):
                return score

            if cals_quantity < ref:
                score -= constants.DEDUCT_CALORIES
            elif cals_quantity >= ref:
                score += constants.ADD_CALORIES
        return score

    def prioritize_score(self, priors, minimize_list, avoid_list, meal, score):
        prior_list = list()
        for elem_name in priors:
            if elem_name in minimize_list + avoid_list:
                continue

            tag_elem_quantity = priors[elem_name]
            if elem_name in meal.ingredients and \
                    tag_elem_quantity <= float(meal.ingredients[elem_name]):
                prior_list.append(elem_name)

            for nutrition, nutrition_quantity in meal.nutrition.items():
                # TODO #1: this behavior should be fixed. either is A IN B
                # or B in A. Usually one of the two information comes from the
                # database, so it can be considered safe

                # TODO #2: since we are using MongoDB, we can play around with dictionaries
                # as long as we want, so instead of saving nutrition fact quantities
                # as strings, they might be saved in this form:
                # {'quantity': float, 'unit': [mcg, gr, ...whatever]}, so that we don't
                # have to retrieve data using awkward method (like split + indexing)
                if (nutrition in elem_name or elem_name in nutrition) and \
                        tag_elem_quantity <= float(nutrition_quantity.split(' ')[0]):
                    prior_list.append(elem_name)
                elif 'calorie' in elem_name and nutrition == 'cals':
                    score += self.adjust_score_according_to_calories(
                        nutrition_quantity,
                        tag_elem_quantity,
                    )

        # TODO: why this line? to avoid duplicates?
        prior_list = list(set(prior_list))
        score += len(prior_list) * constants.ADD_PRIOR

        return score, prior_list

    def repeating_meals(self, patient_id, start_date):
        """
        Check previously ordered meals

        :param patient_id: ObjectId()
        :param start_date: datetime.datetime()
        :return: [Meal()] or None, [Meal()] or None
        """
        last_week_patient_meals, two_weeks_ago_patient_meals = list(), list()
        last_week_order = connectMongo.db.orders.find_one({
            'patient_id':patient_id,
            'week_start_date': start_date - timedelta(weeks=1)
        })
        two_weeks_ago_order = connectMongo.db.orders.find_one({
            'patient_id': patient_id,
            'week_start_date': start_date - timedelta(weeks=2)
        })
        if last_week_order:
            last_week_patient_meals = [
                self.meals.get(x) for x in last_week_order['patient_meal_id']
            ]

        if two_weeks_ago_order:
            two_weeks_ago_patient_meals = [
                self.meals.get(x) for x in two_weeks_ago_order['patient_meal_id']
            ]

        return last_week_patient_meals, two_weeks_ago_patient_meals

    def get_score_board(self, patient):
        """
        create a scoring system based on minimize, avoid and prior tags
        :return: {int : [{'prior':[str], 'minimizes': [str]. 'avoids': [str],
        'meal': Meal()]}, [Meal()]

        # TODO: quantity
        if meal.quantity == 0:
        continue
        """
        logger.info("Started generating score card")
        score_board = dict()
        # get meals from one, two weeks ago to check repetition: repeat_one if one week ago, repeat_two is two weeks ago
        repeat_one_week, repeat_two_week= self.repeating_meals(patient._id, self.today)

        for meal in self.meals.values():
            if self.suppliers and meal.supplier_id not in self.suppliers:
                continue

            score = 100
            avoid_list = list()

            # TODO: is it correct that this loop exits after the first match ?
            for each in list(meal.nutrition.keys()) + list(meal.ingredients.keys()):
                if each in patient.avoid:
                    avoid_list.append(each)
                    score += constants.DEDUCT_AVOID
                    break

            full_meal_info = {}
            full_meal_info.update(meal.ingredients)
            full_meal_info.update(meal.nutrition)

            score, minimize_list = self.minimize_score(
                score, patient.minimize, full_meal_info
            )
            score, prior_list = self.prioritize_score(
                patient.prioritize, minimize_list, avoid_list, meal, score
            )

            # check repetition. deduct for every repetition of meal
            score += sum([
                constants.REPEAT_ONE for repeat_meal in repeat_one_week if repeat_meal == meal])
            score += sum([
                constants.REPEAT_TWO for repeat_meal in repeat_two_week if repeat_meal == meal])

            if score not in score_board.keys():
                score_board[score] = list()

            score_board[score].append({
                'meal': meal,
                'prior': prior_list,
                'minimize': minimize_list,
                'avoid': avoid_list
            })

        return score_board

    def reorder_slots(self,slots):
        '''
        reorder based on calories
        :param slots:[Meal()]
        :return: [Meal()]
        '''
        #sort by calories
        slots = sorted(slots, key = lambda meal: float(meal['meal'].nutrition['cals'].split(' ')[0]),reverse=True)
        high_cal = slots[:7]
        low_cal = slots[8:]
        new_slots = []
        for high,low in zip(high_cal,low_cal[::-1]):
            new_slots.append(high)
            new_slots.append(low)
        new_slots.append(slots[7])
        return new_slots

    def to_mongo(self, meal_info, patient_id, start_date, end_date):
        patient_meal_id = list()
        for meal in meal_info:
            patient_meal = model.Patient_meal(patient_id, meal['meal']._id, 'pending', datetime.today())
            patient_meal_id.append(
                connectMongo.db.patient_meals.insert_one(
                    patient_meal.class_to_dict()
                ).inserted_id
            )
        new_order = model.Order(
            patient_id=patient_id,
            patient_meal_id=patient_meal_id,
            week_start_date=start_date,
            week_end_date=end_date
        )
        connectMongo.db.orders.insert_one(new_order.class_to_dict())

    def write_csv(self, slots, patient_id, start_date):
        import csv
        try:
            existing_order = list(csv.reader(open('masterOrder/masterorder.csv','r')))
        except:
            existing_order = [['Patient_ID','Patient_name','date','meal_name','minimize','prior','avoid','supplier_id','supplier_name']]
        for index in range(len(slots)):
            meal = slots[index]
            user = connectMongo.db.users.find_one({'_id':connectMongo.db.patients.find_one({'_id':patient_id})['user_id']})
            patient_name = user['first_name'] + ' ' + user['last_name']
            supplier_name = connectMongo.db.users.find_one({'_id': meal['meal'].supplier_id})['first_name']

            row = [str(patient_id), patient_name, str(start_date.date()+timedelta(days=index)), meal['meal'].name,\
                   meal['minimize'], meal['prior'], meal['avoid'], meal['meal'].supplier_id, supplier_name]
            existing_order.append(row)
        with open('masterOrder/masterorder.csv','w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(existing_order)
        logger.info("Successfully generated orders to a csv file")

    def scoreboard_to_csv_rows(self, score_board, patient_id):
        """
        TODO: move CSV headers to a constants
        """
        sorted_score = sorted(score_board.keys(), reverse=True)
        csv_list = [[patient_id, 'score', 'meal', 'minimize', 'prior', 'avoid', 'supplier_id','supplier_name'], ]
        user = self.db_client.users.find_one({
            '_id': self.db_client.patients.find_one({'_id':patient_id})['user_id']
        })
        patient_name = "{}.{}".format(user['first_name'], user['last_name'])
        for score in sorted_score:
            for meal in score_board[score]:
                supplier_name = self.db_client.users.find_one({'_id': meal['meal'].supplier_id})['first_name']
                csv_list.append([
                    score,
                    meal['meal'].name,
                    ":".join(meal['minimize']),
                    ":".join(meal['prior']),
                    ":".join(meal['avoid']),
                    meal['meal'].supplier_id,
                    supplier_name
                ])

        return patient_name, csv_list

