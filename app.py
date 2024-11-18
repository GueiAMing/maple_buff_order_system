from __future__ import unicode_literals
from flask import Flask, request, abort, render_template
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

app = Flask(__name__, static_url_path='/static')
CHECKLIST = ['20:00', '20:05', '20:10', '20:15', '20:20', '20:25', '20:30', '20:35', '20:40', '20:45', '20:50', '20:55', '21:00', '21:05', '21:10', '21:15', '21:20', '21:25', '21:30', '21:35', '21:40', '21:45', '21:50', '21:55', '22:00']

USERID_TRADER_PARTNER = dict()

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
mydb = myclient["buff_online"]
mycol = mydb["yeardate_time"]
tzone = timezone(timedelta(hours=8))
now = datetime.now(tz=tzone)
id = now.isoformat()[5:7]
mydoc = mycol.find_one({"_id":str(id)},{'_id': 0})
YEARDATEDICT = mydoc
print("YEARDATEDICT in code:",YEARDATEDICT)
# YEARDATEDICT[today.isoformat()[:10]] = CHECKLIST
mycol = mydb["userid_yeardate_time"]
mydoc = mycol.find({},{"_id": 0,"userid":0})
# mydoc = mycol.find({})
print(mydoc)
USERID_YEARDATE_TIME = dict()
for data in mydoc:
    print(data)
    eachuserid = list(data.keys())[0]      
    USERID_YEARDATE_TIME[eachuserid] = data[eachuserid]
print(USERID_YEARDATE_TIME)
mycol = mydb["userid_points"]
mydoc = mycol.find_one({"_id": "1"})
USERIDSLIST=set(mydoc["userids"])
print(mydoc)
print("USERIDSLIST：",USERIDSLIST)
userids = ['U66da2ba27e83014da52f28455ef19c7c', 'Uf8e734e58b67c12e0de1cd574a1718da']
HEADER = {
    'Content-type': 'application/json',
    'Authorization': F'Bearer {config.get("line-bot", "channel_access_token")}'
}

