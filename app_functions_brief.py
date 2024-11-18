from __future__ import unicode_literals
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

from datetime import datetime, timedelta, timezone
import threading
import csv
import os
import pymongo
import requests
import json
import configparser

#有關mongo指令的函式
import mongofunction as mf


import functions as f

import text_functions as tf

app = Flask(__name__, static_url_path='/static', static_folder="./static")
secret_key = os.urandom(16).hex()
app.secret_key = secret_key

# 設定Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"
login_manager.login_view = 'login'  # 當未登入的用戶訪問受限頁面時，將會重定向到此頁面

CHECKLIST = ['22:00', '22:05', '22:10', '22:15', '22:20', '22:25', '22:30', '22:35', '22:40', '22:45', '22:50', '22:55']
#檢查指定12個時間是否被占用
USERID_TRADER_PARTNER = f.getusertraderpartner()
print(USERID_TRADER_PARTNER)
config = configparser.ConfigParser()
config.read('config.ini')

configuration = Configuration(access_token=config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))

username = config.get('mongodb', 'username')
password = config.get('mongodb', 'password')
hostlocation = config.get('mongodb', 'hostlocation')
# myclient = pymongo.MongoClient("mongodb://localhost:27017/")
cluster_url =f"mongodb+srv://{username}:{password}@{hostlocation}/?retryWrites=true&w=majority&appName=GueiMing"
myclient = pymongo.MongoClient(cluster_url, username=username,password=password)




HEADER = {
    'Content-type': 'application/json',
    'Authorization': F'Bearer {config.get("line-bot", "channel_access_token")}'
}

userids = ['U66da2ba27e83014da52f28455ef19c7c', 'Uf8e734e58b67c12e0de1cd574a1718da']

'''利用Line api 中 reply分類作為機器人回覆功能的主要函式'''
def replyMessage(payload):
    url='https://api.line.me/v2/bot/message/reply'
    response = requests.post(url,headers=HEADER,json=payload)
    
    print(response.status_code)
    print(response.text)
    return 'OK'

