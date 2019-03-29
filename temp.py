import utils
import connectMongdo
from connectMongdo import get_any, drop
import model
import pdb


# maggie_id = get_any('patients','name','Maggie')['_id']#'[0]['_id']
#
# mealinfo = model.MealHistory(maggie_id,1)
# mealinfo2 = model.MealHistory(maggie_id,2)
# meal_list = {}
names = ["creamy celeriac soup with rosemary oat crumble",'roasted chickpea & tahini soup', 'perfect pot pie', 'puy lentil & cabbage burger with roasted veggies', 'lunch thyme grain bowl','butternut squash & red lentil dal with seedy topping']
slots = []
for name in names:
    x = get_any('meals','name',name)
    slots.append(x)
pdb.set_trace()

# meal1 = get_any('meals','name','creamy celeriac soup with rosemary oat crumble')
# meal2 = get_any('meals','name','roasted chickpea & tahini soup')
# meal3 = get_any('meals','name','perfect pot pie')
# meal4 = get_any('meals','name','puy lentil & cabbage burger with roasted veggies')
# meal5 = get_any('meals','name','lunch thyme grain bowl')
# meal6 = get_any('meals','name','butternut squash & red lentil dal with seedy topping')
# meal7 = get_any('meals','name','cauliflower alfredo with red lentil rotini')
# meal8 = get_any('meals','name','saag no paneer with cardamom rice')
# meal9 = get_any('meals','name','veggie brunch muffin with roasted red pepper sauce')
# meal10 = get_any('meals','name','chickpea & maitake tacos with corn tortillas')
# meal11 = get_any('meals','name','chana masala with indian spiced rice')
# meal12 = get_any('meals','name','veggie heavy spanakopita with chickpea toast and olive and almond crumble')
#
# li = [meal1,meal2,meal3,meal4,meal5,meal6,meal7,meal8, meal9, meal10,meal11,meal12]
# # pdb.set_trace()
# li2 = [[x['_id']] if x is not None else None for x in li]
#
# mealinfo.meal_list = {'day_1':li2[0],\
#                       'day_2':li2[1],\
#                       'day_3':li2[2],\
#                       'day_4':li2[3],\
#                       'day_5':li2[4],\
#                       'day_6':li2[5]
#                       }
# mealinfo2.meal_list = {'day_1':li2[6],\
#                       'day_2':li2[7],\
#                       'day_3':li2[8],\
#                       'day_4':li2[9],\
#                       'day_5':li2[10],\
#                       'day_6':li2[11]
#                       }
#
#
# # eal12 = get_any('meals','name','veggie heavy spanakopita with chickpea toast and olive and almond crumble')
# drop('mealInfo')
# connectMongdo.add_meal_history(mealinfo,maggie_id)
# connectMongdo.add_meal_history(mealinfo2,maggie_id)