@app.route("/callback", methods=['POST', 'GET'])
def index():
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
        print("useridtype:",type(userId))
        state = getNowState()
        if state == 0:
            text = events[0]["message"]["text"]
            if text == "切換" and userId in userids:

                payload["messages"] = [getOpenText()]
            else:
                print("今日休息")
                payload["messages"] = [getTodayClosedText()]
            replyMessage(payload)
        else: 
            print(state,"營業中")
            # print("營業中")
            if events[0]["type"] == "message":
                if events[0]["message"]["type"] == "text":
                    text = events[0]["message"]["text"]

                    if userId not in USERIDSLIST :
                        if "我的暱稱：" in text:
                            nickname = text[5:]
                            payload["messages"] = [getConfirmNickname(nickname)]
                        else:
                            payload["messages"] = [getUseridNickname(userId)]
                    else:
                        tzone = timezone(timedelta(hours=8))
                        nowdatetime = datetime.now(tz=tzone)
                        nowdate = nowdatetime.isoformat().split("T")[0]
                        nowtime = nowdatetime.isoformat().split("T")[1]
                        if text == "我要預約" :
                            if CountOrdersofUserid(userId) < 2:
                                if len(YEARDATEDICT[nowdate]) == len(CHECKLIST):
                                    payload["messages"] = [getHavenoTime()]
                                elif nowtime > "21:54":
                                    print(nowtime,"超過22:00了")
                                    payload["messages"] = [getOverServicetime()]
                                else:
                                    payload["messages"] = [getConfirmReserve()]
                            else:
                                payload["messages"] = [getReservedtimeIsTwo()]
                        elif len(text.split(" ")) == 2:
                            tradeName = text.split(" ")[0]
                            partyName = text.split(" ")[1]
                            if CountOrdersofUserid(userId) < 2:
                                if len(tradeName.encode("utf-8")) <= 18 and len(partyName.encode("utf-8")) <= 18:
                                    USERID_TRADER_PARTNER[userId] = [ tradeName, partyName] 
                                    tzone = timezone(timedelta(hours=8))
                                    nowtime = datetime.now(tz=tzone).isoformat()[:16] 
                                    lock = threading.Lock()
                                    with lock:
                                        try:
                                            mydb = myclient["buff_online"]
                                            mycol = mydb[f"temp_order"]
                                            mycol.update_one({"userId":userId},{"$set":{
                                                                                        'userId':userId,
                                                                                        "writetime":nowtime,
                                                                                        'Date':"",
                                                                                        'time':"",
                                                                                        'location':"六條岔道",
                                                                                        'trade_name':tradeName,
                                                                                        'party_name':partyName,
                                                                                        'point':"1",
                                                                                        }
                                                                                        },
                                                                                        True
                                                        )
                                            tzone = timezone(timedelta(hours=8))
                                            nowtime = datetime.now(tz=tzone).isoformat()[:16]
                                            mydb = myclient["buff_online"]
                                            mycol = mydb["userid_points"]
                                            mydoc = mycol.find_one({"_id":userId},{"_id":0, "nickname": 1})
                                            nicknameofthisuser = mydoc["nickname"]
                                            data = [
                                                    #['write_yeardate_time','userid',       'nickname'         , 'date' ,  'time' , 'trade_name', 'party_name','remark']
                                                    [      nowtime        , userId  ,    nicknameofthisuser    ,  None  ,   None  ,   tradeName ,  partyName  ,f'{nicknameofthisuser}，確認角色IDs']
                                                ]
                                            file_path = './Data/temp_order.csv'
                                            file_exists = os.path.isfile(file_path)
                                            
                                            with open( file_path, 'a', newline='',encoding='utf-8') as csvfile:

                                                csv_writer = csv.writer(csvfile)
                                                if not file_exists:
                                                    csv_writer.writerow(['write_yeardate_time','userid',    'nickname'    ,     'date'     ,    'time'    , 'trade_name', 'party_name','remark'])
                                                csv_writer.writerows(data)
                                                print(f'已成功寫入 {file_path}')
                                            print(f"userId:{userId}的交易角色ID:{tradeName}、組隊角色ID:{partyName}，寫入成功。")
                                        except:
                                            print(f"userId:{userId}的交易角色ID:{tradeName}、組隊角色ID:{partyName}，寫入失敗。")

                                    payload["messages"] = [getConfirmRoleName(tradeName, partyName)]
                                else:
                                    payload["messages"] = [getWrongIdFormat()]
                            else:
                                payload["messages"] = [getReservedtimeIsTwo()]        
                        if text == "查詢預約資訊":
                            payload["messages"] = [getUseridOrder(userId)]
                        if text =="測試":
                            payload["messages"] = [test(userId)]
                        if text =="刪除預約":
                            if nowtime > "21:54":
                                print(nowtime,"超過22:00了")
                                payload["messages"] = [getOverServicetime()]
                            else:
                                payload["messages"] = [
                                                        getDeleteOrderText(),
                                                        getUseridOrder(userId),
                                                        getConfirmDeleteOrder()
                                                    ]
                        if text == "今日時間":
                            tzone = timezone(timedelta(hours=8))
                            todayDate = datetime.now(tz=tzone).isoformat().split("T")[0]
                            payload["messages"] = [getFreeTime(todayDate)]
                        if text == "全部訂單" and userId == "Uf8e734e58b67c12e0de1cd574a1718da":
                            payload["messages"] = [getGetAllorders()]
                        if  "指定時間：" in text and userId == 'Uf8e734e58b67c12e0de1cd574a1718da':
                            Timelist = text[5:].split(" ")
                            payload["messages"] = [getDeleteSomeOrderList(Timelist)]
                        if text == "我的點數" :
                            if  userId in USERIDSLIST:
                                print(userId,"in USERIDSLIST")
                                payload["messages"] = [getMyPoints(userId)]
                        if text == "更新點數" and userId == 'Uf8e734e58b67c12e0de1cd574a1718da':
                            payload["messages"] = [getUpdatePoints()]
                        if text == "切換" and userId in userids:
                            
                            print("切換為休息")
                            payload["messages"] = [getClosedText()]
                        if text == "兌換":
                            point = getuserIdPoints(userId)
                            if point > 4:
                                payload["messages"] = [getConfirmFreeBuff()]
                            else:
                                payload["messages"] = [getDenyExchangeText(point)]
                    replyMessage(payload)
            elif events[0]["type"] == "postback":
                data = json.loads(events[0]["postback"]["data"])
                action = data["action"]
                if "params" in events[0]["postback"] and action =='Time chosen':
                    
                    reservedDatetime = events[0]["postback"]["params"]["datetime"].split("T")
                    reservedDate = reservedDatetime[0]
                    reservedTime = reservedDatetime[1]
                    if str(reservedTime)  not in  CHECKLIST :
                            data = json.loads(events[0]["postback"]["data"])
                            print(data)
                            print(f"{reservedTime}不符合格式")
                            payload["messages"] = [ 
                                                    getWrongTimeFormat( str(reservedDate),reservedTime), 
                                                    getChooseTimeAgain()
                                                    ]
                    else:
                        payload["messages"] = [getConfirmChooseTime( str(reservedDate), reservedTime)]
                        
                        if str(reservedTime) in YEARDATEDICT[reservedDate]:
                            data = json.dumps({'action':'Time chosen'})
                            payload["messages"] = [ 
                                                getReservedTime(),
                                                getFreeTime(reservedDate),
                                                getChooseTimeAgain()
                                                ]
                    replyMessage(payload)
                else:
                    data = json.loads(events[0]["postback"]["data"])
                    action = data["action"]
                    
                    if action == "Time_confirmed":
                        lock = threading.Lock()
                        reservedDate = data["Date"]
                        reservedTime = data["Time"]
                        yearDate = reservedDate
                        USERID_YEARDATE_TIME[userId]=[yearDate,reservedTime]
                        tzone = timezone(timedelta(hours=8))
                        nowtime = datetime.now(tz=tzone).isoformat()[:16]
                        with lock:
                            try:
                                mydb = myclient["buff_online"]
                                mycol = mydb[f"temp_order"]
                                mycol.update_one({"userId":userId},{"$set":{
                                                                            'userId':userId,
                                                                            'Date':reservedDate,
                                                                            'time':reservedTime,
                                                                            'writetime':nowtime
                                                                            }
                                                                            },
                                                                            True
                                                )
                                tzone = timezone(timedelta(hours=8))
                                nowtime = datetime.now(tz=tzone).isoformat()[:16]
                                mydb = myclient["buff_online"]
                                mycol = mydb["userid_points"]
                                mydoc = mycol.find_one({"_id":userId},{"_id":0, "nickname": 1})
                                nicknameofthisuser = mydoc["nickname"]
                                data = [
                                        #['write_yeardate_time','userid',    'nickname'    ,     'date'     ,    'time'    , 'trade_name', 'party_name','remark']
                                        [      nowtime        , userId ,nicknameofthisuser,  reservedDate  , reservedTime ,     None    ,     None    ,f'{nicknameofthisuser}，確認預約時間']
                                    ]
                                
                                file_path = './Data/temp_order.csv'
                                file_exists = os.path.isfile(file_path)
                
                                with open( file_path, 'a', newline='',encoding='utf-8') as csvfile:

                                    csv_writer = csv.writer(csvfile)
                                    if not file_exists:
                                        csv_writer.writerow(['write_yeardate_time','userid',    'nickname'    ,     'date'     ,    'time'    , 'trade_name', 'party_name','remark'])
                                    csv_writer.writerows(data)
                                    print(f'已成功寫入 {file_path}')
                                
                                print(f"userId:{userId}，把預約時間{reservedDate} {reservedTime}寫到temp_order成功。")
                            except:
                                print(f"userId:{userId}，把預約時間{reservedDate} {reservedTime}寫到temp_order失敗。")
                        lock = threading.Lock()
                        with lock:
                            try:
                                mydb = myclient["buff_online"]           
                                mycol = mydb["userid_yeardate_time"]
                                mycol.update_one({"userid":userId},{"$set":{
                                                                            userId:[reservedDate,reservedTime]
                                                                            }
                                                                            },
                                                                            True
                                                )
                                tzone = timezone(timedelta(hours=8))
                                nowtime = datetime.now(tz=tzone).isoformat()[:16]
                                mydb = myclient["buff_online"]
                                mycol = mydb["userid_points"]
                                mydoc = mycol.find_one({"_id":userId},{"_id":0, "nickname": 1})
                                nicknameofthisuser = mydoc["nickname"]
                                data = [
                                        #['write_yeardate_time', 'userid' ,     'nickname'     ,  'yeardate'  ,    'time'    ,   'remark']
                                        [      nowtime        ,  userId  , nicknameofthisuser , reservedDate , reservedTime ,f'{nicknameofthisuser}，確認預約時間並把選擇日期時間寫入暫時資料庫']
                                    ]
                                
                                file_path = "./Data/userid_yeardate_time.csv"
                                file_exists = os.path.isfile(file_path)
                                with open(file_path, 'a', newline='',encoding='utf-8') as csvfile:
                                    csv_writer = csv.writer(csvfile)
                                    if not file_exists:
                                        csv_writer.writerow(['write_yeardate_time', 'userid' ,     'nickname'     ,   'yeardate'  ,    'time'    ,   'remark'])
                                    csv_writer.writerows(data)
                                    print(f'已成功寫入 {file_path}')

                                
                                print("更新userId的選擇日期和時間到資料庫yeardate_time成功。")
                            except:
                                print("更新userId的選擇日期和時間到資料庫yeardate_time失敗。")
                        tradeName = USERID_TRADER_PARTNER[userId][0]
                        partyName = USERID_TRADER_PARTNER[userId][1]
                        payload["messages"] = [getConfirmFinalOrder(userId, tradeName, partyName)]
                    elif action == 'Reserve_willing':
                        payload["messages"] = [
                                                getRoleNames(),
                                                getRoleNamesExample1(),
                                                getRoleNamesExample2()
                                            ]
                    elif action == 'tradeName&partyName confirmed':
                        # data = json.loads(events[0]["postback"]["data"])
                        # tradeName = data['trader_name']
                        # partyName = data['party_name']
                        
                        payload["messages"] = [getChooseTime(data)]
                    elif action == 'FinalOrder confirmed':
                        if USERID_YEARDATE_TIME[userId][1] not in YEARDATEDICT[USERID_YEARDATE_TIME[userId][0]]:
                            YEARDATEDICT[USERID_YEARDATE_TIME[userId][0]].append(USERID_YEARDATE_TIME[userId][1])
                            print("時間未被選過",YEARDATEDICT)
                            payload["messages"] = [getRealFinalOrder(userId)]
                        else:
                            print(f"差一點，就在剛剛{USERID_YEARDATE_TIME[userId][1]}被預約走了，請選擇其他時間")
                            tzone = timezone(timedelta(hours=8))
                            nowtime = datetime.now(tz=tzone).isoformat()[:16]
                            mydb = myclient["buff_online"]
                            mycol = mydb["userid_points"]
                            mydoc = mycol.find_one({"_id":userId},{"_id":0, "nickname": 1})
                            nicknameofthisuser = mydoc["nickname"]
                            final_order_dbname = nowtime.split("T")[0].replace("-","")[2:]
                            data = [
                                    #['write_yeardate_time',  'userid'  ,     'nickname'     , 'action' ,           'yeardate'            ,               'time'            ,           'tradename'            ,            'partyname'           ,  'location'  ,  'remark']
                                    [      nowtime         ,   userId   , nicknameofthisuser , "Later!" , USERID_YEARDATE_TIME[userId][0] , USERID_YEARDATE_TIME[userId][1] , USERID_TRADER_PARTNER[userId][0] , USERID_TRADER_PARTNER[userId][1] ,  "六條岔道"   ,f'{nicknameofthisuser}，要確認訂單時被搶先一步']
                                ]
                            
                            file_path = f'./Data/final_order_{final_order_dbname}.csv'
                            file_exists = os.path.isfile(file_path)
                            with open(file_path, 'a', newline='',encoding='utf-8') as csvfile:
                                csv_writer = csv.writer(csvfile)
                                if not file_exists:
                                    csv_writer.writerow(['write_yeardate_time',  'userid'  ,     'nickname'     , 'action' ,           'yeardate'            ,               'time'            ,           'tradename'            ,            'partyname'           ,  'location'  ,  'remark'])
                                csv_writer.writerows(data)
                                print(f'已成功寫入 {file_path}')

                            data = json.dumps({'action':'Time chosen'})
                            payload["messages"] = [
                                                    getAfterOtherUsersText(USERID_YEARDATE_TIME[userId][1]),
                                                    getChooseTimeAgain()
                                                    ]
                    if action == 'Delete order':
                        payload["messages"] = [getChooseDeleteTime(userId)]
                    if action == 'Time want to delete':
                        deletedtime = data["time"]
                        payload["messages"] = [getComfirmTimetoDelete(deletedtime)]
                    if action == 'Surely delete the time':
                        surelydeletedtime = data["time"]
                        payload["messages"] = [getDeleteTimeSurelyText(surelydeletedtime, userId)]
                    if action == 'My nickname example':
                        example1, example2 = getNicknameExample()
                        payload["messages"] = [ example1, example2]
                    if action == 'confirm nickname':
                        nickname = data["nickname"]
                        getPoints(userId, nickname)
                        payload["messages"] = [getRewardCardSuccessly()]
                    if action == 'Exchange confirmed':
                        point = getuserIdPoints(userId)
                        if point < 5:
                            payload["messages"] = [getDenyExchangeText(point)]
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
                            Text1, Text2 = getExchangeSuccesslyText(point)
                            payload["messages"] = [Text1, Text2]
                    replyMessage(payload)

    return 'OK'

