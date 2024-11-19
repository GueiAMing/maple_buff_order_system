#ver1.2 取消時間限制，修改程式碼時間經常超過下單時間(22:00)，所以需要解除限制

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

from mongofunction import writeintotemporder_thesame, writeintotemporder_nonthesame, getPoints_write_into_useridpoints,getuseridlist, CountOrdersofUserid, getGetAllorders, getDeleteSomeOrderList, getMyPoints, getUpdatePoints, getuserIdPoints, writeintotemporder_secondtime, getConfirmFinalOrder, getalmosttakeorder, getChooseDeleteTime, getDeleteTimeSurelyText, getRealFinalOrder, getNowState
from functions import getyeardatedict, getusertraderpartner, getuseridyeardatetime,  getnowdateandnowtime, getUseridOrder, getConfirmNickname, getUseridNickname, getConfirmReserve, getConfirmDeleteOrder, getFreeTime, getConfirmFreeBuff, getChooseTimeAgain, getConfirmChooseTime, getComfirmTimetoDelete, getChooseTime, getConfirmRoleName
from text_functions import getOpenText, getTodayClosedText, getRewardCardSuccesslyText, getHavenoTimeText, getOverServicetimeText, getReservedtimeIsTwo_Text, getDeleteOrderText, getClosedText, getDenyExchangeText, getExchangeSuccesslyText, getWrongTimeFormat, getReservedTime, getAfterOtherUsersText, getRoleNames, getRoleNamesExample1, getRoleNamesExample2, getNicknameExample, getWrongIdFormat, getUserPickedTimeText

app = Flask(__name__, static_url_path='/static')
CHECKLIST = ['20:00', '20:05', '20:10', '20:15', '20:20', '20:25', '20:30', '20:35', '20:40', '20:45', '20:50', '20:55', '21:00', '21:05', '21:10', '21:15', '21:20', '21:25', '21:30', '21:35', '21:40', '21:45', '21:50', '21:55', '22:00']
# CHECKLIST = [22]
CHECKLIST = ['20:00', '20:05', '20:10', '20:15', '20:20', '20:25', '20:30', '20:35', '20:40', '20:45', '20:50', '20:55', '21:00', '23:05', '23:10', '23:15', '23:20', '23:25', '23:30', '23:35', '23:40', '23:45', '23:50', '23:55', '22:00']

