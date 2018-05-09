from movie_spider import movie_spider_main
from user_spider import user_spider_main


"""爬虫入口"""
"""先爬取影视数据再爬取用户数据，用户数据的观影历史是基于影视数据的"""
if __name__ == '__main__':
    movie_spider_main()
    user_spider_main()
