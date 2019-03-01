from pymongo import MongoClient
from bson.objectid import ObjectId
import pdb
import itertools
from model import Meal,MealHistory, MealList
import csv
from connectMongdo import add_meal_history,find_meal, get_all_meals, get_mealinfo_by_patient, get_all_tags, get_all_patients
from random import shuffle
import os
from utils import meal_dict_to_class, tag_dict_to_class

class Optimizer:

    def __init__(self, week):
        self.meals = None
        self.tags = None
        self.inventory = None
        self.week = week

    def _get_meals(self):
        '''

        :return: {_id: Meal()}
        '''
        hash_meal = {}
        meals = [meal for meal in get_all_meals()]
        for meal in meals:
            hash_meal[meal['_id']] = meal_dict_to_class(meal)
        self.meals = hash_meal

    def _get_tags(self):
        '''

        :return: {_id: Tag()}
        '''
        hash_tag = {}
        tags = [tag for tag in get_all_tags()]
        for tag in tags:
            hash_tag[tag['_id']] = tag_dict_to_class(tag)
        self.tags = hash_tag

    def _get_patients(self):
        '''

        :return: [Patient()]
        '''
        self.patients = get_all_patients()


    def optimize(self):
        pass

    def _update_mealinfo(self):
        '''

        :return: True/False
        '''
        pass


if __name__ == "__main__":
    op = Optimizer(week = 1)
    op._get_tags()

