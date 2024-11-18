from mongofunction import dbmethod
from datetime import datetime, timedelta, timezone
import time
import os
import csv
import json
import threading

'''取得日期被預約時間'''
def getyeardatedict():
    '''取得日期被預約時間'''
    lock =threading.Lock()
    with lock:
        mycol = dbmethod( "buff_online", "yeardate_time")
        tzone = timezone(timedelta(hours=8))
        now = datetime.now(tz=tzone)
        id = now.isoformat()[5:7]
        mydoc = mycol.find_one({"_id":str(id)},{'_id': 0})
        

    return mydoc

'''取得使用者歷史預約角色名稱'''
def getusertraderpartner():
    '''取得使用者歷史預約角色名稱'''
    mycol = dbmethod( "buff_online", "userid_trader_partner")
    mydoc = mycol.find_one({"_id" : "userid"},{"_id":0})
    if mydoc is None:
        mydoc = dict()
        return mydoc
    else:  
        return mydoc
    
'''取得使用者預約日期時間'''   
def getuseridyeardatetime(userId):
    '''取得使用者預約日期時間'''
    mycol = dbmethod( "buff_online", "userid_yeardate_time")
    mydoc = mycol.find({},{"_id": 0,"userid":0})
    # mydoc = mycol.find({})
    
    result = dict()
    for data in mydoc:
        eachuserid = list(data.keys())[0]      
        result[eachuserid] = data[eachuserid]
    return result[userId]

'''取得當前日期時間'''
def getnowdateandnowtime():
    '''取得當前日期時間'''
    tzone = timezone(timedelta(hours=8))
    nowdatetime = datetime.now(tz=tzone)
    nowdate = nowdatetime.isoformat().split("T")[0]
    nowtime = nowdatetime.isoformat().split("T")[1]
    return nowdate, nowtime

'''查詢使用者個人預約資訊'''
def getUseridOrder(userId):
    '''查詢使用者個人預約資訊'''
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
            "text": "地點(8S)",
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
    
    print(userId)
    # for yeardate in yeardate_keys:
    tzone = timezone(timedelta(hours=8))
    yeardate = datetime.now(tz=tzone)
    yeardate = yeardate.isoformat().split("T")[0].replace("-","")[2:]
    mycol = dbmethod("buff_online",f"final_order_{str(yeardate)}")

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

'''確認客戶暱稱'''
def getConfirmNickname(nickname):
    '''確認客戶暱稱'''
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

'''請客戶點選按鈕輸入暱稱'''
def getUseridNickname():
    '''請客戶點選按鈕輸入暱稱'''
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

'''確認預定意願'''
def getConfirmReserve():
    '''確認預定意願'''
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

'''確認刪除使用者訂單的意願'''
def getConfirmDeleteOrder():
    '''確認刪除使用者訂單的意願'''
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
                    "text": "不要刪除"
                }
            ]
        }
    }
    
    return message

'''顯示空閒時間'''
def getFreeTime(reservedDate, checklist):
    '''顯示空閒時間'''
    tzone = timezone(timedelta(hours=8))
    nowtime = datetime.now(tz=tzone) + timedelta(minutes=6)
    nowtime = nowtime.isoformat().split("T")[1][:5]
    yeardate = getyeardatedict()
    chosen_times = yeardate[reservedDate] 
    not_chosen_times = [time for time in checklist if time not in chosen_times and time > nowtime]
    print(reservedDate,"未被預訂時間",not_chosen_times)
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

'''確認是否要兌換免費Buff'''
def getConfirmFreeBuff():
    '''確認是否要兌換免費Buff'''
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

'''時間被預訂走了，重新選擇時間'''
def getChooseTimeAgain():
    '''時間被預訂走了，重新選擇時間'''
    data = json.dumps({'action':'Time chosen'})
    tzone = timezone(timedelta(hours=8))
    initial_datetime = datetime.now(tz=tzone) + timedelta(minutes=30)
    max_datetime = initial_datetime.isoformat().split("T")[0] + "t23:59"
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
                        # "initial": "2017-12-25T00:00",
                        # "max": "2018-01-24T23:59",
                        # "min": "2017-12-25T00:00"
                    }
                    ]
                }
             }
    return message

'''確認名字後第一次選擇的時間'''
def getConfirmChooseTime(reservedDate, reservedTime, userId):
    '''確認名字後第一次選擇的時間'''
    from mongofunction import getChangeUserstate

    getChangeUserstate(userId=userId, state=4)
    data = json.dumps({'Date':reservedDate,'Time':reservedTime,'action':"Time_confirmed"})
    message = {
        "type": "template",
        "altText": "this is a confirm template",
        "template": {
            "type": "confirm",
            "text": f"是否要預約{reservedDate} {reservedTime}的Buff機？",
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
    '''確認想要刪除的時間'''
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

'''確認意願後第一次選擇時間'''
def getChooseTime(data):
    '''確認意願後第一次選擇時間'''
    data = json.dumps({'action':'Time chosen'})
    tzone = timezone(timedelta(hours=8))
    initial_datetime = datetime.now(tz=tzone) + timedelta(minutes=10)
    max_datetime = initial_datetime.isoformat().split("T")[0] + "t23:59"
    # initial_datetime = datetime.now(tz=tzone)
    # max_datetime = initial_datetime.isoformat().split("T")[0] + "t23:59"
    format_initial_datetime = initial_datetime.isoformat()[:16]
    message = {
                "type": "template",
                "altText": "This is a buttons template",
                "template": {
                    "type": "buttons",
                    "text": "選擇晚上10點，5的倍數分鐘",
                    "actions": [
                    {
                        "type": "datetimepicker",
                        "label": "\"點我\"來選擇時間",
                        "data": data,
                        "mode": "datetime",
                        "initial": str(format_initial_datetime),
                        "max": str(max_datetime),
                        "min": str(format_initial_datetime),
                        # "initial": "2017-12-25T00:00",
                        # "max": "2018-01-24T23:59",
                        # "min": "2017-12-25T00:00",
                        "text":"test"
                        
                    }
                    ]
                }
             }
    return message

'''確認交易角色ID，組隊角色ID'''
def getConfirmRoleName(tradeName, partyName):
    '''確認交易角色ID，組隊角色ID'''
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



def gethistoryfinalOrder(date):
    file_path = f'./Data/final_order_{date}.csv'
    try:
        with open(file_path, 'r', newline='',encoding='utf-8') as csvfile:
            csvreader = csv.reader(csvfile)
            result = []
            for row in csvreader:
                result.append(row)
            print(result)
    except FileNotFoundError:
        print(f"File {file_path} not found")
        result = [f"{date}查無資料"]
        print(result)
    return result