'''請客戶點選按鈕輸入暱稱'''
def getUseridNickname(userId):
    message = {
    "type": "flex",
    "altText": "this is a flex message",
    "contents": {
            "type": "bubble",
            "header": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "text",
                            "text": "請點選下方按鈕提供您的暱稱，方便我記錄您的點數，並贈送您一點",
                            "wrap": True
                        }
                        ]
                    },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                        "type": "postback",
                        "label": "點我",
                        "data": json.dumps({"action":"My nickname example"}),
                        "inputOption": "openKeyboard",
                        "fillInText":"我的暱稱："
                    }
                },
                
                ]
            }
            }
    }
    return message

'''暱稱範例'''
def getNicknameExample():
    message = [{
                "type":"text",
                "text":"例如："
                },
                {
                "type":"text",
                "text":"我的暱稱：明明"
                }
                # {
                # "type":"text",
                # "text":"注意！\n\"我的暱稱：\"也要輸入"
                # }
    ]

    return message[0],message[1]

'''確認客戶暱稱'''
def getConfirmNickname(nickname):
    data = json.dumps({'nickname':nickname, 'action':'confirm nickname'})
    message = {
                "type": "template",
                "altText": "this is a confirm template",
                "template": {
                    "type": "confirm",
                    "text": f"是否您的暱稱為\"{nickname}\"",
                    "actions": [
                    {
                        "type": "postback",
                        "label": "是",
                        "data": data,
                        "displayText": "是",
                    },
                    {
                        "type": "message",
                        "label": "否",
                        "text": "否"
                    }
                    ]

                }
            }
    return message

