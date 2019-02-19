import requests
from urllib.parse import urlencode
from ua_pool import get_ua
from ip_pool import get_ip
from requests.exceptions import RequestException
from config import *
import json
import re
from bs4 import BeautifulSoup
from pymongo import MongoClient
import os
from hashlib import md5
from lxml import etree

client = MongoClient(MONGO_URL, 27017)
db = client[MONGO_DB_TOUTIAO]


def get_page_index(KEYWORD, offset):
    data = {
        "aid": 24,
        "autoload": "true",
        "count": 20,
        "cur_tab": 1,
        "en_qc": 1,
        "from": "search_tab",
        "format": "json",
        "keyword": KEYWORD,
        "offset": offset,
        "pd": "synthesis"
    }
    url = 'https://www.toutiao.com/api/search/content/?' + urlencode(data)
    # url = 'https://www.toutiao.com/api/search/content/?aid=24&offset=0&format=json&keyword=街拍&' \
    #       'autoload=true&count=20&en_qc=1&cur_tab=1&from=search_tab&pd=synthesis'
    while 1:
        try:
            headers = get_ua()
            proxies = get_ip()
            response = requests.get(url, headers=headers, proxies=proxies, timeout=2)
            # response = requests.get(url)
        except Exception as e:
            # print(e)
            pass
        else:
            break
    try:
        if response.status_code == 200:
            print('请求索引页成功')
            return response.text.encode('utf-8')
        print('请求索引页失败')
        return None
    except RequestException:
        return None


def get_page_detail(url):
    while 1:
        try:
            headers = get_ua()
            proxies = get_ip()
            response = requests.get(url, headers=headers, proxies=proxies, timeout=2)
            # response = requests.get(url)
        except Exception as e:
            # print(e)
            pass
        else:
            break
    try:
        if response.status_code == 200:
            print('请求详情页成功')
            return response.text
        print('请求详情页失败')
        return None
    except RequestException:
        return None


def parse_page_index(html):
    data = json.loads(html)  # json.load()将字符串转换为字典,json.dumps()则相反
    # print(data)  # 数据和原来的源码一样，只是类型从字符串变成字典
    # print(type(data))  # 返回dict字典类型
    if data and 'data' in data.keys():
        for item in data.get('data')[2:]:  # 循环拿出data标签下的字典
            # print(item)  #
            # print(type(item))
            yield item.get('article_url')  # 生成器迭代return图集的链接


def parse_page_detail(html):
    # soup = BeautifulSoup(html, 'lxml')
    # title = soup.select('title')
    # title = soup.select('title')[0].get_text()  # select返回的是列表，取值下标第一个，再提取文字
    title_pattern = re.compile(r'class="article-title">(.*?)</h1', re.S)
    title = re.findall(title_pattern, html)[0]
    etree_html = etree.HTML(html)
    images = etree_html.xpath('//div[@class="pgc-img"]/img/@src')
    # print(title)
    # images_pattern = re.compile(r'img src&#x3D;&quot;(.*?)&quot;', re.S)
    # images = re.findall(images_pattern, html)
    # result = re.search(images_pattern, html)
    # print(images)
    for image in images:
        download(image)
    return {'title': title,
            'images': images}


def save_to_mongodb(result):
    if db[MONGO_TABLE_JIEPAI].insert(result):
        print('存储到MongoDB成功', result)
        return True
    return False


def download(url):
    print('正在下载：', url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            save_image(response.content)
    except RequestException:
        print('请求图片出错：', url)
        return None


def save_image(content):
    file_path = '{0}/{1}.{2}'.format('/Users/mac/Downloads/jiepai', md5(content).hexdigest(), 'jpg')
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)
            f.close()


def main(offset):
    # 第一步，拿到索引页源码
    html = get_page_index(KEYWORD, offset)
    # print(html)  #返回请求链接的源码，为json串
    # print(type(html))  #json串为字符串str类型
    # 第二步，解析索引源码，拿到图集的链接
    # yield_return = parse_page_index(html)
    # print(yield_return)  #打印结果：<generator object parse_page_index at 0x1017e2d68>
    # print(type(yield_return))  #打印结果：<class 'generator'>
    for url in parse_page_index(html):  #循环拿出生成器拿到的图集链接
        print('正在解析详情页', url)
        # 第三步，已经拿到了图集链接，我们要拿到每个图集链接的网页源码
        html = get_page_detail(url)
        # print('html', html)
        # 第四步，解析详情页源码，拿出标题和图集下所有图片链接
        result = parse_page_detail(html)
        print(result)
        save_to_mongodb(result)


if __name__ == '__main__':
    for x in range(GROUP_START,GROUP_END+1)
        main(x*20)
