# -*- coding: utf-8 -*-
# @Time    : 18-4-9 下午7:43
# @Author  : pythonZhe
# @Email   : 18219111730@163.com
# @File    : spider.py
# @Software: PyCharm
import re

from selenium import  webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from  pyquery import PyQuery as pq
from config import *
import pymongo

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]



url = 'https://www.taobao.com'
options = Options()
# 无头参数
options.add_argument('-headless')
browser = webdriver.Chrome(chrome_options=options)
wait  = WebDriverWait(browser,10)

# # 设置phantomjs窗口的大小
# browser.set_window_size(1400,900)

def search():
    print('正在搜索')
    try:
        browser.get(url)
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button'))
        )


        input.send_keys(KEY_WORD)

        submit.click()
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total'))
        )
        get_products()
        return total.text
    except TimeoutException as e:
        return search()

def next_page(page_number):
    print('paging ',page_number)
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_number))
        )
        get_products()
    except TimeoutException as e:
        next_page(page_number)

def get_products():
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist .items .item'))
    )
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image': 'https:'+item.find('.pic .img').attr('src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text()[:-3],
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        # print(product)
        save2mongo(product)

def save2mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('保存到mongodb成功',result)
    except Exception:
        print('保存到mongodb失败',result)


def main():
    try:
        total = search()
        total = int(re.compile('(\d+)').search(total).group(1))

        for i in range(2, total+1):
            next_page(i)
    except Exception as e:
        print(e)
    finally:
        browser.close()

if __name__ == '__main__':
    main()