'''發點數卡'''
def getPoints(userId, nickname):
    print(userId,"in getpoints")
    USERIDSLIST.add(userId)
    print(USERIDSLIST)
    lock = threading.Lock()
    tzone = timezone(timedelta(hours=8))
    nowyeardatetime = datetime.now(tz=tzone)
    nowyeardatetime = nowyeardatetime.isoformat()[:16].replace("T","-")
    with lock:
        try:
            mydb = myclient["buff_online"]
            mycol = mydb["userid_points"]
            mycol.update_one({"_id": "1"},{"$set":{"userids":list(USERIDSLIST)}})
            mycol.insert_one({"_id":userId,"nickname":nickname,"got_reward_card_time":nowyeardatetime,"points":1})
            print(f"{userId}獲得點數卡")
        except:
            print(f"{userId}獲得點數卡，失敗")

'''領取點數卡成功'''
def getRewardCardSuccessly():
    message = {
                "type":"text",
                "text":"已領取點數卡，可以進行預約了"
                }
    

    return message

'''確認預定意願'''
def getConfirmReserve():
    data = json.dumps({'action':'Reserve_willing'})
    message = {
        "type": "template",
        "altText": "this is a confirm template",
        "template": {
            "type": "confirm",
            "text": "是否要預約\"艾麗亞\"伺服器的Buff機？",
            "actions": [
            # {
            #     "type": "postback",
            #     "label": "是",
            #     "data": data,
            # },
                {
                "type": "postback",
                "label": "是",
                "data": data,
                "displayText": "是",
                "inputOption": "openKeyboard",
                
                },
                {
                    "type": "message",
                    "label": "否",
                    "text": "否"
                }
            ]
        }
    }
    
    return message

'''輸入交易角色ID，組隊角色ID'''
def getRoleNames():
    # data = json.dumps({data:userId})
    message ={
                "type": "text",
                "text": "請輸入交易角色ID及組隊角色ID\n用(空格)隔開"
             }
    

    return message

def getRoleNamesExample1():
    message ={
                "type": "text",
                "text": "例如："
             }

    return message

def getRoleNamesExample2():
    message ={
                "type": "text",
                "text": "歸01 歸01"
             }

    return message

'''角色ID格式錯誤'''
def getWrongIdFormat():
    message = {
        "type" : "text",
        "text" : "角色ID長度不符合，請重新輸入"
    }
    return message

'''確認交易角色ID，組隊角色ID'''
def getConfirmRoleName(tradeName, partyName):
    data = json.dumps({'trader_name':tradeName, 'party_name':partyName, 'action':'tradeName&partyName confirmed'})
    message = {
                "type": "template",
                "altText": "this is a confirm template",
                "template": {
                    "type": "confirm",
                    "text": f"交易角色:{tradeName}\n組隊角色:{partyName}",
                    "actions": [
                    {
                        "type": "postback",
                        "label": "是",
                        "data": data,
                        "displayText": "是",
                    },
                    {
                        "type": "message",
                        "label": "否",
                        "text": "否"
                    }
                    ]

                }
            }
    return message

'''確認意願後第一次選擇時間'''
def getChooseTime(data):
    data = json.dumps({'action':'Time chosen'})
    tzone = timezone(timedelta(hours=8))
    initial_datetime = datetime.now(tz=tzone) + timedelta(minutes=30)
    max_datetime = initial_datetime.isoformat().split("T")[0] + "t22:00"
    format_initial_datetime = initial_datetime.isoformat()[:16]
    message = {
                "type": "template",
                "altText": "This is a buttons template",
                "template": {
                    "type": "buttons",
                    "text": "選擇晚上八~十點，5的倍數分鐘",
                    "actions": [
                    {
                        "type": "datetimepicker",
                        "label": "\"點我\"來選擇時間",
                        "data": data,
                        "mode": "datetime",
                        "initial": str(format_initial_datetime),
                        "max": str(max_datetime),
                        "min": str(format_initial_datetime)
                        # "initial": "2017-12-25T00:00",
                        # "max": "2018-01-24T23:59",
                        # "min": "2017-12-25T00:00"
                    }
                    ]
                }
             }
    return message

'''選擇時間不在服務時間上所以重選(選擇非五的倍數時間或已被預約的時間)'''
def getWrongTimeFormat(reservedDate, reservedTime):
    message ={
        
                "type": "text",
                "text": f"您輸入的日期時間為{reservedDate} {reservedTime}，請輸入正確時間\n如20：05、20：10"
             }

    return message

'''時間被預訂走了的提示訊息'''
def getReservedTime():
    message ={
        
                "type": "text",
                "text": "您輸入的日期時間已被預定，請重新選擇時間"
             }

    return message

