# Copyright © https://steam.oxxostudio.tw

from linebot import LineBotApi, WebhookHandler
# 載入對應的函式庫
from linebot.models import FlexSendMessage, BubbleContainer, ImageComponent
from datetime import datetime, timedelta, timezone
import threading
import csv
import os
import pymongo
import requests
import json
import configparser

config = configparser.ConfigParser()
config.read('/home/linebot008/Buffonline/config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
# 剛剛 Flex Message 的 JSON 檔案就貼在下方
username = config.get('mongodb', 'username')
password = config.get('mongodb', 'password')
hostlocation = config.get('mongodb', 'hostlocation')

userId = "Uf8e734e58b67c12e0de1cd574a1718da"

cluster_url =f"mongodb+srv://{username}:{password}@{hostlocation}/?retryWrites=true&w=majority&appName=GueiMing"
myclient = pymongo.MongoClient(cluster_url, username=username,password=password)

tzone = timezone(timedelta(hours=8))
yeardate = datetime.now(tz=tzone)
yeardatetime = yeardate.isoformat()[0:16]
yeardate = yeardate.isoformat().split("T")[0].replace("-","")[2:]
print("日期",yeardate)
mydb = myclient["buff_online"]

mycol = mydb[f"final_order_{str(yeardate)}"]

message = {
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
# mydoc = mycol.find({'userId':userId},{'Date':1,'time':1})
mydoc = mycol.find({}).sort('time',1)
# print("123")
for data in mydoc:
    # print(data)
    reverseddate = data['Date']
    reversedtime = data['time']
    tradeName = data['trade_name']
    partyName = data['party_name']
    message["body"]["contents"].append({
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
    }
    )
    message["body"]["contents"].append({
            "type": "separator"
        })

line_bot_api.push_message(config.get('line-bot', 'my_user_id'), FlexSendMessage(
    alt_text='hello',
    contents=message
))

print(f"{yeardatetime}推送訂單")