'''Line bot 的callback主邏輯'''
@app.route("/callback", methods=['POST', 'GET'])
def callback():
    if request.method == 'GET':
        return 'ok'
    body = request.json
    events = body["events"]
    if request.method == 'POST' and len(events) == 0:
        return 'ok'
    print(body)
    if "replyToken" in events[0]:
        payload = dict()
        replyToken = events[0]["replyToken"]
        payload["replyToken"] = replyToken
        userId = events[0]["source"]["userId"]
        state = mf.getNowState()
        if state == 0:
            text = events[0]["message"]["text"]
            if text == "切換" and userId in userids:
                payload["messages"] = [tf.getOpenText()]
            else:
                print("今日休息")
                payload["messages"] = [tf.getTodayClosedText()]
            replyMessage(payload)
        else: 
            print(state,"營業中")
            # print("營業中")
            if events[0]["type"] == "message":
                if events[0]["message"]["type"] == "text":
                    text = events[0]["message"]["text"]
                    if userId not in mf.getuseridlist() :
                        if "我的暱稱：" in text:
                            nickname = text[5:]
                            nickname_list = mf.get_nickname_list()
                            if nickname in nickname_list:
                                payload["messages"] = [tf.getAutoReplyText(),tf.getNicknameAlreadyUsed(),f.getUseridNickname()]
                            else:
                                payload["messages"] = [f.getConfirmNickname(nickname)]
                        else:
                            print("Insert Nickname")
                            payload["messages"] = [f.getUseridNickname()]
                    else:
                        Reserve_willing = mf.getUseridstate(userId)
                        nowdate_1,nowtime_1 = f.getnowdateandnowtime()
                        if text == "我要預約" :
                            if mf.CountOrdersofUserid(userId) < 2:
                                yeardate = f.getyeardatedict()
                                if len(yeardate[nowdate_1]) == len(CHECKLIST):
                                    payload["messages"] = [tf.getAutoReplyText(),tf.getHavenoTimeText()]
                                elif nowtime_1 > "23:59":
                                    print(nowtime_1,"超過22:00了")
                                    payload["messages"] = [tf.getOverServicetimeText()]
                                else:
                                    payload["messages"] = [tf.getAutoReplyText(),f.getConfirmReserve()]
                            else:
                                payload["messages"] = [tf.getAutoReplyText(),tf.getReservedtimeIsTwo_Text()]
                        elif Reserve_willing == 1 :
                            if mf.CountOrdersofUserid(userId) < 2:
                                if len(text)==2 and "一樣" in text :
                                    tradeName, partyName = mf.writeintotemporder_thesame(userId)
                                    mf.getChangeUserstate(userId=userId, state=2)
                                    payload["messages"] = [tf.getAutoReplyText(),f.getConfirmRoleName(tradeName, partyName)]
                                elif len(text.split(" ")[0].encode("utf-8")) <= 18 and len(text.split(" ")[1].encode("utf-8")) <= 18 :
                                    mf.getChangeUserstate(userId=userId, state=2)
                                    tradeName, partyName = mf.writeintotemporder_nonthesame( text, userId)
                                    payload["messages"] = [tf.getAutoReplyText(),f.getConfirmRoleName(tradeName, partyName)]
                                else:
                                    payload["messages"] = [tf.getAutoReplyText(),tf.getWrongIdFormat()]
                            else:
                                payload["messages"] = [tf.getReservedtimeIsTwo_Text()]        
                        if text == "查詢預約資訊":
                            payload["messages"] = [f.getUseridOrder(userId)]
                        if text =="測試":
                            payload["messages"] = [test(userId)]
                        if text == "B":
                            payload["messages"] = [tf.getBufforders()]
                        if text =="刪除預約":
                            _, nowtime_delete = f.getnowdateandnowtime()
                            if nowtime_delete > "23:59":
                                print(nowtime_delete,"超過22:00了")
                                payload["messages"] = [tf.getOverServicetimeText()]
                            else:
                                payload["messages"] = [
                                                        tf.getDeleteOrderText(),
                                                        f.getUseridOrder(userId),
                                                        f.getConfirmDeleteOrder()
                                                    ]
                        if text == "今日時間":
                            todayDate, _ = f.getnowdateandnowtime()
                            payload["messages"] = [tf.getAutoReplyText(),f.getFreeTime(todayDate, CHECKLIST)]
                        if text == "全部訂單" and userId in userids:
                            payload["messages"] = [mf.getGetAllorders()]
                        if  "指定時間：" in text and userId in userids:
                            Timelist = text[5:].split(" ")
                            payload["messages"] = [mf.getDeleteSomeOrderList(Timelist)]
                        if text == "我的點數" :
                            if  userId in mf.getuseridlist():
                                print(userId,"in USERIDSLIST")
                                payload["messages"] = [mf.getMypointsCard(userId),mf.getMyPointsText(userId)]
                        if text == "更新點數" and userId in userids:
                            payload["messages"] = [mf.getUpdatePoints()]
                        if text == "切換" and userId in userids:              
                            print("切換為休息")
                            payload["messages"] = [tf.getClosedText()]
                        if text == "兌換":
                            point = mf.getuserIdPoints(userId)
                            if point > 4:
                                payload["messages"] = [f.getConfirmFreeBuff()]
                            else:
                                payload["messages"] = [tf.getDenyExchangeText(point)]
                        if text == "否":
                            mf.getChangeUserstate(userId=userId, state=0)
                            payload["messages"] = [tf.getResetUserState0()]
                    replyMessage(payload)
            elif events[0]["type"] == "postback":
                data = json.loads(events[0]["postback"]["data"])
                action = data["action"]
                userId_state3 = mf.getUseridstate(userId)
                if "params" in events[0]["postback"] and action =='Time chosen' and userId_state3 == 3:
                    if mf.CountOrdersofUserid(userId) < 2:
                        reservedDatetime = events[0]["postback"]["params"]["datetime"].split("T")
                        reservedDate = reservedDatetime[0]
                        reservedTime = reservedDatetime[1]
                        if str(reservedTime)  not in  CHECKLIST :
                                data = json.loads(events[0]["postback"]["data"])
                                print(data)
                                print(f"{reservedTime}不符合格式")
                                payload["messages"] = [ tf.getAutoReplyText(),
                                                        tf.getWrongTimeFormat( str(reservedDate),reservedTime), 
                                                        f.getChooseTimeAgain()
                                                        ]
                        else:
                            payload["messages"] = [ tf.getAutoReplyText(),
                                                    tf.getUserPickedTimeText( str(reservedDate), reservedTime),
                                                    f.getConfirmChooseTime( str(reservedDate), reservedTime, userId=userId)
                                                    ]
                            yeardate = f.getyeardatedict()
                            if str(reservedTime) in yeardate[reservedDate]:
                                print(yeardate[reservedDate],"reservetime list")
                                data = json.dumps({'action':'Time chosen'})
                                mf.getChangeUserstate(userId=userId, state=3)
                                payload["messages"] = [ 
                                                    tf.getReservedTimeText(),
                                                    f.getFreeTime(reservedDate, CHECKLIST),
                                                    f.getChooseTimeAgain()
                                                    ]
                    else:
                        payload["messages"] = [tf.getReservedtimeIsTwo_Text()]  
                    replyMessage(payload)
                else:
                    data = json.loads(events[0]["postback"]["data"])
                    action = data["action"] 
                    userId_state = mf.getUseridstate(userId)
                    if userId_state == 4 and action == "Time_confirmed":
                        mf.writeintotemporder_secondtime(userId, data)
                        payload["messages"] = [tf.getAutoReplyText(),mf.getConfirmFinalOrder(userId)]
                    elif action == 'Reserve_willing':
                        mf.getChangeUserstate(userId=userId, state=1)
                        payload["messages"] = [ tf.getAutoReplyText(),
                                                tf.getRoleNames(),
                                                tf.getRoleNamesExample1(),
                                                tf.getRoleNamesExample2()
                                            ]
                    elif userId_state == 2 and action == 'tradeName&partyName confirmed':
                        todayDate, _ = f.getnowdateandnowtime()
                        mf.getChangeUserstate(userId=userId, state=3)
                        payload["messages"] = [tf.getAutoReplyText(),
                                               f.getFreeTime(todayDate, CHECKLIST),
                                               f.getChooseTime(data)
                                               ]
                    elif action == 'FinalOrder confirmed':
                        thisuser_yeardate_time = f.getuseridyeardatetime(userId)
                        mf.getChangeUserstate(userId=userId, state=5)
                        yeardate = f.getyeardatedict()
                        if thisuser_yeardate_time[1] not in yeardate[thisuser_yeardate_time[0]]:
                            yeardate[thisuser_yeardate_time[0]].append(thisuser_yeardate_time[1])
                            ordered_time_list = yeardate[thisuser_yeardate_time[0]]
                            print("時間未被選過",yeardate)
                            payload["messages"] = [tf.getAutoReplyText(),
                                                   mf.getRealFinalOrder(userId, ordered_time_list, checklist=CHECKLIST),
                                                   f.getUseridOrder(userId),
                                                   tf.getBufforders()]
                        else:
                            print(f"差一點，就在剛剛{thisuser_yeardate_time[1]}被預約走了，請選擇其他時間")
                            mf.getalmosttakeorder(userId, thisuser_yeardate_time)
                            data = json.dumps({'action':'Time chosen'})
                            payload["messages"] = [ tf.getAutoReplyText(),
                                                    tf.getAfterOtherUsersText(thisuser_yeardate_time[1]),
                                                    f.getChooseTimeAgain()
                                                    ]
                    if action == 'Delete order':
                        payload["messages"] = [mf.getChooseDeleteTime(userId)]
                    if action == 'Time want to delete':
                        deletedtime = data["time"]
                        payload["messages"] = [f.getComfirmTimetoDelete(deletedtime)]
                    if action == 'Surely delete the time':
                        surelydeletedtime = data["time"]
                        payload["messages"] = [mf.getDeleteTimeSurelyText(surelydeletedtime, userId),
                                               f.getUseridOrder(userId)]
                    if action == 'My nickname example':
                        example1, example2, example3 = tf.getNicknameExample()
                        payload["messages"] = [ example1, example2, example3]
                    if action == 'confirm nickname':
                        nickname = data["nickname"]
                        mf.update_nickname_list(nickname)
                        mf.getPoints_write_into_useridpoints( userId, nickname)
                        payload["messages"] = [tf.getRewardCardSuccesslyText()]
                    if action == 'Exchange confirmed':
                        point = mf.getuserIdPoints(userId)
                        if point < 5:
                            payload["messages"] = [tf.getDenyExchangeText(point)]
                        else:
                            point -= 5
                            lock = threading.Lock()
                            with lock:
                                try:
                                    mydb = myclient["buff_online"]
                                    mycol = mydb["userid_points"]
                                    mydoc = mycol.update_one({"_id":userId},{"$set":{"points":point}})
                                    print("兌換成功")
                                except:
                                    print("兌換失敗")
                            Text1, Text2 = tf.getExchangeSuccesslyText(point)
                            payload["messages"] = [Text1, Text2]
                    replyMessage(payload)

    return 'OK'

