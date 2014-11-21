#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import re
import redis
import json

import pymongo
import config

r = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=0)
con = pymongo.Connection(config.MONGODB_HOST, config.MONGODB_PORT)
db = con.TalentVote

# 每页显示数量
LIST_NUM_PER_PAGE = 3
EXPIRE_TIME = 60

'''
    对缓存Redis的操作
'''


class RedisOperation(object):


    def __init__(self):
        self.total_page = 0
        r.flushdb()

    # 更新每个页面的选手列表
    def update_anchor_info_per_page(self):
        anchors = db.anchorInfo.find({'state': config.PARTICIPATION})  # 列出所有参赛选手
        count = anchors.count()
        max_page = (count + LIST_NUM_PER_PAGE - 1) / LIST_NUM_PER_PAGE
        self.total_page = max_page
        r.delete('sorted')
        if count:
            for anchor in anchors:
                anchor_id = anchor['id']
                r.hmset(anchor_id, anchor)
                r.expire(anchor_id, EXPIRE_TIME)
                r.zadd('sorted', anchor['rank'], anchor_id)
            lis = r.zrange('sorted', 0, -1)

            page = 0
            rank = 0
            for i in xrange(1, max_page + 1):
                r.delete('page:%s' % i)
            for each in lis:
                if rank % LIST_NUM_PER_PAGE == 0:
                    page += 1
                rank += 1
                r.rpush('page:%s' % page, json.dumps(r.hgetall(each)))  # 二级缓存按页查找
            # 设置页面信息的生存时间
            for i in xrange(1, page + 1):
                r.expire('page:%s' % i, EXPIRE_TIME)
        else:
            pass

    # 返回所有参赛选手信息
    def get_anchor_list(self, page):
        anchor_list = r.lrange('page:%s' % page, 0, -1)
        result = []
        while not anchor_list:
            self.update_anchor_info_per_page()
            anchor_list = r.lrange('page:%s' % page, 0, -1)
        for item in anchor_list:
            obj = json.loads(item)
            result.append(obj)
        # print 'total_page:', self.total_page
        # print result
        return result, self.total_page

    # 根据id返回选手信息
    def get_anchor_by_id(self, anchor_id):
        anchor = r.hgetall(anchor_id)
        anchor = json.loads(json.dumps(anchor))
        if anchor is None or not anchor:
            anchor = db.anchorInfo.find_one({'id': anchor_id})
            # print '去服务器拿数据'
            if anchor:
                r.hmset(anchor_id, anchor)
                r.expire(anchor_id, EXPIRE_TIME)
        return anchor

    # 根据id给选手投票，在这里只更新选手票数，不更新排名
    def vote_by_id(self, anchor_id, number):
        r.hincrby(anchor_id, 'votes', number)
        # print 'votes:', r.hget(anchor_id, 'votes')

    # 搜索选手信息
    def search_anchor_by_type(self, searchtype, text):
        if not r.exists('sorted'):
            self.update_anchor_info_per_page()
        else:
            pass
        lis = r.zrange('sorted', 0, -1)
        result = []
        if searchtype == 0:
            result.append(json.loads(json.dumps(r.hgetall(text))))
            return result
        elif searchtype == 1:
            for anchor_id in lis:
                anchor = r.hgetall(anchor_id)
                pattern = re.compile(text)
                # 昵称正则匹配
                if pattern.match(anchor['nickname'].decode('utf-8')):
                    result.append(json.loads(json.dumps(anchor)))
                else:
                    pass
        elif searchtype == 2:
            for anchor_id in lis:
                anchor = r.hgetall(anchor_id)
                # 此时type(anchor['name']) 是str, 而type(text)是Unicode，所有要将anchor['name']按'utf-8'解码
                if anchor['name'].decode('utf-8') == text:
                    result.append(json.loads(json.dumps(anchor)))
                else:
                    pass
        else:
            for anchor_id in lis:
                anchor = r.hgetall(anchor_id)
                if anchor['phone'] == text:
                    result.append(json.loads(json.dumps(anchor)))
                else:
                    pass
        return result
