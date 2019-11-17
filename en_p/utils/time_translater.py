#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2018/9/18 上午10:49
# @Author  : wjq
# @File    : time_translater
import calendar
from datetime import datetime
from datetime import timedelta
import time
import re
from en_p.utils.files import get_int_list


def timestamps():
    # 时间戳
    t = str(int(time.time() * 1000))
    return t


def find_time_style(time_str):
    # 2019年02月03日  19年02月03日 2019年2月3日 19年2月3日  02月03日  2月3日
    if re.search(r'\d{1,2}月\d{1,2}日', time_str):
        if re.match(r'\d{1,2}月\d{1,2}日', time_str):
            pattern1 = '%m月%d日'  # 开头是月份
        elif re.match(r'\d{2}年\d{1,2}月\d{1,2}日', time_str):
            pattern1 = '%y年%m月%d日'  # 开头的年份是2位数字
        else:
            pattern1 = '%Y年%m月%d日'  # 开头的年份是4位数字
        time_str = re.sub(r'(?:\d{2,}年)?\d{1,2}月\d{1,2}日', '', time_str)
  
    # 2019-02-03  19-02-03 2019-2-3  19-2-3 02-03 2-3
    elif re.search(r'\d{1,2}-\d{1,2}', time_str):
        if re.match(r'\d{4}-\d{1,2}-\d{1,2}', time_str):
            pattern1 = "%Y-%m-%d"
        elif re.match(r'\d{2}-\d{1,2}-\d{1,2}', time_str):
            pattern1 = "%y-%m-%d"
        else:
            pattern1 = "%m-%d"
        time_str = re.sub(r'(?:\d{2,}-)?\d{1,2}-\d{1,2}', '', time_str, count=1)   # '2019-07-10 14-13-59'
        
    # 2019/02/03 19/02/03 2019/2/3  2019/2/3
    elif re.search(r'\d{1,2}/\d{1,2}', time_str):
        if re.search(r'\d{4}/\d{1,2}/\d{1,2}', time_str):
            pattern1 = "%Y/%m/%d"
        elif re.match(r'\d{2}/\d{1,2}/\d{1,2}', time_str):
            pattern1 = "%y/%m/%d"
        else:
            pattern1 = "%m/%d"
        time_str = re.sub(r'(?:\d{2,}/)?\d{1,2}/\d{1,2}', '', time_str, count=1)
    else:
        print(time_str, '时间解析错误!')
        return
        
    # 2019.02.03  19.02.03 2019.2.3  19.2.3  02.03   2.3
    if re.search(r'\d{1,2}\.\d{1,2}', time_str):
        if re.search(r'\d{4}\.\d{1,2}\.\d{1,2}', time_str):
            pattern1 = "%Y.%m.%d"
        elif re.match(r'\d{2}\.\d{1,2}\.\d{1,2}', time_str):
            pattern1 = "%y.%m.%d"
        else:
            pattern1 = "%m.%d"
        time_str = re.sub(r'(?:\d{2,}\.)?\d{1,2}\.\d{1,2}', '', time_str)
    
    if time_str == "":
        return pattern1

    st = time_str.count(' ')
    mt = time_str.count(':')
    if mt > 0:  # '2019-07-10 14-13-59'
        return pattern1 + ' ' * st + '%H:%M' + ':%S' * (mt - 1)
    else:
        mt = time_str.count('-')
        return pattern1 + ' ' * st + '%H-%M' + '-%S' * (mt - 1)
        
    # todo 改为效率更高的正则
    print(time_str, '时间解析错误!')


def nettime_to_pubtime(pubtime):
    # 转时间戳
    if str(pubtime).isdigit():
        return str(pubtime) if len(str(pubtime)) >= 13 else str(pubtime) + '000'
    elif str(pubtime)[-1] == "前":  # 3小时前  30分钟前
        day = int(pubtime[:-2]) if pubtime[-2:] == "天前" else 0
        hour = int(pubtime[:-3]) if pubtime[-3:] == "小时前" else 0
        miniute = int(pubtime[:-3]) if pubtime[-3:] == "分钟前" else 0
        t = time.time() - ((day * 24 + hour) * 60 + miniute) * 60
        return str(int(t * 1000))
    pattern = find_time_style(pubtime)
    if not pattern:
        return ''
    
    a = datetime.strptime(pubtime, pattern)

    if pattern.find(r"%Y") < 0:
        a = a.replace(datetime.now().year)  # 新闻发布时间缺少年份就默认取今年
    print(a)
    b = int(time.mktime(a.timetuple())) * 1000
    return str(b)


