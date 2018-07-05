__author__ = 'Administrator'
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from pyquery import PyQuery as pq
from config import *
import pymongo

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

browser = webdriver.Chrome()
"""
如果把Chrome修改为使用PhantomJS
1. 首先需要安装phantomJS
2. 自定义一些配置参数，这里不加载图片以及使用缓存
browser = webdriver.PhantomJS(service_args=SERVICE_ARGS)
3. 设置窗口大小
browser.set_window_size(1400,900)
"""

wait = WebDriverWait(browser, 10)


def search():
    # print('正在搜索')  用于phantomJS调试
    try:
        browser.get('https://www.taobao.com')
        input1 = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
        )
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button')))
        # 这里的美食可以替换为配置文件中的变量KEYWORD
        input1.send_keys('美食')
        submit.click()
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total')))
        # 调用get_products
        get_products()
        return total.text

    except TimeoutError:
        return search()


# 使用翻页输入框来翻页
def next_page(page_number):
    # print('正在翻页',page_number) 用于phantomJS调试
    try:
        input1 = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        input1.clear()
        input1.send_keys(page_number)
        submit.click()
        # 根据选择页面会高亮这个条件，来判断是否成功跳转
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_number)))
        # 调用get_products()
        get_products()

    except TimeoutError:
        next_page(page_number)


# 解析信息
def get_products():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text()[:-3],
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        print(product)
        # 保存数据到mongodb
        save_to_mongo(product)


# 定义一个保存到mongodb的方法
def save_to_mongo(result):
    try:
        if db[MON_TABLE].insert(result):
            print('存储到MONGODB成功', result)
    except Exception:
        print('存储到MONGODB失败', result)


def main():
    try:
        # 输出100数字
        total = search()
        total = int(re.compile('(\d+)').search(total).group(1))
        # 调用翻页函数
        for i in range(2, total + 1):
            next_page(i)
    except Exception:
        print('出错了')

    finally:
        browser.close()

if __name__ == '__main__':
    main()