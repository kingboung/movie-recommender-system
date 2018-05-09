import pymongo

"""数据预处理部分"""


def del_worthless_data():
    """
    认为观影历史记录少于10部的记录为没有价值的数据
    :return:
    """
    worthless_data_list = []

    try:
        client = pymongo.MongoClient(host='127.0.0.1')
        db = client.get_database('douban')
        col = db.get_collection('user')
        cursor = col.find({}, {'collect_movie': 1})

        for data in cursor:
            if len(data['collect_movie']) <= 100:
                worthless_data_list.append({
                    '_id': data['_id']
                })

        for worthless_data in worthless_data_list:
            col.remove(worthless_data)

    except Exception:
        pass


if __name__ == '__main__':
    del_worthless_data()
