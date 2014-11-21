#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymongo
import config

from pymongo import errors

connection = pymongo.Connection(config.MONGODB_HOST, config.MONGODB_PORT)
db = connection.TalentVote

'''
    对mongo数据库的操作
'''


class MongodbOperation(object):


    def __init__(self):
        # 对票数一栏增加索引
        db.anchorInfo.create_index([('votes', pymongo.DESCENDING)])

    # 主播信息录入
    def register(self, anchor):
        try:
            # 手机号已经注册过
            if db.anchorInfo.find({'phone': anchor.phone}).count() != 0:
                print '手机号重复了，注册失败'
                return False
            else:
                # 插入主播信息
                anchor.rank = db.anchorInfo.find({'votes': {'$gt': anchor.votes},
                                                  'state': config.PARTICIPATION}).count() + 1
                anchor.id = self.id_generator()
                if anchor.id == -1:
                    raise ValueError
                # print "排名是：", anchor.rank
                # print 'id是：', anchor.id
                db.anchorInfo.insert({'name': anchor.name, 'nickname': anchor.nickname, 'phone': anchor.phone,
                                      'votes': anchor.votes, 'rank': anchor.rank, 'state': anchor.state,
                                      'id': anchor.id})
                # 将票数低于当前主播的排名+1
                db.anchorInfo.update({'votes': {'$lt': anchor.votes}, 'state': config.PARTICIPATION},
                                     {'$inc': {'rank': 1}}, upsert=False, multi=True)
                return True
        except (ValueError, pymongo.errors.PyMongoError), e:
            print '录入主播信息时，出现异常', e

    # 设置初始ID为1000,每注册一个主播，ID加1
    @staticmethod
    def id_generator():
        try:
            data = db.idCollection.find_one({}, {'id': 1})
            anchor_id = 1000
            if data is None:
                db.idCollection.insert({'id': 1000})
            else:
                db.idCollection.update({}, {'$inc': {'id': 1}})
                anchor_id = data['id'] + 1
            return anchor_id
        except pymongo.errors.PyMongoError, e:
            print '生成id时，出现异常', e
            return -1

    # 获取所有选手信息
    def get_anchor_list(self):
        try:
            anchor_info_list = list(db.anchorInfo.find({'state': config.PARTICIPATION}).sort('rank', 1))
            return anchor_info_list
        except pymongo.errors.PyMongoError, e:
            print '获取所有选手信息时，出现异常', e
            return None

    # 根据选手id获取数据
    def get_anchor_by_id(self, anchor_id):
        try:
            anchor_info = list(db.anchorInfo.find({'id': anchor_id}))
            if not anchor_info:
                return None
            else:
                return anchor_info
        except pymongo.errors.PyMongoError, e:
            print '根据选手id获取数据时，出现异常', e
            return None

    # 根据id给相应选手投票
    def vote_by_id(self, anchor_id, number):
        try:
            # 获取当前选手的票数并加上number
            votes = db.anchorInfo.find_one({'id': anchor_id}, {'votes': 1})['votes']
            votes += number
            # 更新当前主播的排名
            rank = db.anchorInfo.find({'votes': {'$gt': votes}, 'state': config.PARTICIPATION}).count() + 1
            db.anchorInfo.update({'id': anchor_id}, {'$set': {'votes': votes, 'rank': rank}})
            #主播投票更新后排在主播后面而之前排在主播前面的选手排名
            db.anchorInfo.update({'votes': {'$gte': votes - number, '$lt': votes}, 'state': config.PARTICIPATION},
                                 {'$inc': {'rank': 1}}, upsert=False, multi=True)
            return True
        except pymongo.errors.PyMongoError, e:
            print '给选手投票时，出现异常',e
            return False

    # 根据id设置选手的状态
    def update_anchor_state(self, anchor_id, state):
        try:
            anchor = db.anchorInfo.find_one({'id': anchor_id})
            if anchor is None:
                return False
            votes = anchor['votes']
            pre_state = anchor['state']
            if pre_state == state:
                return True
            # 由退出改为参赛
            if pre_state == config.DROPOUT:
                rank = db.anchorInfo.find({'votes': {'$gt': votes}, 'state': config.PARTICIPATION}).count() + 1
                db.anchorInfo.update({'id': anchor_id}, {'$set': {'state': state, 'rank': rank}})
                db.anchorInfo.update({'state': config.PARTICIPATION, 'votes': {'$lt': votes}},
                                     {'$inc': {'rank': 1}}, upsert=False, multi=True)
            # 由参赛改为退出
            else:
                db.anchorInfo.update({'id': anchor_id}, {'$set': {'state': state}})
                db.anchorInfo.update({'state': config.PARTICIPATION, 'votes': {'$lt': votes}},
                                     {'$inc': {'rank': -1}}, upsert=False, multi=True)
            return True
        except pymongo.errors.PyMongoError, e:
            print '设置选手状态时，出现异常', e
            return False

    # 根据id更新选手的姓名，昵称和电话
    def update_anchor_info(self, anchor_id, name, nickname, phone):
        try:
            db.anchorInfo.update({'id': anchor_id}, {'$set': {'name': name, 'nickname': nickname, 'phone': phone}})
            return True
        except pymongo.errors.PyMongoError, e:
            print '更新选手信息时，出现异常', e
            return False

    # 搜索选手信息
    def search_anchor_by_type(self, searchtype, text):
        try:
            if searchtype == 0:
                anchor_info_list = list(db.anchorInfo.find({'id': text}).sort('rank', 1))
            elif searchtype == 1:
                anchor_info_list = list(db.anchorInfo.find({'nickname': {'$regex': text}}).sort('rank', 1))
            elif searchtype == 2:
                anchor_info_list = list(db.anchorInfo.find({'name': text}).sort('rank', 1))
            else:
                anchor_info_list = list(db.anchorInfo.find({'phone': text}).sort('rank', 1))
            return anchor_info_list
        except pymongo.errors.PyMongoError, e:
            print '搜索选手信息时，出现异常', e
            return None
