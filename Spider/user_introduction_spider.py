import time
import redis
import pymongo
import requests
from lxml import etree
from urllib import parse

from config import *
from util import call_eip_worker_api

# 每页的电影数目为30
distance = 30


def gen_movie_link(user_id, type, index=0):
    """
    生成当前id用户正在看电影索引页的response
    :param user_id: 用户id
    :param type: collect 看过; wish 想看; do 正在看
    :param index: 对应页的索引
    :return: 返回用户正在看电影索引页的response
    """
    root_url = 'https://movie.douban.com/people/'
    url = parse.urljoin(root_url, user_id + '/' + type)

    querystring = {"start": str(index * distance), "sort": "time", "rating": "all", "filter": "all", "mode": "list"}

    response = requests.request("GET", url, headers=headers, cookies=cookies, params=querystring)

    # 爬虫中断异常(访问被禁止)
    if response.status_code is not 200:
        # 自动更换ip，继续爬取
        call_eip_worker_api()
        time.sleep(180)

        logging.warning('更换eip')

        return gen_movie_link(user_id, type, index)
    return response


def user_introduction_saver(user_data_dict):
    """
    将解析出来的用户信息入库到mongo中
    :param user_data_dict: 需要入库的电影信息
    :return:
    """
    try:
        mongo_client = pymongo.MongoClient(host='127.0.0.1', port=27017)
        mongo_collection = mongo_client.get_database('douban').get_collection('user')
        mongo_collection.insert(user_data_dict)
    except Exception as ex:
        logging.warning(user_data_dict['id'] + '\t' + ex)


def user_introduction_parser(user_url):
    """
    对用户页的一些用户信息进行爬取
    :param user_url: 用户页对应的url
    :return: 返回相关用户信息的字典
    """
    response = requests.request("GET", user_url, headers=headers, cookies=cookies)

    # 爬虫中断异常(访问被禁止)
    if response.status_code is not 200:
        # 自动更换ip，继续爬取
        call_eip_worker_api()
        time.sleep(180)

        logging.warning('更换eip')
        return user_introduction_spider(user_url)

    html = response.content
    tree = etree.HTML(html)

    # 用户id
    user_id = user_url.split('/')[-2]

    # 用户名
    name = tree.xpath('//*[@class="info"]/h1/text()')
    if name:
        name = name[0].strip()

    # 用户签名
    signature = tree.xpath('//*[@class="info"]//*[@class="signature_display pl"]/text()')
    if signature:
        signature = signature[0]

    # 用户常居地
    permanent_residence = tree.xpath('//*[@class="user-info"]/a/text()')
    if permanent_residence:
        permanent_residence = permanent_residence[0]

    # 用户头像地址
    userface = tree.xpath('//*[@class="basic-info"]/img/@src')
    if userface:
        userface = userface[0]

    user_data_dict = {
        'id': user_id,
        'name': name,
        'signature': signature,
        'userface': userface,
        'permanent_residence': permanent_residence,
    }

    return user_data_dict


def get_total_page(tree):
    """
    获取总页数
    :param tree: DOM树
    :return: 总页数
    """
    total_page = tree.xpath('//*[@class="thispage"]/@data-total-page')
    if total_page:
        try:
            return int(total_page[0])
        except ValueError:
            return 0
    else:
        return 0


def check_movie_exists(movie_id):
    """
    检查该电影是否已经存在于我们的mongo数据库
    :param movie_id: 电影id
    :return: True or False
    """
    try:
        client = redis.Redis(host='127.0.0.1')
        return client.hget('douban_movie', movie_id)
    except Exception as ex:
        logging.warning(ex)


def user_movie_parser(user_id, movie_type):
    """
    获取相应id用户看过的电影及其评分
    :param user_id: 用户id
    :param movie_type: collect 看过; wish 想看; do 正在看
    :return: 返回该用户看过的电影(及其评分，用户看过电影部分有评分)
    """
    result_list = []

    response = gen_movie_link(user_id, movie_type)
    html = response.content
    tree = etree.HTML(html)

    total_page = get_total_page(tree)
    for index in range(total_page):
        response = gen_movie_link(user_id, movie_type, index)
        html = response.content
        tree = etree.HTML(html)

        id_list = tree.xpath('//*[starts-with(@id, "list")]/@id')
        for movie_list_id in id_list:
            movie_id = movie_list_id[4:]

            # 如果数据库中不存在该id的电影，不需要记录该电影
            if not check_movie_exists(movie_id):
                continue

            if movie_type is 'collect':
                rate = tree.xpath('//*[@id="{}"]//*[starts-with(@class, "rating")]/@class'.format(movie_list_id))
                if rate:
                    score = rate[0][6]
                else:
                    score = 0

                result_list.append({'score': score, 'id': movie_id})

            else:
                result_list.append(movie_id)

    return result_list


def user_introduction_spider(user_url):
    """
    对user_url页的用户进行爬取
    :param user_url: 用户详细页的连接
    :return:
    """
    user_id = user_url.split('/')[-2]

    user_data_dict = user_introduction_parser(user_url)
    collect_list = user_movie_parser(user_id, 'collect')
    wish_list = user_movie_parser(user_id, 'wish')
    do_list = user_movie_parser(user_id, 'do')

    user_data_dict['collect_movie'] = collect_list
    user_data_dict['wish_movie'] = wish_list
    user_data_dict['do_movie'] = do_list

    user_introduction_saver(user_data_dict)
