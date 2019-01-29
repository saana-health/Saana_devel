from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
import time
import pdb

def submit_form(male, age, height_ft, height_in, weight, acitivty):
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

    height_ft_field = driver.find_element_by_id('HEIGHT_FEET')
    height_ft_field.send_keys(height_ft)

    height_in_field = driver.find_element_by_id('HEIGHT_INCHES')
    height_in_field.send_keys(height_in)

    weight_field = driver.find_element_by_id('WEIGHT')
    weight_field.send_keys(weight)

    select = Select(driver.find_element_by_id('ACTIVITY'))
    select.select_by_value('Sedentary')

    button = driver.find_element_by_name('submit')

    button.click()

    # new page
    time.sleep(1)
    tb = driver.find_elements_by_tag_name('td')

    calorie = int(tb[6].text.replace('kcal/day',''))
    carb_l = tb[8].text.split(' ')
    carb = (int(carb_l[0]),int(carb_l[2]))
    fiber = int(tb[10].text.replace('grams',''))
    protein = int(tb[12].text.replace('grams',''))
    fat_l = tb[14].text.split(' ')
    fat = (int(fat_l[0]),int(fat_l[2]))

    return calorie, carb, fiber, protein, fat

if __name__ == "__main__":
    calorie, carb, fiber, proetin, fat = submit_form(True, 20, 5, 8, 120,'Sedentary')
    pdb.set_trace()