'''顯示空閒時間'''
def getFreeTime(reservedDate):
    tzone = timezone(timedelta(hours=8))
    nowtime = datetime.now(tz=tzone) + timedelta(minutes=6)
    nowtime = nowtime.isoformat().split("T")[1][:5]
    chosen_times = YEARDATEDICT[reservedDate] 
    not_chosen_times = [time for time in CHECKLIST if time not in chosen_times and time > nowtime]
    text0 ="目前空閒時間\n"
    text = ""
    for i in range(len(not_chosen_times)):
        text += not_chosen_times[i] + "；"
        if i%4 == 3:
            text += "\n"
    message={
            "type": "text",
            "text": text0 + text
    }
    return message

'''時間被預訂走了，重新選擇時間'''
def getChooseTimeAgain():
    data = json.dumps({'action':'Time chosen'})
    tzone = timezone(timedelta(hours=8))
    initial_datetime = datetime.now(tz=tzone) + timedelta(minutes=30)
    max_datetime = initial_datetime.isoformat().split("T")[0] + "t22:00"
    format_initial_datetime = initial_datetime.isoformat()[:16]
    
    message = {
                "type": "template",
                "altText": "This is a buttons template",
                "template": {
                    "type": "buttons",
                    "text": "請重新選擇時間(5的倍數分鐘)",
                    "actions": [
                    {
                        "type": "datetimepicker",
                        "label": "\"點我\"來選擇時間",
                        "data": data,
                        "mode": "datetime",
                        "initial": str(format_initial_datetime),
                        "max": str(max_datetime),
                        "min": str(format_initial_datetime)
                    }
                    ]
                }
             }
    return message

'''確認第一次選擇的時間'''
def getConfirmChooseTime(reservedDate, reservedTime):
    data = json.dumps({'Date':reservedDate,'Time':reservedTime,'action':"Time_confirmed"})
    message = {
        "type": "template",
        "altText": "this is a confirm template",
        "template": {
            "type": "confirm",
            "text": f"是否要預約日期{reservedDate} {reservedTime}的Buff機？",
            "actions": [
            {
                "type": "postback",
                "label": "是",
                "data": data,
                "displayText": "是",
            },
            {
                "type": "message",
                "label": "否",
                "text": "否"
            }
            ]
        }
    }

    return message

'''確認最後訂單'''
def getConfirmFinalOrder(userId, tradeName, partyName):
    data = json.dumps({'action':'FinalOrder confirmed'})
    message = {
                "type": "template",
                "altText": "this is a confirm template",
                "template": {
                    "type": "confirm",
                    "text": f"訂單確認：\n交易時間:{USERID_YEARDATE_TIME[userId][0]} {USERID_YEARDATE_TIME[userId][1]}\n交易角色:{tradeName}\n組隊角色:{partyName}",
                    "actions": [
                    {
                        "type": "postback",
                        "label": "是",
                        "data": data,
                        "displayText": "是",
                    },
                    {
                        "type": "message",
                        "label": "否",
                        "text": "否"
                    }
                    ]
                }
            }
    return message

'''訂單確認成功，把暫時資料庫的資料寫入最終訂單資料庫'''
def getRealFinalOrder(userId):
    yeardate = USERID_YEARDATE_TIME[userId][0]                                                              
    time = USERID_YEARDATE_TIME[userId][1]
    lock =threading.Lock()
    with lock:
        try:
            id = datetime.now().isoformat()[5:7]
            mydb = myclient["buff_online"]
            mycol = mydb["yeardate_time"]
            mycol.update_one({'_id':id},{'$set':{yeardate:YEARDATEDICT[yeardate]}},True)
            print("日期的時間清單更新成功")
        except:
            print("日期的時間清單更新失敗")

    yeardate = yeardate.replace("-","")[2:]
    mycol = mydb[f"temp_order"]
    mydoc = mycol.find_one({"userId":userId},{"_id":0})
    dict = mydoc
    lock =threading.Lock()
    with lock:
        try:
            mydb = myclient["buff_online"]
            mycol = mydb[f"final_order_{yeardate}"]
            time_id = CHECKLIST.index(time)
            # mycol.insert_one({"_id":str(time_id).zfill(2)})
            mycol.update_one({"_id":str(time_id).zfill(2)},{"$set":dict},True)
            print("暫時訂單寫入確認訂單成功。")
            tzone = timezone(timedelta(hours=8))
            nowtime = datetime.now(tz=tzone).isoformat()[:16]
            mydb = myclient["buff_online"]
            mycol = mydb["userid_points"]
            mydoc = mycol.find_one({"_id":userId},{"_id":0, "nickname": 1})
            nicknameofthisuser = mydoc["nickname"]
            final_order_dbname = nowtime.split("T")[0].replace("-","")[2:]

            values_list = [dict[key] for key in dict]
            data = [
                    #['write_yeardate_time',    'userid'    ,     'nickname'     , 'action' ,    'yeardate'   ,     'time'     ,  'tradename'   ,  'partyname'   ,  'location'  ,  'remark']
                     [      nowtime        ,     userId     , nicknameofthisuser , "Insert" ,values_list[1] , values_list[5] , values_list[6] , values_list[3] ,values_list[2],f'{nicknameofthisuser}，暫時資料庫的資料寫入最終訂單']
                ]
            file_path = f'./Data/final_order_{final_order_dbname}.csv'
            file_exists = os.path.isfile(file_path)
            with open(file_path, 'a', newline='',encoding='utf-8') as csvfile:
                csv_writer = csv.writer(csvfile)
                if not file_exists:
                    csv_writer.writerow(['write_yeardate_time',    'userid'    ,     'nickname'     , 'action' ,    'yeardate'   ,     'time'     ,  'tradename'   ,  'partyname'   ,  'location'  ,  'remark'])
                csv_writer.writerows(data)
                print(f'已成功寫入 {file_path}')

            message ={
        
                "type": "text",
                "text": "恭喜訂單成立"
             }
            print(f'寫入成功到final_order_{yeardate}：',dict)

        except:
            data = json.dumps({'action':'Time chosen'})
            message = getChooseTimeAgain()
            print("暫時訂單寫入確認訂單失敗。")
    return message

