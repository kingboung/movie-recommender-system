import json
import logging
import pymongo
from flask import Flask
from flask import request
from werkzeug.exceptions import BadRequestKeyError

"""影视推荐系统后台"""

app = Flask(__name__)

# 日志配置
fmt = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
date_fmt = '%a, %d %b %Y %H:%M:%S'
logging.basicConfig(filename='server.log', format=fmt, level=logging.INFO, datefmt=date_fmt)


def get_user_info(user_id):
    """
    从数据库中获取用户信息
    :param user_id: 用户id
    :return: 用户信息
    """
    try:
        client = pymongo.MongoClient(host='127.0.0.1')
        db = client.get_database('douban')
        col = db.get_collection('user')

        return col.find({'id': user_id}, {'_id': 0})
    except Exception as ex:
        logging.warning(ex)


def get_movie_info(movie_id):
    """
    从数据库中获取电影信息
    :param movie_id: 电影id
    :return: 电影信息
    """
    try:
        client = pymongo.MongoClient(host='127.0.0.1')
        db = client.get_database('douban')
        col = db.get_collection('movie')

        return col.find({'id': movie_id}, {'_id': 0})
    except Exception as ex:
        logging.warning(ex)


def get_recommend_info(user_id):
    """
    获取用户被推荐的影视信息
    :param user_id: 用户id
    :return: 推荐影视信息
    """
    try:
        client = pymongo.MongoClient(host='127.0.0.1')
        db = client.get_database('douban')
        col = db.get_collection('recommend')

        return col.find({'user_id': user_id}, {'_id': 0})
    except Exception as ex:
        logging.warning(ex)


@app.route('/user_info', methods=['GET', 'POST'])
def api_get_user_info():
    if request.method == 'GET':
        user_id = request.args.get('user_id')
    elif request.method == 'POST':
        try:
            user_id = request.form['user_id']
        except BadRequestKeyError:
            # 请求没有附带参数
            return json.dumps({
                'Response': {
                    'Info': None,
                    'Msg': '非法请求',
                    'Code': 403
                }
            })

    else:
        # 错误的HTTP方法
        return json.dumps({
            'Response': {
                'Info': None,
                'Msg': '非法请求',
                'Code': 403
            }
        })

    if user_id:
        user_info = get_user_info(user_id)
        recommend_info = get_recommend_info(user_id)

        # mongo能够找到该id的用户信息
        if user_info.count() and recommend_info.count():
            return json.dumps({
                'Response': {
                    'Info': user_info[0],
                    'Recommend': recommend_info[0]['recommend_movie_id_list'],
                    'Msg': 'success',
                    'Code': 200
                }
            })
        # mongo没有该id的用户信息
        else:
            return json.dumps({
                'Response': {
                    'Info': None,
                    'Msg': '没有该id的用户信息',
                    'Code': 404
                }
            })

    # 请求没有附带参数
    else:
        return json.dumps({
            'Response': {
                'Info': None,
                'Msg': '非法请求',
                'Code': 403
            }
        })


@app.route('/movie_info', methods=['GET', 'POST'])
def api_get_movie_info():
    if request.method == 'GET':
        movie_id = request.args.get('movie_id')
    elif request.method == 'POST':
        try:
            movie_id = request.form['movie_id']
        except BadRequestKeyError:
            # 请求没有附带参数
            return json.dumps({
                'Response': {
                    'Info': None,
                    'Msg': '非法请求',
                    'Code': 403
                }
            })

    else:
        # 错误的HTTP方法
        return json.dumps({
            'Response': {
                'Info': None,
                'Msg': '非法请求',
                'Code': 403
            }
        })

    if movie_id:
        movie_info = get_movie_info(movie_id)

        # mongo能够找到该id的电影信息
        if movie_info.count():
            return json.dumps({
                'Response': {
                    'Info': movie_info[0],
                    'Msg': 'success',
                    'Code': 200
                }
            })
        # mongo没有该id的电影信息
        else:
            return json.dumps({
                'Response': {
                    'Info': None,
                    'Msg': '没有该id的电影信息',
                    'Code': 404
                }
            })

    # 请求没有附带参数
    else:
        return json.dumps({
            'Response': {
                'Info': None,
                'Msg': '非法请求',
                'Code': 403
            }
        })


@app.route('/user_id_list', methods=['GET'])
def api_get_user_id_list():
    """
    获取所有的用户id
    :return: 用户id列表
    """
    try:
        client = pymongo.MongoClient(host='127.0.0.1')
        db = client.get_database('douban')
        col = db.get_collection('user')

        return json.dumps({
            'Response': {
                'Info': col.distinct('id'),
                'Msg': 'success',
                'Code': 200
            }
        })
    except Exception as ex:
        logging.warning(ex)
        return json.dumps({
            'Response': {
                'Info': None,
                'Msg': '请求失败',
                'Code': 403
            }
        })


@app.route('/movie_id_list', methods=['GET'])
def api_get_movie_id_list():
    """
    获取所有的电影id
    :return: 电影id列表
    """
    try:
        client = pymongo.MongoClient(host='127.0.0.1')
        db = client.get_database('douban')
        col = db.get_collection('movie')

        return json.dumps({
            'Response': {
                'Info': col.distinct('id'),
                'Msg': 'success',
                'Code': 200
            }
        })
    except Exception as ex:
        logging.warning(ex)
        return json.dumps({
            'Response': {
                'Info': None,
                'Msg': '请求失败',
                'Code': 403
            }
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0')
