
import time
import string
from nltk.corpus import wordnet
from pattern.text.en import singularize, pluralize
from pint import UnitRegistry
ureg = UnitRegistry()
import sqlite3 as lite
con = lite.connect('db')
from fractions import Fraction
from os import listdir
from os.path import isfile, join
from context_extractor import *
from compare_ingredients import *
from images import *
from collections import OrderedDict
from pymongo import MongoClient
from urllib.parse import quote_plus
import conf
import simplejson as json


client = MongoClient('mongodb://{}:{}@{}'.format(
    quote_plus(conf.DATABASE_USER),
    quote_plus(conf.DATABASE_PASSWORD),
    quote_plus(conf.DATABASE_ADDRESS),
), authSource='saana_db')

db = client.saana_db


##client = MongoClient('mongodb://localhost:27017')

recipe_db = db.mst_recipes


##r = requests.get(url)
##html = r.text
##soup = BeautifulSoup(html, "html5lib")
##links = soup.find_all('img')
##print links
##if links:
##    print(links[0]['src'])
##    print(links[1]['src'])
##    print(links[2]['src'])
##    

nutrientCategory = {}
nutrientCategoryNum = {}
nutrientData = OrderedDict()


def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)
  
  
def getMixedFraction(flt):
  while True:
    fractionString = str(Fraction(flt).limit_denominator(8))
    if '/' in fractionString:
      fractionNums = str(Fraction(flt).limit_denominator(8)).split('/')
      num = int(fractionNums[0])
      if '8' in fractionNums[1] or '4' in fractionNums[1] or '3' in fractionNums[1]:
        den = int(fractionNums[1])
        if num<den:
          return str(num) + "/" + str(den)
        else:
          return str(num/den) + " " + str(num-den*(num/den)) + "/" + str(den)
      else:
        flt = flt - 0.05
    else:
      return str(round(flt))
    