'''被其他使用者搶先預約'''
def getAfterOtherUsersText(reservedtime):
    
    message = {
                "type":"text",
                "text":f"差一點，就在剛剛{reservedtime}被其他人預約走了，請選擇其他時間"
    }

    return message

'''查詢預約資訊'''
def getUseridOrder(userId):
    message = {
  "type": "flex",
  "altText": "this is a flex message",
  "contents": {
  "type": "bubble",
  "body": {
    "type": "box",
    "layout": "vertical",
    "spacing": "md",
    "contents": [
      {
        "type": "box",
        "layout": "horizontal",
        "spacing": "md",
        "contents": [
          {
            "type": "text",
            "text": "日期時間",
            "wrap": True
          },
          {
            "type": "separator"
          },
          {
            "type": "text",
            "text": "交易角色",
            "wrap": True
          },
          {
            "type": "separator"
          },
          {
            "type": "text",
            "text": "組隊角色",
            "wrap": True
          },
          {
            "type": "separator"
          },
          {
            "type": "text",
            "text": "地點(10S)",
            "wrap": True
          },
          {
            "type": "separator"
          }
          
        ]
      },
      {
        "type": "separator"
      },
    ]
  }
}
}
    print(YEARDATEDICT)
    yeardate_keys = list(YEARDATEDICT.keys())
    print(userId)
    print(yeardate_keys)
    # for yeardate in yeardate_keys:
    tzone = timezone(timedelta(hours=8))
    yeardate = datetime.now(tz=tzone)
    mydb = myclient["buff_online"]
    yeardate = yeardate.isoformat().split("T")[0].replace("-","")[2:]
    mycol = mydb[f"final_order_{str(yeardate)}"]

    # mydoc = mycol.find({'userId':userId},{'Date':1,'time':1})
    mydoc = mycol.find({'userId':userId}).sort('time',1)
    
    for data in mydoc:
        print(data)
        reverseddate = data['Date']
        reversedtime = data['time']
        tradeName = data['trade_name']
        partyName = data['party_name']
        message["contents"]["body"]["contents"].append({
            "type": "box",
            "layout": "horizontal",
            "spacing": "md",
            "contents": [
            {
                "type": "text",
                "text": f"{reverseddate}\n{reversedtime}",
                "wrap": True
            },
            {
                "type": "separator"
            },
            {
                "type": "text",
                "text": tradeName,
                "wrap": True
            },
            {
                "type": "separator"
            },
            {
                "type": "text",
                "text": partyName,
                "wrap": True
            },
            {
                "type": "separator"
            },
            {
                "type": "text",
                "text": "六條岔道",
                "wrap": True
            },
            {
                "type": "separator"
            }
            ]
        })
        message["contents"]["body"]["contents"].append({
            "type": "separator"
        })
    
    return message

'''刪除訂單提醒文字'''
def getDeleteOrderText():
    message ={
                "type": "text",
                "text": "預約資訊："
             }
    return message

'''確認刪除使用者訂單的意願'''
def getConfirmDeleteOrder():
    data = json.dumps({'action':'Delete order'})
    message = {
        "type": "template",
        "altText": "this is a confirm template",
        "template": {
            "type": "confirm",
            "text": "是否要刪除已有的預約？",
            "actions": [
                {
                "type": "postback",
                "label": "是",
                "data": data,   
                "displayText": "是",           
                },
                {
                    "type": "message",
                    "label": "否",
                    "text": "否"
                }
            ]
        }
    }
    
    return message

'''確認想要刪除的時間'''
def getComfirmTimetoDelete(deletedtime):
    data = json.dumps({'time':deletedtime, 'action':'Surely delete the time'})
    tzone = timezone(timedelta(hours=8))
    yeardate = datetime.now(tz=tzone)
    yeardate = yeardate.isoformat().split("T")[0]
    message = {
        "type": "template",
        "altText": "this is a confirm template",
        "template": {
            "type": "confirm",
            "text": f"是否要刪除{yeardate} {deletedtime}的預約",
            "actions": [
                {
                "type": "postback",
                "label": "是",
                "data": data,
                "displayText": "是"
                },
                {
                    "type": "message",
                    "label": "否",
                    "text": "否"
                }
            ]
        }
    }
    return message

'''真的刪除使用者訂單並回傳預約刪除成立'''
def getDeleteTimeSurelyText(surelydeletedtime, userId):
    tzone = timezone(timedelta(hours=8))
    yeardate = datetime.now(tz=tzone)
    yeardate = yeardate.isoformat().split("T")[0]
    dbyeardate = yeardate.replace("-","")
    dbyeardate = dbyeardate[2:]

    lock = threading.Lock()
    with lock:
        try: 
            mydb = myclient["buff_online"]
            mycol = mydb[f"final_order_{dbyeardate}"] 
            mycol.delete_one({'time':str(surelydeletedtime)})
            print(f"指定時間{surelydeletedtime}已從最終訂單移除")
            tzone = timezone(timedelta(hours=8))
            nowtime = datetime.now(tz=tzone).isoformat()[:16]
            mydb = myclient["buff_online"]
            mycol = mydb["userid_points"]
            mydoc = mycol.find_one({"_id":userId},{"_id":0, "nickname": 1})
            nicknameofthisuser = mydoc["nickname"]
            final_order_dbname = nowtime.split("T")[0].replace("-","")[2:]
            data = [
                    #['write_yeardate_time',  'userid'  ,     'nickname'     , 'action' ,           'yeardate'            ,       'time'     , 'tradename' , 'partyname' ,  'location'  ,  'remark']
                    [      nowtime         ,   userId   , nicknameofthisuser , "Delete" ,USERID_YEARDATE_TIME[userId][0] , surelydeletedtime ,     None    ,    None     ,  "六條岔道"   ,f'{nicknameofthisuser}，刪除{surelydeletedtime}的訂單']
                ]
            file_path = f'./Data/final_order_{final_order_dbname}.csv'
            file_exists = os.path.isfile(file_path)
            with open(file_path, 'a', newline='',encoding='utf-8') as csvfile:
                csv_writer = csv.writer(csvfile)
                if not file_exists:
                    csv_writer.writerow(['write_yeardate_time',    'userid'    ,     'nickname'     , 'action' ,    'yeardate'   ,     'time'     ,  'tradename'   ,  'partyname'   ,  'location'  ,  'remark'])
                csv_writer.writerows(data)
                print(f'已成功寫入 {file_path}')

        except:
            print(f"指定時間{surelydeletedtime}已從最終訂單移除失敗")

    
    yeardate = USERID_YEARDATE_TIME[userId][0]
    yeardatetimelist = YEARDATEDICT[yeardate]
    print("yeardatetimelist:",yeardatetimelist)
    yeardatetimelist.pop(yeardatetimelist.index(surelydeletedtime))
    print("yeardatetimelist.pop():",yeardatetimelist)
    print('yeardate:',yeardate)
    print('id:',yeardate[-2:])
    lock = threading.Lock()
    with lock:
        try: 
            mydb = myclient["buff_online"]
            mycol = mydb["yeardate_time"]
            id = yeardate[5:7]
            mycol.update_one({'_id':id},{'$set':{yeardate:yeardatetimelist}},True)
            print(f"把上述指定時間{surelydeletedtime}，從該日期的時間清單移除")
        except:
            print(f"把上述指定時間{surelydeletedtime}，從該日期的時間清單移除失敗")
    message = {
                "type":"text",
                "text": f"您先前在{yeardate} {surelydeletedtime}的預約，已被刪除"
    }
    return message

