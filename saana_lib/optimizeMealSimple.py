## Main Optimization script ##
# Pared down version for only generating a scorecard 

import itertools
import csv
import os
import sys
from datetime import date

from . import model, connectMongo, utils, feedback, manual_input

## Preset point values ##

# Deductions
DEDUCT_AVOID = -60
DEDUCT_GR_MIN2 = -60
DEDUCT_LT_MIN2 = -30
DEDUCT_LT_MIN1 = -15
DEDUCT_LT_MIN1_VEESTRO = - 20

# Additions
ADD_PRIOR = 10
LIKED_MEAL = 10

# ?
TEST = True


## Define Optimization Object and Functions

class Optimizer:

    def __init__(self, test = True):
        '''
        meals: {_id: Meal()}
        tags: {_id: Tag()}
        patients: [Patient()]
        '''
        print("Started initializing Optimizer Object")
        self.test = test
        self.today = date.today()
        self.meals = self._get_meals()
        self.tags = self._get_tags()
        self.patients = self._get_patients()
        print("Finished initializing Optimizer Object")

    def _get_meals(self):
        '''
        gets all meals in db in {_id:Meal(object)} structure
        :return: {_id: Meal()}
        '''
        print("Started getting meals from DB")
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
            map_meal[temp['_id']] = new_meal
        print("Started getting meals from DB")
        return map_meal

    def _get_tags(self):
        '''
        Gets all tags
        :return: {_id: Tag()}
        '''
        print("Started getting tags from DB")
        hash_tag = {}
        tags = list(connectMongo.db.tags.find())
        for tag in tags:
            new_tag = model.Tag()
            new_tag.dict_to_class(tag)
            hash_tag[tag['_id']] = new_tag
        print("Finished getting tags from DB")
        return hash_tag

    def _get_patients(self):
        '''
        Get all patients
        :return: [Patient()]
        '''
        print("Started getting patients from DB")
        patient_obj = []
        
        # if selecting patients based on emails read in from manual file
        # if no emails are specified -> run on all patients 
        patients = connectMongo.db.patients.find()
        emails = manual_input.manual_input('suppliers.csv')[1]
        for patient in patients:
            if emails != []:
                user = connectMongo.db.users.find_one({'_id':patient['user_id']})
                # if emails specified but not matched
                try:
                    if connectMongo.db.users.find_one({'_id':patient['user_id']})['email'] not in emails:
                        continue
                except:
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
        print("Finished getting patients")
        return patient_obj

    
    # meal ranking functions

    def optimize(self):
        '''
        optimize -> get_score_board -> choose_meal -> to_mongo & write_csv
        :return:
        '''
        for patient in self.patients:
            try:

                print('Processing   {}!'.format(patient.name))

                score_board = {}

                # get all tags
                tag_ids = patient.symptoms + patient.disease + patient.treatment_drugs + patient.comorbidities
                tags = list(connectMongo.db.tags.find({'tag_id':{'$in':tag_ids}}))
                print('tags:', tags)

                # prepare tags
                minimizes = {}
                priors = {}
                multiplier = []
                for tag in tags:
                    minimizes.update(tag['minimize'])
                    priors.update(tag['prior'])

                avoids = list(set(itertools.chain(*[utils.tag_dict_to_class(tag).avoid for tag in tags])))

                print("Finished annotating tags")

                ## Get scoreboard ##
                score_board = self.get_score_board(patient, minimizes, avoids, priors) 
                self.scoreboard_to_csv(score_board,patient._id) #### CURRENTLY #####

                print('Finished processing   {}'.format(patient.name))

            except:
                print('Error while generating meals for {}'.format(patient.name))

    def get_score_board(self, patient, minimizes, avoids, priors):
        '''
        create a scoring system based on minimize, avoid and prior tags
        :param patient: Patient()
        :param minimizes: {str: {min1: str(int), min2: str(int)} }
        :param avoids: [ str ]
        :param priors: { str: int}
        :return: {int : [{'prior':[str], 'minimizes': [str]. 'avoids': [str], 'meal': Meal()]}, [Meal()]
        '''
        print("Started generating score card")
        score_board = {}

        for meal in self.meals.values():
            # skip meal if not from suppliers we want
            suppliers = manual_input.manual_input('suppliers.csv')[0]
            if suppliers != [] and meal.supplier_id not in suppliers:
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

                        # If a unit is included in the value, get rid of it
                        if not isinstance(full_meal_info[ing],(float,)) and not isinstance(full_meal_info[ing],int):
                            contain_val = float(full_meal_info[ing].split(' ')[0])
                        else:
                            contain_val = float(full_meal_info[ing])

                        # if (val > min2)
                        if contain_val > float(minimizes[min_item]['min2']):
                            score += DEDUCT_GR_MIN2*multiplier_factor
                            minimize_list.append(min_item)
                        # if (min1 < val < min2)
                        elif contain_val > float(minimizes[min_item]['min1']):
                            score += DEDUCT_LT_MIN2*multiplier_factor
                            minimize_list.append(min_item)
                        #if (val < min1)
                        elif contain_val <= float(minimizes[min_item]['min1']):
                            pass
                            # Do we deduct points for {value} < min1 ? No
                            # if meal.supplier_id == connectMongo.db.users.find_one({'first_name':'Veestro'})['_id']:
                            #     score += DEDUCT_LT_MIN1_VEESTRO*multiplier_factor
                            # else:
                            #     score += DEDUCT_LT_MIN1*multiplier_factor
                        # This should never happen
                        else:
                            print('ERR')
                            raise ValueError

            ## PRIORITIZE
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

            # update the score_board
            if score not in score_board.keys():
                score_board[score] = [{'meal': meal,'prior':prior_list,'minimize':minimize_list, 'avoid':avoid_list}]
            else:
                score_board[score].append({'meal': meal,'prior':prior_list,'minimize':minimize_list, 'avoid':avoid_list})

        print("Finished generating score card")
        return score_board


    def scoreboard_to_csv(self,score_board,patient_id):
        '''
        Save score_board to csv
        :param score_board: {int : [{'prior':[str], 'minimizes': [str]. 'avoids': [str], 'meal': Meal()]},
        :param patient_id: ObjectId()
        :return: True
        '''
        sorted_score = sorted(score_board.keys(),reverse = True)
        csv_list = [[patient_id],['score','meal','minimize','prior','avoid','supplier_id','supplier_name']]
        user = connectMongo.db.users.find_one({'_id':connectMongo.db.patients.find_one({'_id':patient_id})['user_id']})
        patient_name = user['first_name'] + '.' + user['last_name']
        for score in sorted_score:
            for meal in score_board[score]:
                supplier_name = connectMongo.db.users.find_one({'_id': meal['meal'].supplier_id})['first_name']
                temp_list = [score]
                temp_list += [meal['meal'],meal['minimize'],meal['prior'], meal['avoid'],meal['meal'].supplier_id,supplier_name]
                csv_list.append(temp_list)
        with open('scoreboard/scoreboard_'+str(patient_name)+'_'+str(self.today)+'.csv','w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_list)
        print("Successfully wrote score card to a csv file")
        return True

if __name__ == "__main__":

    ## CAUTION: ALWAYS ADD NUMBERS IN CODE AS THEIR VALUES ARE NEGATIVES
    # MINUS

    op = Optimizer()
    op.optimize(TEST)