def getFoodFromDatabase(sentence,nutrition):
  # Remove things in parentheses

  regEx = re.compile(r'([^\(]*)\([^\)]*\) *(.*)')
  m = regEx.match(sentence)
  while m:
    sentence = m.group(1) + m.group(2)
    m = regEx.match(sentence)
  
  sentence = sentence.lower()
  sentence = sentence.replace('-',' ')
  sentence = sentence.replace(' or ',' ')
  sentence = sentence.replace(' and ',' ')
  sentence = sentence.replace(' to ',' ')
  sentence = sentence.replace(' for ',' ')
  sentence = sentence.replace('white sugar','granulated sugar')
  sentence = sentence.replace('(','')
  sentence = sentence.replace(')','')
  sentence = sentence.replace('about','')
  sentence = sentence.replace('and/or','')
  sentence = sentence.replace('/','slashslash')
  # Remove puncuation
  exclude = set(string.punctuation)
  sentence = ''.join(ch for ch in sentence if ch not in exclude)
  sentence = sentence.replace('slashslash','/')
  words = sentence.split()

  for i in range(len(words)):
    if words[i][-1] == 's':
      words[i] = singularize(words[i])
    if '/' in words[i]:
      words[i]=str(ureg.parse_expression(words[i]))

  #print "sentence '"+sentence+"'"
  #print "The words: ", 
  #print words
  
  # Determine which words are ingredients and which are measurements (quantities)
  foodWords = [False]*len(words)
  measurementWords = [False]*len(words)
  quantityExpression = "none"
  measurementString = "dimensionless" #normally calculated after
  price = 0 #normally defined after
  ingredientdescription = ""
  ingredient = ""
  ingredientArray = []
  measure = ""
  quantity = ""
  ingredient_list_item = {}
  ingredient_list_item_fullid = {}
  
  for i in range(len(words)):
    synsets = wordnet.synsets(words[i])
    
    try:
      foo = ureg.parse_expression(words[i])
      measurementWords[i] = True
    except:
      pass
     
    for synset in synsets:
      if "none" in quantityExpression and hasNumbers(words[i]):
        quantityExpression = words[i] + ' dimensionless'
        quantity = words[i]
        
      if i>0 and 'quantity' in synset.lexname() and hasNumbers(words[i-1]):
        quantityExpression = words[i-1] + " " + words[i]
        measurementWords[i] = True
        measurementWords[i-1] = True
        measurementString = words[i] #normally calculated after
        measure = words[i]
        quantity = words[i-1]
        
      if 'color' in synset.lexname() or 'food' in synset.lexname() or 'plant' in synset.lexname():  ## should be uncommented
        
        if not measurementWords[i]:
          foodWords[i] = True
          ##ingredient += " " + words[i]
      if i>1 and 'quantity' in synset.lexname() and hasNumbers(words[i-1]) and hasNumbers(words[i-2]):
        quantityExpression = words[i-2] + " " + words[i-1] + " " + words[i]
        measure = words[i]
        quantity = words[i-2] + " " + words[i-1]
        measurementWords[i] = True
        measurementWords[i-1] = True
        measurementWords[i-2] = True

  for i in range(len(measurementWords)):
      if measurementWords[i] == False:
          ingredientdescription += " " + words[i]
  for i in range(len(foodWords)):
      if foodWords[i] == True:
          ingredient += words[i] + " "
  
  ingredient_list_item['ingredient_full_name'] = ingredientdescription
  ingredient_list_item['ingredient'] = ingredient
  ingredient_list_item['quantity'] = quantity
  ingredient_list_item['unit'] = measure
  ingredient_list_item['food_ingredient_id'] = get_ingredient_highest(ingredient) ##with ingredient id from db  
  
  # Figure out the grams
  tryToFindAnotherMeasure = False
  try:
    foodGrams = ureg.parse_expression(quantityExpression).to(ureg.grams)
  except:
    try:
      mills = ureg.parse_expression(quantityExpression).to(ureg.milliliters)
      foodGrams = mills.magnitude*ureg.grams
      tryToFindAnotherMeasure = True
    except:
      try:
        foodGrams = float(quantityExpression[0])*ureg.dimensionless
      except:
        foodGrams = 1*ureg.dimensionless
  #print foodGrams

  
  # Generate some food search strings using the food words and the words around the food words
  possibleWords = []
  # Fixes
  if "baking" in words and "powder" in words:
    possibleWords.append('baking* NEAR/3 powder*')
  for i in range(len(words)):
    if i>0 and foodWords[i]:
      if not measurementWords[i-1]:
        possibleWords.append(words[i-1] + '* NEAR/3 ' + words[i] + '*')
    if i<len(foodWords)-1 and foodWords[i]:
      if not measurementWords[i+1]:
        possibleWords.append(words[i] + '* NEAR/3 ' + words[i+1] + '*')
  for i in range(len(foodWords)):
    if foodWords[i]:
      possibleWords.append(words[i] + '*')
    
  #print possibleWords
  return (ingredient_list_item)
##  foundMatch = False
##  shrt_desc = "No match"
##  ndb_no = '-1'
  #print nutrition  
  