'''Flask 首頁'''
@app.route("/", methods=['POST', 'GET'])
def index():
    return render_template('index.html')


# 使用更安全的密碼哈希存储
# from werkzeug.security import generate_password_hash, check_password_hash

# 使用資料庫儲存用户信息(裡用示例字典)
users_db = mf.getUserdata()

# 使用UserMixin來實現User類別
class User(UserMixin):
    def __init__(self, username, password=None, role='user'):
        self.id = username
        self.password = str(password)  # 將密碼轉換為字符串
        self.role = role
    
    def check_password(self, input_password):
        # 將輸入的密碼也轉換為字符串後比較
        return str(input_password) == self.password
    
    def is_admin(self):
        return self.role == 'admin'
    
    def set_password(self, password):
        self.password = str(password)

# 將資料庫數據轉換為 User 對象的字典
def convert_to_users(db_data):
    users = {}
    for username, data in db_data.items():
        # 特殊的統計鍵可以改成pass但本次測試還是當作使用者帳戶
        if username in ['會員總數', '是否為會員']:
            users[username] = User(
            username=username,
            password=data['password'],  
            role=data.get('role', data['role'])
        )
            
        users[username] = User(
            username=username,
            password=data['password'],  
            role=data.get('role', data['role'])
        )
    return users

