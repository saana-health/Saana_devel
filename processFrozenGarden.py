import csv
import pickle
import pprint
import pdb
import os
from model import Meal
from difflib import SequenceMatcher
from connectMongdo import add_meals
from utils import unicodetoascii
import re

PATH = os.path.join(os.getcwd(),'csv/frozenGarden/')

def similar(a,b):
    return SequenceMatcher(None,a,b).ratio() > 0.76

def processNutrition(filename):
    '''

    :param filename:
    :return:
    '''
    convert_dic = {}

    columns = []
    with open(filename) as csvfile:
        ingredients = {}
        nutritions = {}
        all_contents = []

        reader_list = list(csv.reader(csvfile))
        columns = [x.strip().lower() for x in reader_list[3]]
        for each in columns:
            print(unicodetoascii(each))
        # columns = [x.strip().lower().replace('\\xc2\\xac\\xc2\\xb','n') if '\\xc2\\xac\\xc2\\xb' in x else x.strip().lower() for x in list(reader_list[3])]

        pdb.set_trace()

        units = [re.search('\(.{0,3}\)',columns[y]).group()[1:-1] if re.search('\(.{0,3}\)',columns[y]) else '' for y in range(len(columns))]
        for i in range(len(columns)):
            name = columns[i].replace(' ('+units[i]+')','')
            columns[i] = name


if __name__ == "__main__":
    for filename in os.listdir(PATH):
        if filename[0] != '.':
            print(filename)
            processNutrition(PATH+filename)
