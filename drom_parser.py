import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from selenium.common.exceptions import NoSuchElementException
import time
import sqlalchemy.exc
import psycopg2

engine = sqlalchemy.create_engine("")

def get_car_info_from_page(link):
    """Функция сбора информации объявлений со страницы и сохранения в базу данных"""
    df = pd.DataFrame(columns=['Цена','Город','Модель','Год','url','Коробка передач','Привод','Тип кузова','Цвет','Пробег, км','Руль','Особые отметки','Поколение','Комплектация','Пробег','VIN'])
    r = requests.get(link)
    soup = BeautifulSoup(r.text, 'lxml')

    try:
        cars_block = soup.find('div', class_=['css-1173kvb eaczv700']).find('div', class_='css-1173kvb eaczv700')

        for model_and_year, href, city, price in zip(cars_block.findAll('span', class_='css-o6wtgt e162wx9x0')
                                        ,cars_block.findAll('a', class_='css-3jcp5o ewrty961')
                                        ,cars_block.findAll('span', class_='css-1mj3yjd e162wx9x0')
                                        ,cars_block.findAll('span', class_='css-byj1dh e162wx9x0')
                                       ):
            car_dict = {}
            car_url = href.get('href')
            model_and_year = model_and_year.text.split(',')

            car_dict['Цена'] = re.sub("[^0-9]", "", price.text.replace(u'\xa0', u''))
            car_dict['Город'] = city.text
            car_dict['Модель'] = model_and_year[0]
            car_dict['Год'] = model_and_year[1]
            car_dict['url'] = car_url

            car_request = requests.get(car_url)
            car_soup = BeautifulSoup(car_request.text, 'lxml')
            car_info = car_soup.find('table', class_='css-xalqz7 eppj3wm0').findAll('tr')
            for i in range (3, len(car_info)):
                car_dict[car_info[i].find('th', class_='css-1y4xbwk ezjvm5n2').text] = car_info[i].find('td', class_='css-7whdrf ezjvm5n1').text

            df = df.append(car_dict, ignore_index=True)
        df.to_sql('drom', engine, if_exists='append', index=False)
    except:
        return

def drom_parser():
    """Основная функция, которая проходит по всем объявлениям"""
    driver = webdriver.Chrome()
    base_url = 'https://auto.drom.ru/'
    driver.get(base_url)
    all_brands = driver.find_elements_by_class_name('e4ojbx43')
    #Цикл по каждому бренду
    for brand_num in range(0,len(all_brands)): 
        brand_current_url = driver.current_url
        all_brands[brand_num].click()
        all_models=driver.find_elements_by_class_name('e4ojbx43')
        
        #Цикл по каждой модели
        for models_num in range(0,len(all_models)):
            page = True
            models_url = driver.current_url
            all_models[models_num].click()
            #Цикл по по всем страницам модели
            while page:
                #Считываем всю информацию cо страницы
                get_car_info_from_page(driver.current_url)
                #Проверка наличия следующей страницы.
                try:
                    driver.find_element_by_class_name('e24vrp31').click()
                except NoSuchElementException:
                    page=False
                    driver.get(models_url)
                    all_models = driver.find_elements_by_class_name('e4ojbx43')
                    
        driver.get(brand_current_url)
        all_brands = driver.find_elements_by_class_name('e4ojbx43')
