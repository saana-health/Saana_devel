from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
import time
import pdb

def submit_form(male, age, height_ft, height_in, weight, activity, pregnancy = ''):
    '''
    This function does web-scrap for DRI record
    :param male:
    :param age:
    :param height_ft:
    :param height_in:
    :param weight:
    :param activity:
    :param pregnancy:
    :return:
    '''
    #form page
    driver = webdriver.Chrome()
    driver.get("https://fnic.nal.usda.gov/fnic/dri-calculator/index.php")

    if male:
        male_field = driver.find_element_by_id('sex-male')
        male_field.click()
    else:
        female_field = driver.find_element_by_id('sex-female')
        female_field.click()

    age_field = driver.find_element_by_id('AGE')
    age_field.send_keys(age)

    if not male:
        preg = Select(driver.find_element_by_id('F_STATUS'))
        preg.select_by_value(pregnancy)

    height_ft_field = driver.find_element_by_id('HEIGHT_FEET')
    height_ft_field.send_keys(height_ft)

    height_in_field = driver.find_element_by_id('HEIGHT_INCHES')
    height_in_field.send_keys(height_in)

    weight_field = driver.find_element_by_id('WEIGHT')
    weight_field.send_keys(weight)

    select = Select(driver.find_element_by_id('ACTIVITY'))
    select.select_by_value(activity)

    button = driver.find_element_by_name('submit')

    button.click()

    # new page
    # time.sleep(0.01)
    tb = driver.find_elements_by_tag_name('td')

    calorie = int(tb[7-male].text.replace('kcal/day',''))
    carb_l = tb[9-male].text.split(' ')
    carb = (int(carb_l[0]),int(carb_l[2]))
    fiber = int(tb[11-male].text.replace('grams',''))
    protein = int(tb[13-male].text.replace('grams',''))
    fat_l = tb[15-male].text.split(' ')
    fat = (int(fat_l[0]),int(fat_l[2]))

    driver.close()

    return calorie, carb, fiber, protein, fat

if __name__ == "__main__":
    calorie, carb, fiber, protein, fat = submit_form(False, 20, 5, 8, 120,'Sedentary','pregnant1st')