'''超過服務時間'''
def getOverServicetime():
    message ={
        
                "type": "text",
                "text": "已超過21:54，服務時間已結束，請於每日21:54之前進行預約"
             }

    return message

'''當日已額滿'''
def getHavenoTime():
    message ={
        
                "type": "text",
                "text": "今日預約已額滿，造成不便敬請見諒"
             }

    return message

'''選擇要刪除的時間'''
def getChooseDeleteTime(userId):
    message = {
            "type": "template",
            "altText": "This is a buttons template",
            "template": {
            "type": "buttons",
            "text": "請選擇要刪除的時間",
            "actions": [
            
                       ]
                       }
              }
    
    
    tzone = timezone(timedelta(hours=8))
    yeardate = datetime.now(tz=tzone)
    nowtime = yeardate + timedelta(minutes=30)
    yeardate = yeardate.isoformat().split("T")[0].replace("-","")[2:]
    print("日期",yeardate)
    mydb = myclient["buff_online"]
    
    mycol = mydb[f"final_order_{yeardate}"]

    # mydoc = mycol.find({'userId':userId},{'Date':1,'time':1})
    mydoc = mycol.find({'userId':userId}).sort('time',1)
    nowtime = nowtime.isoformat().split("T")[1][:5]
    
    for data in mydoc:
        print("data")
        print(data)
        reversedtime = data['time']
        if nowtime >= reversedtime:
            message["template"]["actions"].append(
                                            {
                                                "type": "message",
                                                "label": reversedtime,
                                                "text": f"您預定的{reversedtime}已在半個小時內，故不可刪除"
                                            }
                                            )
        else:
            message["template"]["actions"].append(
                                                {
                                                    "type": "postback",
                                                    "label": reversedtime,
                                                    "data": json.dumps({"time":reversedtime,"action":'Time want to delete'})
                                                }
                                                )
    return message

'''計算User已預約幾個時間'''
def CountOrdersofUserid(userId):
    count = 0
    tzone = timezone(timedelta(hours=8))
    yeardate = datetime.now(tz=tzone)
    yeardate = yeardate.isoformat().split("T")[0]
    yeardate = yeardate.replace("-","")[2:]
    mydb = myclient["buff_online"]
    mycol = mydb[f"final_order_{yeardate}"]
    mydoc = mycol.find({"userId":userId})
    print(mydoc)
    for data in mydoc:
        print(data)
        count += 1

    return count

'''已達一天預約上線的提示訊息'''
def getReservedtimeIsTwo():
    message ={ 
            "type":"text",
            "text":"您已預約兩個時間，若需修改時間請先刪除一個再預約新的時間，謝謝"
    }

    return message

'''我本人拿全部訂單'''
def getGetAllorders():
    message = {
  "type": "flex",
  "altText": "this is a flex message",
  "contents": {
  "type": "bubble",
  "body": {
    "type": "box",
    "layout": "vertical",
    "spacing": "md",
    "contents": [
      {
        "type": "box",
        "layout": "horizontal",
        "spacing": "md",
        "contents": [
          {
            "type": "text",
            "text": "日期時間",
            "wrap": True
          },
          {
            "type": "separator"
          },
          {
            "type": "text",
            "text": "交易角色",
            "wrap": True
          },
          {
            "type": "separator"
          },
          {
            "type": "text",
            "text": "組隊角色",
            "wrap": True
          },
          {
            "type": "separator"
          },
          {
            "type": "text",
            "text": "地點(10S)",
            "wrap": True
          },
          {
            "type": "separator"
          }
          
        ]
      },
      {
        "type": "separator"
      },
    ]
  }
}
}
    tzone = timezone(timedelta(hours=8))
    yeardate = datetime.now(tz=tzone)
    yeardate = yeardate.isoformat().split("T")[0].replace("-","")[2:]
    print("日期",yeardate)
    mydb = myclient["buff_online"]
    
    mycol = mydb[f"final_order_{str(yeardate)}"]

    # mydoc = mycol.find({'userId':userId},{'Date':1,'time':1})
    mydoc = mycol.find({}).sort('time',1)
    print("123")
    for data in mydoc:
        print(data)
        reverseddate = data['Date']
        reversedtime = data['time']
        tradeName = data['trade_name']
        partyName = data['party_name']
        message["contents"]["body"]["contents"].append({
            "type": "box",
            "layout": "horizontal",
            "spacing": "md",
            "contents": [
            {
                "type": "text",
                "text": f"{reverseddate}\n{reversedtime}",
                "wrap": True
            },
            {
                "type": "separator"
            },
            {
                "type": "text",
                "text": tradeName,
                "wrap": True
            },
            {
                "type": "separator"
            },
            {
                "type": "text",
                "text": partyName,
                "wrap": True
            },
            {
                "type": "separator"
            },
            {
                "type": "text",
                "text": "六條岔道",
                "wrap": True
            },
            {
                "type": "separator"
            }
            ]
        })
        message["contents"]["body"]["contents"].append({
            "type": "separator"
        })
    
    return message

