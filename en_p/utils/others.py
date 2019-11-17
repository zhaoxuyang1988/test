#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2018/9/21 上午10:56
# @Author  : wjq
# @File    : others


import os
from functools import wraps
import time
import threading
from typing import Iterable


class Singleton(object):
    _instance_lock = threading.Lock()
    _instances = {}

    def __new__(cls, *args, **kwargs):
        with Singleton._instance_lock:
            if cls.__name__ not in Singleton._instances:
                Singleton._instances[cls.__name__] = object.__new__(cls)
        return Singleton._instances[cls.__name__]


def get_upper_dir(abs_path, n):
    """获取上n级的路径"""
    if n == 0:
        return abs_path
    path = os.path.dirname(abs_path)
    return get_upper_dir(path, n - 1)


class RetryNoResError(Exception):
    """重试次数太多但无返回"""
    pass


def retry_dec(retry_time, logger):  # 最多执行函数装饰器
    def dec(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            res = None
            _retry_time = retry_time
            while not res and _retry_time > 0:
                _retry_time = _retry_time - 1
                try:
                    res = fn(*args, **kwargs)  # fn是有返回的
                except Exception as e:
                    logger.error("Round:{}, fn: {} raise Exception: %s".format((retry_time-_retry_time), fn.__name__), e)  # 第几轮函数报错
                    # time.sleep(random.uniform(0, 1))
                    time.sleep(3)
            if _retry_time == 0 and not res:
                raise RetryNoResError('fn: %s retry too many times! No res!' % fn.__name__)
            return res

        return wrapper

    return dec


def to_list(cv):
    if cv is None:
        return []
    if isinstance(cv, str):
        return [cv]
    if isinstance(cv, Iterable):
        return cv
    else:
        return [cv]


def get_query_map(url):
    import urllib.parse
    query_map = {}
    result = urllib.parse.urlsplit(url)
    query_map["scheme"] = result.scheme
    query_map["netloc"] = result.netloc
    query_map["path"] = result.path
    query_map["fragment"] = result.fragment
    query_map["query"] = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
    return query_map