##  with con: ## should not be commented but no db
##    cur = con.cursor()    
##    for possibleWord in possibleWords:
##      if not foundMatch:
##        if 'baking' in possibleWord and 'soda' in possibleWord:
##          possibleWord = possibleWord.replace('baking','sodium')
##          possibleWord = possibleWord.replace('soda','bicarbonate')
##
##        cur.execute('select ndb_no,long_desc,com_desc,length(com_desc)-length("'+possibleWord.replace('*','').split()[0] + '") as closest from data where com_desc match "' + possibleWord.replace('*','') + '" order by closest')
##
##        row = cur.fetchone()
##        if row is not None:
##          ndb_no =  row[0].encode('utf-8')
##          shrt_desc = row[1].encode('utf-8')
##          com_desc = row[2].encode('utf-8')
##          foundMatch = True
##          break
##    # search the google hits simultaneously   
##    if not foundMatch:
##      for possibleWord in possibleWords:
##        cur.execute('select c.ndb_no,shrt_desc,google_hits,length(long_desc)-length("'+possibleWord.replace('*','').split()[0] + '") as closest from ranking as r join data as c on r.ndb_no=c.ndb_no where long_desc match "'+possibleWord+'" order by google_hits desc')
##
##        row = cur.fetchone()
##        if row is not None:
##          ndb_no =  row[0].encode('utf-8')
##          shrt_desc = row[1].encode('utf-8')
##          foundMatch = True
##          break
##
##    if foundMatch:
##      cur.execute('select price from food_des where ndb_no like "'+ndb_no+'"')
##      row = cur.fetchone()
##      try:
##        price =  float(row[0])
##      except:
##        price = 0
##
##  if not foundMatch:
##    return ('No match','',quantityExpression,1,nutrition,0)
##  
##  # Now that you have the food but not a good measurement (cups, etc.) try to match one in the table
##  if tryToFindAnotherMeasure:
##    with con:
##      cur.execute('select ndb_no,amount,msre_desc,gm_wgt from weight where ndb_no like "'+ndb_no+'"')
##      rows = cur.fetchall()
##      for row in rows:
##        try:
##          if ureg.parse_expression(quantityExpression).dimensionality == ureg.parse_expression(row[2]).dimensionality:
##            foo = ureg.parse_expression(quantityExpression).to(ureg.parse_expression(row[2]))
##            foodGrams = foo.magnitude * row[3] * ureg.grams
##            break
##        except:
##          pass
##  # Get an appropriate measurement from weights table, or if there is no grams assigned, pick something from the weights table
##  measurementString = "1 dimensionless"
##  measurementAmount = 1
##  with con:
##    cur.execute('select ndb_no,amount,msre_desc,gm_wgt,abs(gm_wgt-'+str(foodGrams.magnitude)+') as diff from weight where ndb_no like "'+ndb_no+'" order by diff')
##    row = cur.fetchone()
##    if row is not None and len(row)>3:    
##      print len(row)
##      print foodGrams
##      if str(foodGrams.dimensionality)=='dimensionless':
##        measurementAmount = float(row[1]) * float(foodGrams.magnitude)
##        foodGrams = (measurementAmount*float(row[3]))*ureg.grams
##        measurementString = getMixedFraction(measurementAmount) + ' ' + row[2]
##      else:
##        measurementAmount = float(foodGrams.magnitude) / (float(row[1]) * float(row[3]))
##        measurementString = getMixedFraction(measurementAmount)  + ' ' + row[2]
##
##  
##  # Get nutrition
##  nutrition = getNutrition(ndb_no,foodGrams.magnitude/100.0,nutrition)
  

    
def getNutrition(foodId,multiplier,nutrition):
  global nutrientData
  with con:
      
    cur = con.cursor()    

    cur.execute('select nutr_no,nutr_val from nutrition_data where ndb_no match "'+foodId+'"')
    
    rows = cur.fetchall()
    
    for row in rows:
      id = int(row[0])
      val = float(row[1])
      cur2 = con.cursor() 
      cur2.execute('select units,NutrDesc,sr_order from nutr_def where nutr_no == "'+str(id)+'" order by sr_order')
      rows2 = cur2.fetchone()
      units = rows2[0]
      name = rows2[1]
      if ord(units[0])==65533:
        units = 'microgram'
      if units == 'IU':
        units = 'dimensionless'
      if name in nutrition.keys():
        nutrition[name.encode('utf-8')] = str(val*ureg.parse_expression(units)+ureg.parse_expression(nutrition[name.encode('utf-8')]))
      else:
        nutrition[name.encode('utf-8')] =str(val*ureg.parse_expression(units))
      if name not in nutrientCategory: 
        c = int(rows2[2])
        nutrientCategoryNum[name]=c
        if c < 1600:
          nutrientCategory[name] = 'Main'
        elif c < 5300:
          nutrientCategory[name] = 'Sugars'
        elif c < 6300:
          nutrientCategory[name] = 'Metals'
        elif c < 9700:
          nutrientCategory[name] = 'Vitamins'
        elif c < 15700:
          nutrientCategory[name] = 'Fatty Acids'
        elif c < 16300:
          nutrientCategory[name] = 'Steroids'
        elif c < 18200:
          nutrientCategory[name] = 'Amino acids'
        elif c < 18500:
          nutrientCategory[name] = 'Other'
      if nutrientCategory[name] not in nutrientData:
        nutrientData[nutrientCategory[name]] = {}
      try:
        if "Energy" in name:
          nutrientData[nutrientCategory[name]][name.encode('utf-8')]=ureg.parse_expression(nutrition[name.encode('utf-8')]).to(ureg.kilocalories).magnitude
        else:
          nutrientData[nutrientCategory[name]][name.encode('utf-8')]=ureg.parse_expression(nutrition[name.encode('utf-8')]).to(ureg.grams).magnitude
      except:
        nutrientData[nutrientCategory[name]][name.encode('utf-8')]=ureg.parse_expression(nutrition[name.encode('utf-8')]).magnitude
      
    
  return nutrition
      
        
  