'''查看點數'''
def getMyPoints(userId):
    mydb = myclient["buff_online"]
    mycol = mydb["userid_points"]
    mydoc = mycol.find_one({"_id":userId})


    point = mydoc["points"]

    message = {
                "type":"text",
                "text":f"目前點數：{point}"
    }
    return message

'''每到22:30更新點數'''
def getUpdatePoints():
    tzone = timezone(timedelta(hours=8))
    yeardate = datetime.now(tz=tzone)
    yeardate = yeardate.isoformat().split("T")[0]
    yeardate = yeardate.replace("-","")[2:]
    mydb = myclient["buff_online"]
    mycol = mydb[f"final_order_{yeardate}"]
    mydoc = mycol.find({},{"_id":0,'userId': 1,'point': 1})
    updatepoint_userid = set()
    list1 = list(mydoc)
    print(list1)
    for data in list1:
        print(updatepoint_userid)
        updatepoint_userid.add(data["userId"])
        print(type(updatepoint_userid))
    for userid in updatepoint_userid:

        lock =threading.Lock()
        with lock:
            try:
                mycol = mydb[f"final_order_{yeardate}"]
                mydoc = mycol.count_documents({"userId":userid})
                mycol =mydb["userid_points"]
                mycol.update_one({"_id":userid},{"$inc":{"points":mydoc}})
                print("更新點數成功。")
            except:
                print("更新點數失敗。")
    message = {
                "type":"text",
                "text":"更新點數成功"
    }
    return message

'''刪除指定時間訂單，22:00後執行，因為可能有人棄單不能讓他更新點數'''
def getDeleteSomeOrderList(Timelist):
    tzone = timezone(timedelta(hours=8))
    yeardate = datetime.now(tz=tzone).isoformat()
    dbyeardate = yeardate.split("T")[0]
    dbyeardate = dbyeardate.replace("-","")[2:]
    lock = threading.Lock()
    with lock:
        try:
            mydb = myclient["buff_online"]
            mycol = mydb[f"final_order_{dbyeardate}"]
            for time in Timelist:
                mycol.delete_one({"time":time})
                print(f"從final_order_{dbyeardate}移除time:{time}訂單成功")
        except:
            print(f"從final_order_{dbyeardate}移除time:{time}訂單成功")
     

'''確認是否要兌換免費Buff'''
def getConfirmFreeBuff():
    data = json.dumps({'action':'Exchange confirmed'})
    message = {
                "type": "template",
                "altText": "this is a confirm template",
                "template": {
                    "type": "confirm",
                    "text": f"是否要兌換免費一次的Buff機？",
                    "actions": [
                    {
                        "type": "postback",
                        "label": "是",
                        "data": data,
                        "displayText": "是",
                    },
                    {
                        "type": "message",
                        "label": "否",
                        "text": "否"
                    }
                    ]

                }
            }
    return message

'''提醒點數不夠文字'''
def getDenyExchangeText(point):
    message = {
        "type":"text",
        "text":f"目前點數：{point}\n累積5點才能兌換唷！"

    }

    return message


'''回傳兌換成功'''
def getExchangeSuccesslyText(point):
    message = [
                {
                    "type":"text",
                    "text":"兌換免費Buff一次成功，已扣除5點"
                },
                {
                    "type":"text",
                    "text":f"剩餘點數：{point}"
                }
    ]

    return message[0],message[1]

def getTodayClosedText():
    message = {
                "type":"text",
                "text":"今日休息，請多多見諒"
    }
    return message


def getClosedText():
    lock = threading.Lock()
    with lock:
        try:
            mydb = myclient["buff_online"]
            mycol = mydb[f"state"]
            mydoc = mycol.update_one({"_id":0},{"$set":{"state":0}}) 
            message = {
                "type":"text",
                "text":"切換狀態為休息"
                 }
        except:
            print("切換失敗")
            message = {
                        "type":"text",
                        "text":"切換狀態為休息，失敗"
            }
    return message


def getOpenText():
    lock = threading.Lock()
    with lock:
        try:
            mydb = myclient["buff_online"]
            mycol = mydb[f"state"]
            mydoc = mycol.update_one({"_id":0},{"$set":{"state":1}}) 
            message = {
                "type":"text",
                "text":"切換狀態為營業中"
                 }
        except:
            print("切換失敗")
            message = {
                        "type":"text",
                        "text":"切換狀態為營業中，失敗"
            }
    return message

'''取得當前狀態，休息or營業'''
def getNowState():
    mydb = myclient["buff_online"]
    mycol = mydb[f"state"]
    mydoc = mycol.find_one({"_id":0},{"_id":0}) 
    state = mydoc["state"]
    return state

'''測試函式，現在放的是輸入客戶暱稱'''
def test(userId):
    message = {
    "type": "flex",
    "altText": "this is a flex message",
    "contents": {
            "type": "bubble",
            "header": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "text",
                            "text": "請點選下方按鈕提供您的暱稱，方便我記錄您的點數，並贈送您一點",
                            "wrap": True
                        }
                        ]
                    },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                        "type": "postback",
                        "label": "點我",
                        "data": json.dumps({"action":"My nickname example"}),
                        "inputOption": "openKeyboard",
                        "fillInText":"我的暱稱："
                    }
                },
                
                ]
            }
            }
    }
    return message

'''查詢user點數'''
def getuserIdPoints(userId):

    mydb = myclient["buff_online"]
    mycol = mydb["userid_points"]
    mydoc = mycol.find_one({"_id":userId})
    point = mydoc["points"]

    return point
    

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
