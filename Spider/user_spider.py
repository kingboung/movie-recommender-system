import time
import pymongo
import requests
from lxml import etree
from urllib import parse

from config import *
from util import call_eip_worker_api
from user_introduction_spider import user_introduction_spider

"""
取500部电影影评下各两名用户进行爬取
"""

root_url = "https://movie.douban.com/subject/"


def get_movie_id_list():
    try:
        client = pymongo.MongoClient(host='127.0.0.1')
        db = client.get_database('douban')
        col = db.get_collection('movie')

        return [id_dict['id'] for id_dict in col.find({}, {'_id': 0, 'id': 1}, limit=500)]

    except Exception as ex:
        logging.warning('mongo操作出错,{}'.format(ex))


def user_spider(movie_id):
    """
    将对应movie_id电影页下的用户列表爬取出来
    :param movie_id: 电影id
    :return:
    """
    user_result_list = []

    url = parse.urljoin(root_url, movie_id)
    response = requests.request("GET", url, headers=headers, cookies=cookies)

    if response.status_code is not 200:
        call_eip_worker_api()
        time.sleep(180)
        logging.info('更换eip')

        return user_spider(movie_id)

    html = response.content
    tree = etree.HTML(html)

    user_list = tree.xpath('//*[@class="comment-item"]//*[@class="comment-info"]/a/@href')
    for user in user_list[:2]:
        user_result_list.append(user)

    return user_result_list


def user_spider_main():
    logging.getLogger('').addHandler(user_handler)

    user_url_list = []

    movie_id_list = get_movie_id_list()
    for movie_id in movie_id_list:
        user_url_list.extend(user_spider(movie_id))

    # 去除重复用户并记录到文件
    user_url_list = list(set(user_url_list))
    for user_url in user_url_list:
        with open('user_url_list.txt', 'w') as stream:
            stream.write(user_url + '\n')

    # 开始爬取用户的详细信息
    for user_url in user_url_list:
        user_introduction_spider(user_url)
