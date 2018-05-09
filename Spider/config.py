import random
import string
import logging

# 日志配置
fmt = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
date_fmt = '%a, %d %b %Y %H:%M:%S'

formatter = logging.Formatter(fmt=fmt, datefmt=date_fmt)
movie_handler = logging.FileHandler(filename='log/movie_spider.log')
movie_handler.setFormatter(formatter)
movie_handler.setLevel(logging.INFO)

user_handler = logging.FileHandler(filename='log/user_spider.log')
user_handler.setFormatter(formatter)
user_handler.setLevel(logging.INFO)

# 请求配置
headers = {
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"
}
cookies = {"bid": "".join(random.sample(string.ascii_letters + string.digits, 11))}