# 初始化用戶數據
users_db = convert_to_users(users_db)

# 加載用戶
@login_manager.user_loader
def load_user(username):
    users_db = convert_to_users(mf.getUserdata())
    
    if username not in users_db:
        return None
    user = users_db[username]
    return User(username=username, password=user.password, role=user.role)

# 登入頁面
@app.route('/login', methods=['GET', 'POST'])
def login():
    
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')   

        if not username or not password:
            flash('請輸入用戶名和密碼')
            return render_template('login.html')
        
        users_db = convert_to_users(mf.getUserdata())    
        user = users_db.get(username)

        if user and user.check_password(password):
            login_user(user, remember=True)
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        
        flash('用户名或密碼錯誤')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'user')  # 預設為普通用戶
        print(role)
        print(request.form)
        if not username or not password:
            flash('请填寫所有字段')
            return render_template('register.html')
            
        if username in users_db:
            flash('用户名已存在')
            return render_template('register.html')
            
        user = User(username, role=role)
        user.set_password(password)
        users_db[username] = username
        new_user = {
            "username": username,
            "password": str(password),  #應加密
            "role": role
        }
        try:
            mf.getPoints_write_into_useridpoints_web(new_user)
        except Exception as e:
            print(f"註冊錯誤: {e}")
            flash('註冊失敗，請稍後重試')
            return render_template('register.html')
        flash('註冊成功！请登入')
        return redirect(url_for('login'))
        
    return render_template('register.html')

# 儀表板頁面（僅限登入用戶）
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('user_dashboard'))

@app.route('/dashboard/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('沒有權限訪問該頁面')
        return redirect(url_for('dashboard'))
    return render_template('admin_dashboard.html')

'''歷史紀錄頁面for admin'''
@app.route('/dashboard/admin/history', methods=['GET', 'POST'])
@login_required
def admin_history():
    if not current_user.is_admin():
        flash('沒有權限訪問該頁面')
        return redirect(url_for('dashboard'))
    
    request_method = request.method
    orders = []
    
    if request_method == 'POST':
        date = str(request.form.get('history'))
        date = date.replace("-","")[2:]
        print(date)
        orders = f.gethistoryfinalOrder(date)
        return render_template(
            'admin_history.html',  # 修改為管理員專用的模板
            request_method=request_method,
            orders=orders,
        )
    return render_template('admin_history.html')  # 修改為管理員專用的模板

'''訂單頁面 for admin'''
@app.route('/dashboard/admin/order', methods=['GET', 'POST'])
def admin_order():
    request_method = request.method
    orders = []
    
    if request_method == 'POST' :
        # username = request.form['order']
        # print(username)
        date = str(request.form.get('specied order'))
        date = date.replace("-","")[2:]
        print(date)
        orders = mf.getWebGetAllOrder(date)
    return render_template(
        'admin_order.html',
        request_method=request_method,
        orders=orders,
    )

'''dashboard for user'''
@app.route('/dashboard/user')
@login_required
def user_dashboard():
    return render_template('user_dashboard.html')

'''dashboard for user to check order in the past'''
@app.route('/dashboard/user/history', methods=['GET', 'POST'])
@login_required
def user_history():
    request_method = request.method
    if request_method == 'POST' :
        try:
            userId, order_date_history = mf.getWebUserHistoryOrder(current_user.id)
            order_history_list = mf.get_user_order_history(userId, order_date_history)
        except:
            order_history_list = ["查無資料"]
        return render_template(
            'user_dashboard.html',
            request_method=request_method,
            orders=order_history_list,
        )
    else:
        return redirect(url_for('user_dashboard'))  

# 登出功能
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已成功登出')
    return redirect(url_for('login'))



'''測試函式'''
def test(userId):
    message = {
  "type": "text",
  "text": "test"
}
    if userId in userids:
        return message



'''利用Line api 中 reply分類作為機器人回覆功能的主要函式'''
def replyMessage(payload):
    url='https://api.line.me/v2/bot/message/reply'
    response = requests.post(url,headers=HEADER,json=payload)
    
    print(response.status_code)
    print(response.text)
    return 'OK'

if __name__ == "__main__":
    app.debug = True
    # app.run(debug=True, port=5000, host="0.0.0.0")
    app.run()
