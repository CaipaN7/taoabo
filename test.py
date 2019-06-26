from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from urllib.parse import quote
from pyquery import PyQuery
import pymongo

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
browser = webdriver.Chrome(executable_path=r"D:\Chromedriver\chromedriver.exe", chrome_options=chrome_options)
wait = WebDriverWait(browser, 10)
# keyword = '手机'
keyword = input('请输入你要查询的商品：')

client = pymongo.MongoClient(host='localhost', port=27017)
db = client.Caipan
collection = db.taobao


def index_page(page):
    '''抓取索引页，参数为页码'''
    print('正在抓取第{0}页'.format(page))
    url = 'https://s.taobao.com/search?q=' + quote(keyword)
    browser.get(url)
    try:
        if page > 1:
            input = wait.until(
                EC.presence_of_element_located((By.XPATH, '//div[@id="mainsrp-pager"]//input[@aria-label="页码输入框"]')))
            submit = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//div[@id="mainsrp-pager"]//span[@class="btn J_Submit"]')))
            input.clear()
            input.send_keys(page)
            submit.click()
    except TimeoutException:
        index_page(page)
    wait.until(
        EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'div#mainsrp-pager li.item.active > span'), str(page)))
    wait.until(EC.presence_of_element_located(
        (By.XPATH, '//div[@id="mainsrp-itemlist"]//div[@class="items"]/div[contains(@class,"item")]')))
    html = browser.page_source
    return html


def get_products(html):
    '''提取商品数据'''
    doc = PyQuery(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'img': 'https:' + str(item.find('.img').attr('data-src')),
            'price': item.find('.price.g_price.g_price-highlight').text().replace('\n', ' '),
            'count': item.find('.deal-cnt').text(),
            'title': item.find('.row.row-2.title').text().replace('\n', ' '),
            'shopname': item.find('.shopname').text(),
            'location': item.find('.location').text()
        }
        print('\t', product)
        save_to_mongo(product)


def save_to_mongo(product):
    try:
        if collection.insert(product):
            print('\t\t --成功保存')
    except Exception as e:
        print('\t\t --保存失败\n', e)


def main(page):
    html = index_page(page)
    get_products(html)


if __name__ == '__main__':
    for page in range(1, 101):
        main(page)
