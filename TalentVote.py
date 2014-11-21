#!/usr/bin/env python
# -*- coding:utf-8 -*-

import re
import time
import config

from flask import render_template, Flask, request, abort, make_response

from MongodbOperation import MongodbOperation
from RedisOperation import RedisOperation
from Anchor import Anchor

app = Flask(__name__)
app.config.from_object('config')
mongodb = MongodbOperation()
redis = RedisOperation()



@app.route('/apply', methods=['GET'])
def apply_page():
    return render_template("apply.html",
                           message='')


# 选手报名页面
@app.route('/apply', methods=['POST'])
def apply_in():
    name = request.form['Name'].strip()
    nickname = request.form['Nickname'].strip()
    phone = request.form['Telephone'].strip()
    valid, msg = authenticate(name, nickname, phone)
    if not valid:
        return render_template('apply.html',
                               message=msg)
    anchor_info = Anchor(name, nickname, phone, 0, None, config.PARTICIPATION)
    # 插入数据库
    result = mongodb.register(anchor_info)
    message = u'注册成功'
    if not result:
        message = u'注册失败'
    return render_template('apply.html',
                           message=message)


# 验证昵称，姓名和手机号
def authenticate(name, nickname, phone):
    match = re.match(r'(1[3, 5, 8][0-9]{9})', phone)
    if len(name) == 0 or len(name) > 20:
        return False, u'姓名不能为空或者超过20个字符'
    elif len(nickname) == 0 or len(nickname) > 20:
        return False, u'昵称不能为空或者超过20个字符'
    elif match is None or len(phone) != 11:
        return False, u'手机号格式无效'
    else:
        return True, ''


# 显示全部选手信息页面
@app.route('/showAll')
def show_all():
    cur_page = int(request.args.get('page', 1))
    # print 'page:',page
    anchor_info_list, total_page = redis.get_anchor_list(cur_page)
    # print 'anchorInfAoArr的长度为：', len(anchor_info_list), 'total_page:', total_page
    return render_template('showAll.html',
                           anchor_info_list=anchor_info_list,
                           cur_page=cur_page,
                           total_page=total_page)


# 显示选手详细信息
@app.route('/anchor', methods=['GET'])
def anchor():
    try:
        anchor_id = int(request.args.get('id', 0))
        anchor_info = redis.get_anchor_by_id(anchor_id)
        # 没有查找到选手信息
        if not anchor_info:
            return render_template('error.html',
                                   message=u'未查找到选手信息')
        else:
            return render_template('anchor.html',
                                   anchor=anchor_info)
    except ValueError:
        abort(404)


# 给主播投票
@app.route('/vote', methods=['POST'])
def vote():
    try:
        anchor_id = int(request.args.get('id', 0))
        anchor_info = mongodb.vote_by_id(anchor_id, 1)
        redis.vote_by_id(anchor_id, 1)
        # 没有查找到选手信息
        if not anchor_info:
            return render_template('error.html',
                                   message=u'投票失败')
        else:
            return render_template('success.html',
                                   message=u'投票成功')
    except ValueError:
        abort(404)


# 后台管理用户验证
def verify():
    username = request.cookies.get('username')
    # print username
    if username is None:
        return False
    else:
        return True


# 后台管理
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    is_valid_user = verify()
    if not is_valid_user:
        return render_template('login.html')
    else:
        # resp = make_response(render_template('admin.html'))
        # resp.set_cookie('username', request.cookies.get('username'), expires=0)
        # return resp
        return render_template('admin.html')


# 后台登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    user = request.form['username']
    pwd = request.form['password']
    if user == config.USERNAME and pwd == config.PWD:
        #设置cookie的生存时间为30minutes
        outdated = time.time() + 30 * 60
        resp = make_response(render_template('admin.html'))
        resp.set_cookie('username', user, max_age=30 * 60, expires=outdated)
        return resp
    else:
        return render_template('login.html')


#管理后台请求选手加票页面
@app.route('/addVotesPage', methods=['GET'])
def add_votes_page():
    is_valid_user = verify()
    if not is_valid_user:
        return render_template('login.html')
    else:
        return render_template('addVotes.html')


# 管理后台请求更改选手状态页面
@app.route('/changeAnchorStatePage', methods=['GET'])
def update_anchor_state_page():
    is_valid_user = verify()
    if not is_valid_user:
        return render_template('login.html')
    else:
        return render_template('changeAnchorState.html')


# 管理后台请求更改选手信息页面
@app.route('/changeAnchorInfoPage', methods=['GET'])
def update_anchor_info_page():
    is_valid_user = verify()
    if not is_valid_user:
        return render_template('login.html')
    else:
        return render_template('changeAnchorInfo.html')


# 后台给主播投票
@app.route('/addVotes', methods=['POST'])
def add_votes():
    try:
        anchor_id = int(request.form['id'].strip())
        number = int(request.form['number'].strip())
        # 更新mongo数据库
        anchor_info = mongodb.vote_by_id(anchor_id, number)
        redis.vote_by_id(anchor_id, number)
        #没有查找到选手信息
        if not anchor_info:
            return render_template('error.html',
                                   message=u'投票失败')
        else:
            return render_template('success.html',
                                   message=u'投票成功')
    except ValueError:
        abort(404)


# 后台更改选手状态
@app.route('/changeAnchorState', methods=['POST'])
def change_anchor_state():
    try:
        anchor_id = int(request.form['id'].strip())
        if request.form['choice'] == 'participation':
            # print '你选择了参赛选项'
            state = config.PARTICIPATION
            mongodb.update_anchor_state(anchor_id, config.PARTICIPATION)
        else:
            # print '你选择了退出选项'
            state = config.DROPOUT
        result = mongodb.update_anchor_state(anchor_id, state)
        if result:
            return render_template('success.html',
                                   message=u'设置成功')
        else:
            return render_template('error.html',
                                   message=u'设置失败')
    except ValueError:
        abort(404)


# 后台更改选手信息
@app.route('/changeAnchorInfo', methods=['POST'])
def change_anchor_info():
    try:
        anchor_id = int(request.form['id'].strip())
        name = request.form['name'].strip()
        nickname = request.form['nickname'].strip()
        phone = request.form['phone'].strip()
        # 验证信息
        valid, msg = authenticate(name, nickname, phone)
        if not valid:
            return render_template('error.html',
                                   message=msg)
        # 更新数据库
        result = mongodb.update_anchor_info(anchor_id, name, nickname, phone)
        if result:
            return render_template('success.html',
                                   message=u'修改成功')
        else:
            return render_template('error.html',
                                   message=u'修改失败')
    except ValueError:
        abort(404)


# 搜索页面
@app.route('/search', methods=['GET'])
def search():
    return render_template('search.html')


# 搜索选手
@app.route('/searchResult', methods=['POST'])
def search_result():
    try:
        search_type = request.form['searchType'].strip()
        search_text = request.form['searchText'].strip()
        if search_type == 'id':
            anchor_id = int(search_text)
            result = redis.search_anchor_by_type(0, anchor_id)
        elif search_type == 'nickname':
            result = redis.search_anchor_by_type(1, search_text)
        elif search_type == 'name':
            result = redis.search_anchor_by_type(2, search_text)
        else:
            result = redis.search_anchor_by_type(3, search_text)
        if result:
            return render_template('searchResult.html',
                                   anchorInfoArr=result)
        else:
            return render_template('error.html',
                                   message=u'没有找到相关信息')
    except ValueError:
        abort(404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