USERID_TRADER_PARTNER = getusertraderpartner()
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

                    if userId not in getuseridlist() :
                        if "我的暱稱：" in text:
                            nickname = text[5:]
                            payload["messages"] = [getConfirmNickname(nickname)]
                        else:
                            print("Insert Nickname")
                            payload["messages"] = [getUseridNickname()]
                    else:
                        nowdate_1,nowtime_1 = getnowdateandnowtime()
                        if text == "我要預約" :
                            if CountOrdersofUserid(userId) < 2:
                                yeardate = getyeardatedict()
                                if len(yeardate[nowdate_1]) == len(CHECKLIST):
                                    payload["messages"] = [getHavenoTimeText()]
                                elif nowtime_1 > "23:59":
                                    print(nowtime_1,"超過22:00了")
                                    payload["messages"] = [getOverServicetimeText()]
                                else:
                                    payload["messages"] = [getConfirmReserve()]
                            else:
                                payload["messages"] = [getReservedtimeIsTwo_Text()]
                        elif len(text.split(" ")) == 2 or "一樣" in text:
                            if CountOrdersofUserid(userId) < 2:
                                if len(text)==2 and "一樣" in text :
                                    tradeName, partyName = writeintotemporder_thesame(userId)
                                    payload["messages"] = [getConfirmRoleName(tradeName, partyName)]
                                elif len(text.split(" ")[0].encode("utf-8")) <= 18 and len(text.split(" ")[1].encode("utf-8")) <= 18 :
                                    tradeName, partyName = writeintotemporder_nonthesame( text, userId)
                                    payload["messages"] = [getConfirmRoleName(tradeName, partyName)]
                                else:
                                    payload["messages"] = [getWrongIdFormat()]
                            else:
                                payload["messages"] = [getReservedtimeIsTwo_Text()]        
                        if text == "查詢預約資訊":
                            payload["messages"] = [getUseridOrder(userId)]
                        if text =="測試":
                            payload["messages"] = [test()]
                        if text =="刪除預約":
                            _, nowtime_delete = getnowdateandnowtime()
                            if nowtime_delete > "23:59":
                                print(nowtime_delete,"超過22:00了")
                                payload["messages"] = [getOverServicetimeText()]
                            else:
                                payload["messages"] = [
                                                        getDeleteOrderText(),
                                                        getUseridOrder(userId),
                                                        getConfirmDeleteOrder()
                                                    ]
                        if text == "今日時間":
                            todayDate, _ = getnowdateandnowtime()
                            payload["messages"] = [getFreeTime(todayDate, CHECKLIST)]
                        if text == "全部訂單" and userId in userids:
                            payload["messages"] = [getGetAllorders()]
                        if  "指定時間：" in text and userId in userids:
                            Timelist = text[5:].split(" ")
                            payload["messages"] = [getDeleteSomeOrderList(Timelist)]
                        if text == "我的點數" :
                            if  userId in getuseridlist():
                                print(userId,"in USERIDSLIST")
                                payload["messages"] = [getMyPoints(userId)]
                        if text == "更新點數" and userId in userids:
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
                    if CountOrdersofUserid(userId) < 2:
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
                            payload["messages"] = [
                                                    getUserPickedTimeText( str(reservedDate), reservedTime),
                                                    getConfirmChooseTime( str(reservedDate), reservedTime)
                                                    ]
                            yeardate = getyeardatedict()
                            if str(reservedTime) in yeardate[reservedDate]:
                                print(yeardate[reservedDate],"reservetime list")
                                data = json.dumps({'action':'Time chosen'})
                                payload["messages"] = [ 
                                                    getReservedTime(),
                                                    getFreeTime(reservedDate, CHECKLIST),
                                                    getChooseTimeAgain()
                                                    ]
                    else:
                        payload["messages"] = [getReservedtimeIsTwo_Text()]  
                    replyMessage(payload)
                else:
                    data = json.loads(events[0]["postback"]["data"])
                    action = data["action"]
                    
                    if action == "Time_confirmed":
                        writeintotemporder_secondtime(userId, data)
                        payload["messages"] = [getConfirmFinalOrder(userId)]
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
                        thisuser_yeardate_time = getuseridyeardatetime(userId)
                        yeardate = getyeardatedict()
                        if thisuser_yeardate_time[1] not in yeardate[thisuser_yeardate_time[0]]:
                            yeardate[thisuser_yeardate_time[0]].append(thisuser_yeardate_time[1])
                            ordered_time_list = yeardate[thisuser_yeardate_time[0]]
                            print("時間未被選過",yeardate)
                            payload["messages"] = [getRealFinalOrder(userId, ordered_time_list, checklist=CHECKLIST),
                                                   getUseridOrder(userId)]
                        else:
                            print(f"差一點，就在剛剛{thisuser_yeardate_time[1]}被預約走了，請選擇其他時間")
                            getalmosttakeorder(userId, thisuser_yeardate_time)
                            data = json.dumps({'action':'Time chosen'})
                            payload["messages"] = [
                                                    getAfterOtherUsersText(thisuser_yeardate_time[1]),
                                                    getChooseTimeAgain()
                                                    ]
                    if action == 'Delete order':
                        payload["messages"] = [getChooseDeleteTime(userId)]
                    if action == 'Time want to delete':
                        deletedtime = data["time"]
                        payload["messages"] = [getComfirmTimetoDelete(deletedtime)]
                    if action == 'Surely delete the time':
                        surelydeletedtime = data["time"]
                        payload["messages"] = [getDeleteTimeSurelyText(surelydeletedtime, userId),
                                               getUseridOrder(userId)]
                    if action == 'My nickname example':
                        example1, example2 = getNicknameExample()
                        payload["messages"] = [ example1, example2]
                    if action == 'confirm nickname':
                        nickname = data["nickname"]
                        getPoints_write_into_useridpoints( userId, nickname)
                        payload["messages"] = [getRewardCardSuccesslyText()]
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

















'''測試函式，現在放的是輸入客戶暱稱'''
def test():
    message = {
  "type": "flex",
  "altText": "this is a flex message",
  "contents":{
  "type": "bubble",
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "text",
        "text": "明明",
        "weight": "bold",
        "size": "50px"
      },
      {
        "type": "box",
        "layout": "baseline",
        "margin": "md",
        "contents": [
          {
            "type": "icon",
            "url": "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png",
            "size": "40px"
          },
          {
            "type": "icon",
            "url": "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png",
            "size": "40px"
          },
          {
            "type": "icon",
            "url": "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png",
            "size": "40px"
          },
          {
            "type": "icon",
            "url": "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png",
            "size": "40px"
          },
          {
            "type": "icon",
            "url": "https://developers-resource.landpress.line.me/fx/img/review_gray_star_28.png",
            "size": "40px" 
          }
        ]
      },
      {
        "type" : "separator",
        "color": "#000000"
      },
      {
        "type": "box",
        "layout": "baseline",
        "margin": "md",
        "contents": [
            {
            "type": "text",
            "text": "4點",
            "size": "40px",
            "color": "#000000",
            "margin": "md",
            "align":"end"
          }

        ]
      },
      {
          "type" : "image",
          "url" :"https://drive.google.com/file/d/13hljzIBT1Xm6xoe6jfN2N8w1YTSrVco7/view?usp=sharing",
          "aspectRatio": "1:1"
      }


    ]
  }
}

  }

    
    
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
