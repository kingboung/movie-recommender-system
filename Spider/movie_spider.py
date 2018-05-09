import json
import time
import requests
import threading

from config import *
from util import call_eip_worker_api
from movie_introduction_spider import movie_introduction_spider_main

# 豆瓣电影（最新）
url = "https://movie.douban.com/j/new_search_subjects"

# 根据时间进行排序
# querystring = {"sort": "R", "range": "0,10", "tags": "电影", "start": "0"}
# 根据热度进行排序
querystring = {"sort": "T", "range": "0,10", "tags": "电影", "start": "0"}


def movide_spider(index):
    """
    将index页下的所有电影链接爬取出来
    :param index: 第几页下的电影(字符串形式)
    :return: 当页的电影信息
    """
    querystring["start"] = str(index * 20)
    response = requests.request("GET", url, headers=headers, params=querystring, cookies=cookies)
    status_code = response.status_code

    if status_code is not 200:
        call_eip_worker_api()
        time.sleep(180)
        logging.info('更换eip')

        return movide_spider(index)

    response_json = json.loads(response.text)['data']
    return response_json


def movie_spider_main():
    logging.getLogger('').addHandler(movie_handler)

    index = 0
    while True:
        movie_data_list = movide_spider(index)

        # movie_introduction_spider_main(movie_data_list)
        thread = threading.Thread(target=movie_introduction_spider_main, args=(movie_data_list,))
        thread.start()

        index += 1
