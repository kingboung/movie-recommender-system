import pymongo
import numpy as np

"""基于用户的协同过滤算法"""

threshold = None    # 选取最近邻居的阈值
k = 5   # 选取最近邻居的数目
recommend_number = 5    # 推荐的电影数


def get_data():
    """
    从数据库取数据
    :return: 电影数据，用户数据(及其电影评分)
    """
    movie_dict = {}
    user_dict = {}
    movie_dict_by_index = {}
    user_dict_by_index = {}

    try:
        client = pymongo.MongoClient(host='127.0.0.1')
        db = client.get_database('douban')
        movie_col = db.get_collection('movie')
        user_col = db.get_collection('user')

        movie_cursor = movie_col.distinct('id')
        user_cursor = user_col.find({}, {'_id': 0, 'id': 1, 'collect_movie': 1})

        for index, movie_data in enumerate(movie_cursor):
            movie_dict[movie_data] = index
            movie_dict_by_index[index] = movie_data

        for index, user_data in enumerate(user_cursor):
            user_dict[user_data['id']] = user_data['collect_movie']
            user_dict_by_index[index] = user_data['id']

        return movie_dict, user_dict, movie_dict_by_index, user_dict_by_index
    except Exception:
        pass


def create_user_model(movie_dict, user_dict):
    """
    建立用户模型(用户-项目评分矩阵)
    :param movie_dict: 电影数据集
    :param user_dict: 用户数据集
    :return:
    """
    movie_number = len(movie_dict)
    user_number = len(user_dict)

    user_model = np.zeros((user_number, movie_number), dtype=np.int8)

    for user_index, (user_id, user_score) in enumerate(user_dict.items()):
        for movie in user_score:
            movie_id = movie['id']
            movie_score = movie['score']

            movie_index = movie_dict[movie_id]
            user_model[user_index][movie_index] = movie_score

    return user_model


def calc_user_cosine_sim(user_vector_a, user_vector_b):
    """
    计算用户的余弦相似性
    :param user_vector_a: 一组用户数据
    :param user_vector_b: 一组用户数据
    :return: 余弦相似性
    """
    sim = np.dot(user_vector_a, user_vector_b) / (np.linalg.norm(user_vector_a) * np.linalg.norm(user_vector_b))
    return sim


def calc_average_vector(vector):
    """
    计算vector中除去0值部分的平均值
    :return:
    """
    nonzero_index = list(np.nonzero(vector)[0])
    nonzero_value = []

    for index in nonzero_index:
        nonzero_value.append(vector[index])

    return np.mean(np.array(nonzero_value))


def generate_recommend_items(user_vector_a, neighborhood_sim_vector, total_movie):
    """
    生成推荐项目
    :param user_vector_a: 需要被推荐电影用户的用户数据
    :param neighborhood_sim_vector: 需要被推荐电影用户的邻居的用户数据
    :param total_movie: 电影总数
    :return: 推荐电影id列表
    """
    # 获取需要被推荐电影用户已评价电影索引
    evaluated_movie_index_list = list(np.nonzero(user_vector_a)[0])
    user_mean_score_a = calc_average_vector(user_vector_a)

    # 从用户a未观看过的电影中推荐电影
    numerator = 0
    denominator = 0
    recommend_movie_predict_score = []
    for index in range(total_movie):
        if index not in evaluated_movie_index_list:
            for neighbor_sim_vector in neighborhood_sim_vector:
                sim = neighbor_sim_vector[1]
                user_vector_b = np.array(neighbor_sim_vector[2])

                user_mean_score_b = calc_average_vector(user_vector_b)

                numerator += sim * (user_vector_b[index] - user_mean_score_b)
                denominator += abs(sim)

            predict_score = user_mean_score_a + numerator / denominator
            recommend_movie_predict_score.append((index, predict_score))

    recommend_movie_predict_score = sorted(recommend_movie_predict_score, key=lambda x: x[1], reverse=True)
    return recommend_movie_predict_score[:recommend_number]


def save_remcommend_result(user_id, movie_id_list):
    """
    将推荐结果保存到mongo中
    :return:
    """
    try:
        client = pymongo.MongoClient(host='127.0.0.1')
        db = client.get_database('douban')
        col = db.get_collection('recommend')

        col.insert({
            'user_id': user_id,
            'recommend_movie_id_list': movie_id_list
        })
    except Exception:
        pass


def main():
    """
    主函数
    :return:
    """
    movie_dict, user_dict, movie_dict_by_index, user_dict_by_index = get_data()
    total_user = len(user_dict)
    total_movie = len(movie_dict)

    user_model = create_user_model(movie_dict, user_dict)
    for index_a in range(total_user):
        user_vector_a = user_model[index_a]
        sim_dict = {}

        for index_b in range(total_user):
            # 相同用户不进行比较
            if index_b == index_a:
                continue

            user_vector_b = user_model[index_b]
            sim = calc_user_cosine_sim(user_vector_a, user_vector_b)
            sim_dict[index_b] = sim

        # 对sim_dict进行排序，按value从大到小排序，并选择前k个作为该用户的最近邻居
        neighborhood_sim = sorted(sim_dict.items(), key=lambda item: item[1], reverse=True)[:k]

        neighborhood_sim_vector = []
        for neighbor in neighborhood_sim:
            user_index = neighbor[0]
            user_vector = user_model[user_index]
            neighborhood_sim_vector.append((neighbor[0], neighbor[1], user_vector))

        recommend_result = generate_recommend_items(user_vector_a, neighborhood_sim_vector, total_movie)

        user_id = user_dict_by_index[index_a]
        movie_id_list = []
        for recommend_item in recommend_result:
            movie_index = recommend_item[0]
            movie_id_list.append(movie_dict_by_index[movie_index])

        save_remcommend_result(user_id, movie_id_list)


if __name__ == '__main__':
    main()
