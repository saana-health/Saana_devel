import pdb
import itertools
import csv
import os
from datetime import date, timedelta, datetime
from . import model, connectMongo, utils, feedback
from . import manual_input

DEDUCT_AVOID = -60
DEDUCT_GR_MIN2 = -60
DEDUCT_LT_MIN2 = -30
DEDUCT_LT_MIN1 = -15
DEDUCT_LT_MIN1_VEESTRO = - 20

# REPEAT
REPEAT_ZERO = -50
REPEAT_ONE = -30
REPEAT_TWO = -15
REPEAT_CUM = - 5

# PLUS
ADD_PRIOR = 10

try:
    os.remove('masterOrder/masterorder.csv')
except:
    pass

TEST = True

TODAY = utils.find_tuesday(date.today(),2)

class Optimizer:

    def __init__(self, test = True):
        '''
        meals: {_id: Meal()}
        tags: {_id: Tag()}
        # inventory:  ?
        patients: [Patient()]
        today: datetime.datetime()
        '''
        self.today = datetime.combine(TODAY,datetime.min.time())
        # check today is tuesday
        assert self.today.weekday() == 1
        self.test = test
        self.meals = self._get_meals()
        self.tags = self._get_tags()
        self.patients = self._get_patients()

    def _get_meals(self):
        '''
        gets all meals in db in {_id:Meal(object)} structure

        :return: {_id: Meal()}
        '''
        map_meal = {}
        meals_dict= list(connectMongo.db.meal_infos.find())
        for temp in meals_dict:
            ingredients = {}
            for ingredient in temp['ingredients']:
                name = connectMongo.db.mst_food_ingredients.find_one({'_id':ingredient['food_ingredient_id']})['name']
                ingredients[name] = ingredient['quantity']
            temp['ingredients'] = ingredients
            new_meal = model.Meal()
            new_meal.dict_to_class(temp)
            map_meal[temp['_id']] = new_meal#utils.meal_dict_to_class(temp)
        return map_meal

    def _get_tags(self):
        '''
        Gets all tags

        :return: {_id: Tag()}
        '''
        hash_tag = {}
        tags = list(connectMongo.db.tags.find())
        for tag in tags:
            new_tag = model.Tag()
            new_tag.dict_to_class(tag)
            hash_tag[tag['_id']] = new_tag
        return hash_tag

    def _get_patients(self):
        '''
        Get all patients

        :return: [Patient()]
        '''
        patient_obj = []
        patients = connectMongo.db.patients.find()
        for patient in patients:
            # Skip if subscription is not active or not order cycle
            if not self._check_subscription(patient['_id']):
                continue
            comorbidities = connectMongo.get_comorbidities(patient['_id'])
            disease = connectMongo.get_disease(patient['_id'])
            symptoms = connectMongo.get_symptoms(patient['_id'])
            drugs = connectMongo.get_drugs(patient['_id'])
            user_id = connectMongo.db.patients.find_one({'_id':patient['_id']})['user_id']
            name = connectMongo.db.users.find_one({'_id':user_id})['first_name']

            new_patient = model.Patient(name=name,comorbidities=comorbidities, disease=disease, _id = patient['_id'],\
                                  symptoms=symptoms, treatment_drugs=drugs)
            patient_obj.append(new_patient)

        return patient_obj

    def _check_subscription(self, patient_id):
        '''
        Checks subscription status

        :param patient_id: ObjectId()
        :return: True / False
        '''
        if self.test:
            return True

        patient_subscription = connectMongo.db.patient_subscriptions.find_one({'patient_id':patient_id})
        # No subscription
        if patient_subscription is None:
            return False

        # Inactive status
        if patient_subscription['status'] != 'active':
            return False

        # Weekly order
        if connectMongo.db.mst_subscriptions.find_one({'_id':patient_subscription['subscription_id']})['interval_count']\
            == 1:
            return True

        # order if not ordered last week
        order_lastWeek = connectMongo.db.orders.find_one({'patient_id':patient_id, 'week_start_date':self.today + timedelta(weeks=-1)})
        if order_lastWeek is None:
           return True
        else:
            return False

    def optimize(self, test = True):
        '''
        optimize -> get_sscre_board -> choose_meal -> to_mongo & write_csv
        :return:
        '''
        for patient in self.patients:
            # plan either 7 or 15
            num_meal = connectMongo.get_subscription(patient._id)

            ## deprecated
            # patient.next_order = connectMongo.get_next_order(patient._id)

            today = self.today
            start_date = today

            print('Processing   {}  on {}!'.format(patient.name,str(today)))
            score_board = {}

            # get all tags
            tag_ids = patient.symptoms+patient.disease+patient.treatment_drugs+patient.comorbidities
            tags = list(connectMongo.db.tags.find({'tag_id':{'$in':tag_ids}}))

            # prepare tags
            minimizes = {}
            priors = {}
            multiplier = []
            symptoms_progress = feedback.get_lateset_symptoms(patient._id)
            for tag in tags:
                minimizes.update(tag['minimize'])
                priors.update(tag['prior'])
                if tag['tag_id'] in symptoms_progress['worsen']:
                    multiplier += list(tag['minimize'].keys())+list(tag['prior'].keys())
                    print(1)


            avoids = list(set(itertools.chain(*[utils.tag_dict_to_class(tag).avoid for tag in tags])))

            ## Get scoreboard ##
            score_board, repeat_one_week = self.get_score_board(patient, minimizes, avoids, priors, list(set(multiplier)))
            self.scoreboard_to_csv(score_board,patient._id)

            ## Start choosing meals ##
            slots = self.choose_meal(score_board, repeat_one_week)
            assert len(slots) == 15
            slots = self.reorder_slots(slots)

            # Save the result to csv and update on mongo
            if num_meal> 8:
                end_date = utils.find_tuesday(start_date,2)
                self.to_mongo(slots,patient._id,start_date,end_date)
                self.write_csv(slots,patient._id,start_date,end_date)
            else:
                end_date = utils.find_tuesday(start_date,3)
                self.to_mongo(slots, patient._id,start_date,end_date)
                self.write_csv(slots,patient._id,start_date,end_date)

    def get_score_board(self, patient, minimizes, avoids, priors, multiplier):
        '''
        create a scoring system based on minimize, avoid and prior tags

        :param patient: Patient()
        :param minimizes: {str: {min1: str(int), min2: str(int)} }
        :param avoids: [ str ]
        :param priors: { str: int}
        :return: {int : [{'prior':[str], 'minimizes': [str]. 'avoids': [str], 'meal': Meal()]}, [Meal()]
        '''
        # get meals from one, two weeks ago to check repetition: repeat_one if one week ago, repeat_two is two weeks ago
        repeat_one_week, repeat_two_week= self._repeating_meals(patient._id,self.today)
        score_board = {}

        for meal in self.meals.values():
            # skip meal if not from suppliers we want
            if meal.supplier_id not in manual_input.manual_input('suppliers.csv')[0]:
                continue

            score = 100
            # TODO: quantity
            # if meal.quantity == 0:
            #     continue

            # arrays for storing matched contents
            avoid_list = []
            minimize_list = []
            prior_list = []

            ## AVOID ##
            # avoid_list is avoid tags that MATCHED
            for each in list(meal.nutrition.keys()) + list(meal.ingredients.keys()):
                if each in avoids:
                    avoid_list.append(each)
                    score += DEDUCT_AVOID
                    break

            ## MINIMIZE ##
            full_meal_info = {}
            full_meal_info.update(meal.ingredients)
            full_meal_info.update(meal.nutrition)

            # minimizes: list of all ingredients+nutrition to minimize from tags
            # full_meal_info: from meal info
            for min_item in minimizes.keys():
                for ing in full_meal_info.keys():
                    # if matched
                    if min_item in ing:
                        multiplier_factor = 1

                        if ing in multiplier:
                            multiplier_factor = 1.5

                        # If a unit is included in the value, get rid of it
                        if not isinstance(full_meal_info[ing],(float,)) and not isinstance(full_meal_info[ing],int):
                            contain_val = float(full_meal_info[ing].split(' ')[0])
                        else:
                            contain_val = float(full_meal_info[ing])

                        # if (val > min2)
                        if contain_val > float(minimizes[min_item]['min2']):
                            score += DEDUCT_GR_MIN2*multiplier_factor
                        # if (min1 < val < min2)
                        elif contain_val > float(minimizes[min_item]['min1']):
                            score += DEDUCT_LT_MIN2*multiplier_factor
                        #if (val < min1)
                        elif contain_val < float(minimizes[min_item]['min1']):
                            if meal.supplier_id == connectMongo.db.users.find_one({'first_name':'Veestro'})['_id']:
                                score += DEDUCT_LT_MIN1_VEESTRO*multiplier_factor
                            else:
                                score += DEDUCT_LT_MIN1*multiplier_factor
                        # This should never happen
                        else:
                            print('ERR')
                            raise ValueError
                        minimize_list.append(min_item)

            ## PRIORITIZE
            ## DELETE this line if I see again
            # prior_list = [{nutrition: meal.nutrition[nutrition]} for nutrition in meal.nutrition if nutrition in priors]
            for prior in priors.keys():
                # if 1) string matched 2) not in min or avoid list and 3) content value above threshold
                for ingredient in meal.ingredients.keys():
                    if prior in ingredient and prior not in minimize_list + avoid_list and priors[prior] <= float(meal.ingredients[ingredient]):
                        prior_list.append(prior)
                for nutrition in meal.nutrition.keys():
                    if (nutrition in prior or prior in nutrition) and prior not in minimize_list + avoid_list and priors[prior] <= float(meal.nutrition[nutrition].split(' ')[0]):
                        prior_list.append(prior)
            prior_list = list(set(prior_list))

            # ADD points for priors
            pos = len(prior_list)
            score += pos*ADD_PRIOR

            ## REPETITION
            # check repetition. deduct for every repetition of meal
            for repeat_meal in repeat_one_week:
                if meal == repeat_meal:
                    score += REPEAT_ONE
            for repeat_meal in repeat_two_week:
                if meal == repeat_meal:
                    score += REPEAT_TWO

            # update the score_board
            if score not in score_board.keys():
                score_board[score] = [{'meal': meal,'prior':prior_list,'minimize':minimize_list, 'avoid':avoid_list}]
            else:
                score_board[score].append({'meal': meal,'prior':prior_list,'minimize':minimize_list, 'avoid':avoid_list})

        return score_board, repeat_one_week

    def choose_meal(self,score_board,repeat_one_week):
        '''
        Choosing meals
        :param score_board:  {int : [{'prior':[str], 'minimizes': [str]. 'avoids': [str], 'meal': Meal()]}
        :param repeat_one_week: [Meal()]
        :return: [Meal()]
        '''

        # list for saving meals
        num_repeat = 0
        bucket = {}
        suppliers = list(connectMongo.db.users.find({'role':'supplier'}))

        # manual matching suppliers with their ID (ObjectId)
        Veestro = [obj['_id'] for obj in suppliers if obj['first_name'] == 'Veestro'][0]
        Euphebe = [obj['_id'] for obj in suppliers if obj['first_name'] == 'Euphebe'][0]
        FoodNerd = [obj['_id'] for obj in suppliers if obj['first_name'] == 'FoodNerd'][0]
        FrozenGarden = [obj['_id'] for obj in suppliers if obj['first_name'] == 'FrozenGarden'][0]

        for supplier in [x['_id'] for x in suppliers]:
            bucket[supplier] = []
        restart = False
        num_meal = 15
        five_meal_supplier = None
        ten_meal_supplier = None

        while True:

            # Check if two suppliers can be chosen
            if len(bucket[Veestro]) == 15:
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
            if None not in [five_meal_supplier, ten_meal_supplier]:
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
                    try:
                        bucket[supplier].append(meal)
                    except:
                        pdb.set_trace()

                    # Update score board for meal just selected
                    score_board[score].remove(meal)
                    new_score = score + REPEAT_ZERO
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
                                        deduct_pnt = REPEAT_CUM*num_repeat
                                        if score_ + deduct_pnt in score_board.keys():
                                            score_board[score_ + deduct_pnt].append(each_meal)
                                        else:
                                            score_board[score_ + deduct_pnt] = [each_meal]


                    restart = True
                    break

        # slots filled up
        assert len(slots) == num_meal

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
        # print('{} repetitions from last week'.format(repeat_cnt))

        return slots

    def _repeating_meals(self,patient_id,start_date):
        '''
        Check previously ordered meals

        :param patient_id: ObjectId()
        :param start_date: datetime.datetime()
        :return: [Meal()] or None, [Meal()] or None
        '''
        # prev_order = connectMongo.get_order(patient_id,start_date + timedelta(weeks=-1))
        prev_order = connectMongo.db.orders.find_one({'patient_id':patient_id, 'week_start_date': start_date + timedelta(weeks=-1)})
        prev_two_order = connectMongo.db.orders.find_one({'patient_id':patient_id, 'week_start_date': start_date + timedelta(weeks=-2)})

        if prev_order is not None:
            # for catching errors
            try:
                prev_order = [self.meals[x] for x in prev_order['patient_meal_id']]
            except:
                pdb.set_trace()
        else:
            prev_order = []

        if prev_two_order is not None:
            prev_two_order = [self.meals[x] for x in prev_two_order['patient_meal_id']]
        else:
            prev_two_order = []

        return prev_order, prev_two_order

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

    def to_mongo(self, mealinfo, patient_id,start_date,end_date):
        patient_meal_id = []
        for meal in mealinfo:
            patient_meal = model.Patient_meal(patient_id, meal['meal']._id, 'pending', datetime.today())
            return_id = connectMongo.db.patient_meals.insert_one(patient_meal.class_to_dict()).inserted_id
            patient_meal_id.append(return_id)
        new_order = model.Order(patient_id = patient_id,patient_meal_id = patient_meal_id,\
                          week_start_date=start_date, week_end_date=end_date)
        connectMongo.db.order.insert_one(new_order.class_to_dict())
        return True

    def write_csv(self,slots,patient_id,start_date,end_date):
        try:
            existing_order = list(csv.reader(open('masterOrder/masterorder.csv','r')))
        except:
            existing_order = [['ID','date','meal_name','minimize','prior','avoid','supplier']]
        for index in range(len(slots)):
            meal = slots[index]
            row = [str(patient_id)[-5:],str(start_date.date()+timedelta(days=index)),meal['meal'].name,\
                   meal['minimize'],meal['prior'],meal['avoid'],meal['meal'].supplier_id]
            existing_order.append(row)
        with open('masterOrder/masterorder.csv','w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(existing_order)

    def scoreboard_to_csv(self,score_board,patient_id):
        '''
        Save score_board to csv
        :param score_board: {int : [{'prior':[str], 'minimizes': [str]. 'avoids': [str], 'meal': Meal()]},
        :param patient_id: ObjectId()
        :return: True
        '''
        sorted_score = sorted(score_board.keys(),reverse = True)
        csv_list = [[patient_id],['score','meal','minimize','prior','avoid','supplier_id']]
        for score in sorted_score:
            for meal in score_board[score]:
                temp_list = [score]
                temp_list += [meal['meal'],meal['minimize'],meal['prior'], meal['avoid'],meal['meal'].supplier_id]
                csv_list.append(temp_list)
        with open('scoreboard/scoreboard_'+str(patient_id)[-5:]+'_'+str(self.today.date())+'.csv','w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_list)
        return True



if __name__ == "__main__":

    ## CAUTION: ALWAYS ADD NUMBERS IN CODE AS THEIR VALUES ARE NEGATIVES
    # MINUS

    op = Optimizer()
    op.optimize(TEST)