def timestamp_to_otherStyleTime(timestamp, return_datetime=False):
    """时间戳转字符串或者datetime.datetime类型"""
    if not timestamp:
        return
    tp = int(timestamp) if len(str(timestamp)) < 13 else int(timestamp) // 1000

    if return_datetime:
        return datetime.fromtimestamp(tp)
    else:
        timearray = time.localtime(tp)
        return time.strftime("%Y-%m-%d %H:%M:%S", timearray)


def get_date_of_Monday(nw=0, return_date=True):
    """
    获取星期一的日期
    :param nw:     int      计算间隔多少周之前周一日期, 默认nw=0本周星期一的日期
    :param return_date      返回数据类型 是 <class 'datetime.date'> 还是str
    :return        datetime.date or str
    """
    today = datetime.date.today()
    m1 = calendar.MONDAY
    t = today.weekday()
    days = datetime.timedelta(days=t - m1 + 7 * nw)
    date_Monday = today - days
    return date_Monday if return_date else date_Monday.strftime('%Y-%m-%d')


def get_zero_dt_of_Monday(nw=0, return_datetime=True):
    """
    获取星期一的凌晨时间
    :param nw:     int          计算间隔多少周之前周一的凌晨时间, 默认nw=0本周星期一的凌晨时间
    :param return_datetime      返回数据类型 是 <class 'datetime.datetime'> 还是str
    :return        datetime.datetime or str
    """
    now = datetime.datetime.now()
    today = datetime.date.today()
    m1 = calendar.MONDAY
    t = today.weekday()
    time_delta = datetime.timedelta(days=t - m1 + 7 * nw, hours=now.hour, minutes=now.minute, seconds=now.second,
                                    microseconds=now.microsecond)
    zero_Monday = now - time_delta
    return zero_Monday if return_datetime else zero_Monday.strftime('%Y-%m-%d %H:%M:%S')


def get_zero_dt_of_days(nd=0, return_datetime=True):
    """
    获取前nd天的凌晨时间
    :param nd:     int          计算间隔多少天之前的凌晨时间, 默认nd=0今天的凌晨时间
    :param return_datetime      返回数据类型 是 <class 'datetime.datetime'> 还是str
    :return        datetime.datetime or str
    """
    now = datetime.now()
    # today = datetime.today()
    time_delta = timedelta(days=nd, hours=now.hour, minutes=now.minute, seconds=now.second,
                           microseconds=now.microsecond)
    zero_Monday = now - time_delta
    return zero_Monday if return_datetime else zero_Monday.strftime('%Y-%m-%d %H:%M:%S')


def get_datetime_ago(days=1, hours=0, minutes=0, seconds=0, return_datetime=True, now=None):
    """
    获取now时间days天hours小时minutes分钟之前的时间
    :param now                  时间基准
    :param return_datetime      返回数据类型 是 <class 'datetime.datetime'> 还是str
    :return        datetime.datetime or str
    """
    if not now:
        now = datetime.now()
    time_delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds, microseconds=now.microsecond)
    tt = now - time_delta
    return tt if return_datetime else tt.strftime('%Y-%m-%d %H:%M:%S')


# todo check
def utc2local(utc_st):
    """UTC时间转本地时间（+8:00）"""
    now_stamp = time.time()
    local_time = datetime.fromtimestamp(now_stamp)
    utc_time = datetime.utcfromtimestamp(now_stamp)
    offset = local_time - utc_time
    local_st = utc_st + offset
    return local_st


# todo check
def local2utc(local_st):
    """本地时间转UTC时间（-8:00）"""
    time_struct = time.mktime(local_st.timetuple())
    utc_st = datetime.utcfromtimestamp(time_struct)
    return utc_st


def get_everyday_date(sd, ed):
    """获取每一天的日期"""
    date_1 = sd
    date_list = [sd]
    ds = (ed - sd).days  # 间隔多少天

    for i in range(1, ds):
        date_1 = date_1 + timedelta(days=1)  # 前一天+1天
        date_list.append(date_1)

    return date_list + [ed]


if __name__ == '__main__':
    date_str = "" 
#     "".join(get_int_list(get_datetime_ago(days=idx).strftime('%Y-%m-%d'))) for idx in range(3662, -1, -1)
#         date_str = "".join(get_int_list(get_datetime_ago(days=idx).strftime('%Y-%m-%d')))
#         print(date_str)