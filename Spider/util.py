import os
import time
import pymongo
import threading
from urllib import parse

"""一些常用的模块放在这里"""


def call_eip_worker_api():
    """
    由于调用更换ip脚本后会出现断网的情况而无法正常跑通程序，更换ip服务被放到另一台机子以后台服务形式提供
    :return:
    """
    thread = threading.Thread(target=lambda: os.system('curl http://116.85.37.93:5000/'))
    thread.start()

    time.sleep(5)
    # 由于更换ip而无法得到返回值，导致curl命令一直在等待，我们这里直接kill掉相关进程
    os.system("ps -ef | grep 'curl http://116.85.37.93:5000/' | grep -v grep | awk '{print $2}' | xargs kill -9")

    thread.join(timeout=5)


def deduplicate():
    """
    文本去重
    :return:
    """
    with open('user_list.txt', 'r') as file_stream:
        user_url_list = [line.strip() for line in file_stream.readlines()]

    # 文件内的用户url去重
    user_url_list = list(set(user_url_list))

    with open('user_list.txt', 'w') as file_stream:
        for user_url in user_url_list:
            file_stream.write(user_url + '\n')


def flush_user_list():
    """
    去除user_list.txt文件中已经入库的那部分用户url
    :return:
    """
    client = pymongo.MongoClient(host='127.0.0.1')
    db = client.get_database('douban')
    col = db.get_collection('user')

    id_list = [user_id['id'] for user_id in col.find({}, {'_id': 0, 'id': 1})]

    with open('user_list.txt', 'r') as file_stream:
        user_url_list = [line.strip() for line in file_stream.readlines()]

    for user_id in id_list:
        url = 'https://www.douban.com/people/'
        user_url = parse.urljoin(url, user_id) + '/'
        if user_url in user_url_list:
            user_url_list.remove(user_url)

    with open('user_list.txt', 'w') as file_stream:
        for user_url in user_url_list:
            file_stream.write(user_url + '\n')