def extract_recipe_main(url):
  global nutrientData
  recipe = {}
  ingredient_list = []
  nutrientData = OrderedDict()
  totalPrice = 0
  finalString = ''
  titleString = ''
  contexts = json.load(open('context_settings.json','r'))
  mypath = 'get_google_images/images/'
  onlyfiles = [ f for f in listdir(mypath) if isfile(join(mypath,f)) ]
  snippets = get_snippets(contexts,url)
  #print snippets
  data_ingredients = snippets[0]['ingredients']   # was snippets['ingredients'] before
  data = snippets[0]['directions'] #was 'directions before
  # data_title = snippets[0]['title']  ##doesn't give good things
  #print data_ingredients
  #print data
  #print data_title
  img_title= get_img_title(url)
  data_img = img_title[1]
  data_title = img_title[0]
  #print data_img
  exclude = set(string.punctuation)
  #print '# ' + json_data['name'] + "\n" #this was maybe not in comments before
  imageGridUrls = []
  finalString = finalString + '# ' + titleString + '\n\n'
  finalString = finalString + '# Ingredients\n\n' 
  nutrition  = {}
  start = time.time()
  for line in data_ingredients.split('\n'):
    if len(line)>2:
      finalString = finalString + ' - ' + line.strip().replace('-','').replace('*','') + '\n'
      ingredient_list_item = getFoodFromDatabase(line,nutrition)
      ingredient_list.append(ingredient_list_item)
  recipe['food'] = ingredient_list
  recipe['name'] = data_title # find title
  recipe['url'] = url
  recipe['image_url'] = data_img
  print(recipe)
  print("inserting recipe in db")
  recipe_db.insert_one({'name': data_title, 'food': ingredient_list, 'url': url, 'image_url': data_img})
  return recipe

#print extract_recipe_main('http://www.marthastewart.com/344840/soft-and-chewy-chocolate-chip-cookies')
#print extract_recipe_main('http://www.foodnetwork.com/recipes/alton-brown/baked-macaroni-and-cheese-recipe.html')
#print extract_recipe_main('http://www.foodnetwork.com/recipes/alton-brown/southern-biscuits-recipe.html')
#print extract_recipe_main(sys.argv[1])
#print extract_recipe_main('https://www.forksoverknives.com/recipes/broccoli-pasta-salad-with-red-pepper-pesto')
#print get_image('https://www.forksoverknives.com/recipes/broccoli-pasta-salad-with-red-pepper-pesto')

'''

Useful SQLITE commands

List nutrients
select nutr_no,nutrdesc from nutr_def order by sr_order;


FInd top 50 foods for a given nutrient:
select long_desc,nutr_no,nutr_val from (select long_desc,nutr_no,nutr_val from food_des,nut_data where food_des.ndb_no == nut_data.ndb_no) where nutr_no like '328' order by nutr_val desc limit 50;
'''
