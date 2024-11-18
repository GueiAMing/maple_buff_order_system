import pymongo
import json
import configparser
from datetime import datetime, timedelta, timezone
import threading
import os
import csv



config = configparser.ConfigParser()
config.read('config.ini')

username = config.get('mongodb', 'username')
password = config.get('mongodb', 'password')
hostlocation = config.get('mongodb', 'hostlocation')
# myclient = pymongo.MongoClient("mongodb://localhost:27017/")
cluster_url =f"mongodb+srv://{username}:{password}@{hostlocation}/?retryWrites=true&w=majority&appName=GueiMing"
myclient = pymongo.MongoClient(cluster_url, username=username,password=password)

'''訪問mongodb資料庫的函式'''
def dbmethod(database : str , collcetion : str):
    '''訪問mongodb資料庫的函式'''
    mydb = myclient[database]
    mycol =mydb[collcetion]
    
    return mycol

'''當輸入"一樣"寫入暫時資料庫的函式'''
def writeintotemporder_thesame(userId):
    '''當輸入"一樣"寫入暫時資料庫的函式'''
    from functions import getusertraderpartner #避免 circular import，所以寫在函式裡面
    lock = threading.Lock()
    with lock:
        mycol = dbmethod( "buff_online", "userid_trader_partner")
        mydoc = mycol.find_one({"_id":"userid"})
        USERID_TRADER_PARTNER = getusertraderpartner()
        USERID_TRADER_PARTNER[userId] = mydoc[userId]
        tradeName = USERID_TRADER_PARTNER[userId][0]
        partyName = USERID_TRADER_PARTNER[userId][1]
        print( "一樣:",tradeName,partyName)
        tzone = timezone(timedelta(hours=8))
        nowtime_thesame = datetime.now(tz=tzone).isoformat()[:16] 
        try:
            mycol = dbmethod( "buff_online", "userid_points")
            mydoc = mycol.find_one({"_id":userId},{"_id":0, "nickname": 1})
            nicknameofthisuser = mydoc["nickname"]
            mycol = dbmethod( "buff_online", "userid_trader_partner")
            mycol.update_one({"_id":"userid"},{"$set":{userId:USERID_TRADER_PARTNER[userId]}},True)
            mycol.update_one({"_id": userId },{"$set":{
                                                        'TRADER_PARTNER':USERID_TRADER_PARTNER[userId],
                                                        'nickname': nicknameofthisuser,
                                                        'writetime':nowtime_thesame,}},True)
            mycol = dbmethod( "buff_online", "temp_order")
            mycol.update_one({"userId":userId},{"$set":{
                                                        'userId':userId,
                                                        'writetime':nowtime_thesame,
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
            nowtime_thesame2 = datetime.now(tz=tzone).isoformat()[:16]
            data = [
                    #['write_yeardate_time','userid',       'nickname'         , 'date' ,  'time' , 'trade_name', 'party_name','remark']
                    [    nowtime_thesame2  , userId ,    nicknameofthisuser    ,  None  ,   None  ,   tradeName ,  partyName  ,f'{nicknameofthisuser}，確認角色IDs']
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
    return tradeName, partyName

'''當輸入兩個ID寫入暫時資料庫的函式'''
def writeintotemporder_nonthesame( text, userId):
    '''當輸入兩個ID寫入暫時資料庫的函式'''
    lock = threading.Lock()
    with lock:
        tradeName = text.split(" ")[0]
        partyName = text.split(" ")[1]
        
        tzone = timezone(timedelta(hours=8))
        nowtime_nonthesame = datetime.now(tz=tzone).isoformat()[:16] 
        try:
            mycol = dbmethod( "buff_online", "userid_points")
            mydoc = mycol.find_one({"_id":userId},{"_id":0, "nickname": 1})
            nicknameofthisuser = mydoc["nickname"]
            mycol = dbmethod( "buff_online", "userid_trader_partner")
            mycol.update_one({"_id":"userid"},{"$set":{userId:[ tradeName, partyName]}},True)
            mycol.update_one({"_id": userId },{"$set":{
                                                        'TRADER_PARTNER':[ tradeName, partyName],
                                                        'nickname': nicknameofthisuser,
                                                        'writetime':nowtime_nonthesame,}},True)
            mycol = dbmethod( "buff_online", "temp_order")
            mycol.update_one({"userId":userId},{"$set":{
                                                        'userId':userId,
                                                        "writetime":nowtime_nonthesame,
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
            mycol = dbmethod( "buff_online", "userid_points")
            mydoc = mycol.find_one({"_id":userId},{"_id":0, "nickname": 1})
            nicknameofthisuser = mydoc["nickname"]
            data = [
                    #['write_yeardate_time','userid',       'nickname'         , 'date' ,  'time' , 'trade_name', 'party_name','remark']
                    [  nowtime_nonthesame , userId ,    nicknameofthisuser    ,  None  ,   None  ,   tradeName ,  partyName  ,f'{nicknameofthisuser}，確認角色IDs']
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
    return tradeName, partyName

'''當使用者選擇時間時，第二次寫入暫時資料函式'''
def writeintotemporder_secondtime(userId, data):
    '''當使用者選擇時間時，第二次寫入暫時資料函式'''

    from functions import getuseridyeardatetime #避免 circular import，所以寫在函式裡面

    lock = threading.Lock()
    reservedDate = data["Date"]
    reservedTime = data["Time"]
    yearDate = reservedDate
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
    
'''確認最後訂單'''
def getConfirmFinalOrder(userId):
    '''確認最後訂單'''
    from functions import getuseridyeardatetime, getusertraderpartner #避免 circular import，所以寫在函式裡面
    userid_yeardate_time = getuseridyeardatetime(userId)
    USERID_TRADER_PARTNER = getusertraderpartner()
    tradeName = USERID_TRADER_PARTNER[userId][0]
    partyName = USERID_TRADER_PARTNER[userId][1]
    data = json.dumps({'action':'FinalOrder confirmed'})
    message = {
                "type": "template",
                "altText": "this is a confirm template",
                "template": {
                    "type": "confirm",
                    "text": f"訂單確認：\n交易時間:{userid_yeardate_time[0]} {userid_yeardate_time[1]}\n交易角色:{tradeName}\n組隊角色:{partyName}",
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

'''獲取使用者清單'''
def getuseridlist():
    '''獲取使用者清單'''
    mycol = dbmethod( "buff_online", "userid_points")
    mydoc = mycol.find_one({"_id": "1"})
    useridlist=set(mydoc["userids"])
    return useridlist

'''更新使用者總人數'''
def getUpdateUids():
    '''更新使用者總人數'''
    lock = threading.Lock()
    with lock:
        try:
            mycol = dbmethod("buff_online","userid_points")
            mydoc = mycol.find_one({"_id":"0"})
            now_members = mydoc["numbers of uid"]
            now_uid = now_members + 1
            mycol.update_one({"_id":"0"},{"$set":{"numbers of uid":now_uid}}) 
            str_now_uid = str(now_uid).zfill(8)
        except:
            pass
    return str_now_uid

'''發點數卡'''
def getPoints_write_into_useridpoints(userId, nickname):
    '''發點數卡'''
    lock = threading.Lock()
    with lock:
        temp_useridslist = getuseridlist()
        temp_useridslist.add(userId)
        tzone = timezone(timedelta(hours=8))
        nowyeardatetime = datetime.now(tz=tzone)
        nowyeardatetime = nowyeardatetime.isoformat()[:16].replace("T","-")
        this_user_uid = getUpdateUids()
        try:
            mydb = myclient["buff_online"]
            mycol = mydb["userid_points"]
            mycol.update_one({"_id": "1"},{"$set":{"userids":list(temp_useridslist)}})
            mycol.insert_one({"_id":userId,"nickname":nickname,"got_reward_card_time":nowyeardatetime,"points":1,"uid":this_user_uid, "role":"user","password":"12345678", "change_password":False})
            print(f"{userId}獲得點數卡")
        except:
            print(f"{userId}獲得點數卡，失敗")
    
'''發點數卡在web register'''
def getPoints_write_into_useridpoints_web(user_data):
    '''發點數卡在web register'''
    lock = threading.Lock()
    with lock:
        tzone = timezone(timedelta(hours=8))
        nowyeardatetime = datetime.now(tz=tzone)
        nowyeardatetime = nowyeardatetime.isoformat()[:16].replace("T","-")


        this_user_uid = getUpdateUids()
        temp_useridslist = getuseridlist()
        web_user_uid = "web"+this_user_uid
        temp_useridslist.add(web_user_uid)

        try:
            update_nickname_list(user_data["username"])
            mydb = myclient["buff_online"]
            mycol = mydb["userid_points"]
            mycol.update_one({"_id": "1"},{"$set":{"userids":list(temp_useridslist)}})
            mycol.insert_one({"_id":web_user_uid,"nickname":user_data["username"],"got_reward_card_time":nowyeardatetime,"points":1,"uid":this_user_uid, "role":user_data["role"],"password":user_data["password"], "change_password":True})
            print(f"{web_user_uid}獲得點數卡")
        except:
            print(f"{web_user_uid}獲得點數卡，失敗")
     

'''計算User已預約幾個時間'''
def CountOrdersofUserid(userId):
    '''計算User已預約幾個時間'''
    lock = threading.Lock()
    with lock:
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

'''我本人拿全部訂單'''
def getGetAllorders():
    '''我本人拿全部訂單'''
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
    lock = threading.Lock()
    with lock:
        try:
            tzone = timezone(timedelta(hours=8))
            yeardate = datetime.now(tz=tzone)
            yeardate = yeardate.isoformat().split("T")[0].replace("-","")[2:]
            print("日期",yeardate)
            mycol = dbmethod("buff_online", f"final_order_{str(yeardate)}")
            # mydoc = mycol.find({'userId':userId},{'Date':1,'time':1})
            mydoc = mycol.find({}).sort('time',1)
            print("管理員拿全部訂單")
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
        except:
            message = {
                "type": "text",
                "text": "查詢訂單失敗"
            }
    return message

'''網頁查看訂單'''
def getWebGetAllOrder(date):
    '''網頁查看訂單'''
    lock = threading.Lock()
    with lock:
        try:
            mycol = dbmethod("buff_online", f"final_order_{date}")
            # mydoc = mycol.find({'userId':userId},{'Date':1,'time':1})
            mydoc = mycol.find({}).sort('time',1)
            result_array = []
            for data in mydoc:
                result_array.append(data)
        except:
            print("查詢失敗")
    return result_array


'''刪除指定時間訂單，22:00後執行，因為可能有人棄單不能讓他更新點數'''
def getDeleteSomeOrderList(Timelist):
    '''刪除指定時間訂單，22:00後執行，因為可能有人棄單不能讓他更新點數'''
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

'''查看user個人點數'''
def getMyPointsText(userId):
    '''查看user個人點數'''
    mydb = myclient["buff_online"]
    mycol = mydb["userid_points"]
    mydoc = mycol.find_one({"_id":userId})


    point = mydoc["points"]

    message = {
                "type":"text",
                "text":f"目前點數：{point}"
    }
    return message

'''每到23:30更新點數'''
def getUpdatePoints():
    '''每到23:30更新點數'''
    lock =threading.Lock()
    with lock:
        tzone = timezone(timedelta(hours=8))
        yeardate = datetime.now(tz=tzone)
        yeardate = yeardate.isoformat().split("T")[0]
        yeardate = yeardate.replace("-","")[2:]
        mycol = dbmethod("buff_online",f"final_order_{yeardate}")
        mydoc = mycol.find({},{"_id":0,'userId': 1,'point': 1})
        updatepoint_userid = set()
        list1 = list(mydoc)
        print(list1)
        for data in list1:
            print(updatepoint_userid)
            updatepoint_userid.add(data["userId"])
            # print(type(updatepoint_userid))
        for userId in updatepoint_userid:
            try:
                mycol = dbmethod("buff_online",f"final_order_{yeardate}")
                mydoc = mycol.count_documents({"userId":userId})
                mycol = dbmethod("buff_online","userid_points")
                mycol.update_one({"_id":userId},{"$inc":{"points":mydoc}})
                print("更新點數成功。")
                message = {
                    "type":"text",
                    "text":"更新點數成功"
                }
            except:
                print("更新點數失敗。")
                message = {
                    "type":"text",
                    "text":"更新點數失敗"
                }
    return message

'''兌換時先查詢user點數用'''
def getuserIdPoints(userId):
    '''兌換時先查詢user點數用'''
    mycol = dbmethod("buff_online", "userid_points")
    mydoc = mycol.find_one({"_id":userId})
    point = mydoc["points"]

    return point

'''差一步就預約成功，請重新選時間函式'''
def getalmosttakeorder(userId, thisuser_yeardate_time):
    '''差一步就預約成功，請重新選時間函式'''
    mycol = dbmethod( "buff_online", "userid_trader_partner")
    mydoc = mycol.find_one({"_id" : "userid"},{"_id":0})
    if mydoc is None:
        userid_trader_partner = dict()
    else:
        userid_trader_partner = mydoc
    
    tzone = timezone(timedelta(hours=8))
    nowtime = datetime.now(tz=tzone).isoformat()[:16]
    mydb = myclient["buff_online"]
    mycol = mydb["userid_points"]
    mydoc = mycol.find_one({"_id":userId},{"_id":0, "nickname": 1})
    nicknameofthisuser = mydoc["nickname"]
    final_order_dbname = nowtime.split("T")[0].replace("-","")[2:]
    data = [
            #['write_yeardate_time',  'userid'  ,     'nickname'     , 'action' ,           'yeardate'      ,         'time'            ,           'tradename'            ,            'partyname'           ,  'location'  ,  'remark']
            [      nowtime         ,   userId   , nicknameofthisuser , "Later!" , thisuser_yeardate_time[0] , thisuser_yeardate_time[1] , userid_trader_partner[userId][0] , userid_trader_partner[userId][1] ,  "六條岔道"   ,f'{nicknameofthisuser}，要確認訂單時被搶先一步']
        ]
    
    file_path = f'./Data/final_order_{final_order_dbname}.csv'
    file_exists = os.path.isfile(file_path)
    with open(file_path, 'a', newline='',encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        if not file_exists:
            csv_writer.writerow(['write_yeardate_time',  'userid'  ,     'nickname'     , 'action' ,           'yeardate'            ,               'time'            ,           'tradename'            ,            'partyname'           ,  'location'  ,  'remark'])
        csv_writer.writerows(data)
        print(f'已成功寫入 {file_path}')

'''選擇要刪除的時間'''
def getChooseDeleteTime(userId):
    '''選擇要刪除的時間'''
    message = {
            "type": "template",
            "altText": "This is a buttons template",
            "template": {
            "type": "buttons",
            "text": "請選擇下方要刪除的時間",
            "actions": [
            
                       ]
                       }
              }
    
    
    tzone = timezone(timedelta(hours=8))
    yeardate = datetime.now(tz=tzone)
    nowtime = yeardate + timedelta(minutes=30)
    yeardate = yeardate.isoformat().split("T")[0].replace("-","")[2:]
    print("日期",yeardate)
    mycol = dbmethod("buff_online", f"final_order_{yeardate}")
    # mydoc = mycol.find({'userId':userId},{'Date':1,'time':1})
    mydoc = mycol.find({'userId':userId}).sort('time',1)
    nowtime = nowtime.isoformat().split("T")[1][:5]
    
    for data in mydoc:
        print("data")
        print(data)
        reversedtime = data['time']
        if nowtime >= "23:59":
            message["template"]["actions"].append(
                                            {
                                                "type": "message",
                                                "label":reversedtime,
                                                "text": f"您預定的{reversedtime}已在半個小時內，故不可刪除"
                                            }
                                            )
        else:
            message["template"]["actions"].append(
                                                {
                                                    "type": "postback",
                                                    "label": reversedtime,
                                                    "data": json.dumps({"time":reversedtime,"action":'Time want to delete'}),
                                                    "text": f"您選擇的是今日{reversedtime}的預約"
                                                }
                                                )
    return message

'''真的刪除使用者訂單並回傳預約刪除成立'''
def getDeleteTimeSurelyText(surelydeletedtime, userId):
    '''真的刪除使用者訂單並回傳預約刪除成立'''
    from functions import getuseridyeardatetime, getyeardatedict
    this_user_yeardate_time = getuseridyeardatetime(userId)
    yeardate = datetime.now()
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

            nowtime = datetime.now().isoformat()[:16]
            mydb = myclient["buff_online"]
            mycol = mydb["userid_points"]
            mydoc = mycol.find_one({"_id":userId},{"_id":0, "nickname": 1})
            nicknameofthisuser = mydoc["nickname"]
            final_order_dbname = nowtime.split("T")[0].replace("-","")[2:]
            data = [
                    #['write_yeardate_time',  'userid'  ,     'nickname'     , 'action' ,           'yeardate'            ,       'time'     , 'tradename' , 'partyname' ,  'location'  ,  'remark']
                    [      nowtime         ,   userId   , nicknameofthisuser , "Delete" ,this_user_yeardate_time[0] , surelydeletedtime ,     None    ,    None     ,  "六條岔道"   ,f'{nicknameofthisuser}，刪除{surelydeletedtime}的訂單']
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

    
    yeardate = this_user_yeardate_time[0]
    yeardatedict = getyeardatedict()
    yeardatetimelist = yeardatedict[yeardate]
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
            mycol.update_one({'_id':yeardate[5:7]},{'$set':{yeardate:yeardatetimelist}},True)
            print(f"把上述指定時間{surelydeletedtime}，從該日期的時間清單移除")
        except:
            print(f"把上述指定時間{surelydeletedtime}，從該日期的時間清單移除失敗")
    message = {
                "type":"text",
                "text": f"您先前在{yeardate} {surelydeletedtime}的預約，已被刪除"
    }
    return message

'''訂單日期寫入使用者歷史紀錄'''
def update_history_order(userId):
    '''訂單日期寫入使用者歷史紀錄'''
    from functions import getUseridNickname
    todaydate = datetime.now().isoformat().split("T")[0]
    todaydate = todaydate.replace("-","")[2:]
    lock = threading.Lock()
    with lock:
        try:
            mycol = dbmethod("buff_online","userid_points")
            mydoc = mycol.find_one({"_id":userId},{"_id":0,"nickname":1})
            nickname = mydoc["nickname"]
            mycol = dbmethod("buff_online","userid_order_history")
            print("==============================================")
            print("mycol:",mycol)
            mydoc = mycol.find_one({"_id":userId},{"_id":0,"order_date_history":1})
            print("mydoc:",mydoc)
            if mydoc is None:
                order_date_history = []
                order_date_history.append(todaydate)
                mycol.update_one({"_id":userId},{"$set":{"order_date_history":order_date_history,"nickname":nickname}},True)
            else:
                order_date_history = mydoc["order_date_history"]
                if todaydate not in order_date_history:
                    order_date_history.append(todaydate)
                    mycol.update_one({"_id":userId},{"$set":{"order_date_history":order_date_history,"nickname":nickname}},True)
        except:
            print("訂單日期寫入使用者歷史紀錄失敗")

'''訂單確認成功，把暫時資料庫的資料寫入最終訂單資料庫'''
def getRealFinalOrder(userId, ordered_time_list, checklist):
    '''訂單確認成功，把暫時資料庫的資料寫入最終訂單資料庫'''
    from functions import getuseridyeardatetime, getChooseTimeAgain
    thisuser_yeardate_time = getuseridyeardatetime(userId)
    yeardate = thisuser_yeardate_time[0]                                                              
    time = thisuser_yeardate_time[1]
    update_history_order(userId)
    lock =threading.Lock()
    with lock:
        try:
            id = datetime.now().isoformat()[5:7]
            mydb = myclient["buff_online"]
            mycol = mydb["yeardate_time"]
            mycol.update_one({'_id':id},{'$set':{yeardate:ordered_time_list}},True)
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
            time_id = checklist.index(time)
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
                "text": "恭喜預約成功"
             }
            print(f'寫入成功到final_order_{yeardate}：',dict)

        except:
            data = json.dumps({'action':'Time chosen'})
            message = getChooseTimeAgain()
            print("暫時訂單寫入確認訂單失敗。")
    return message

'''網頁一般用戶取得歷史訂單'''
def getWebUserHistoryOrder(nickname:str) -> tuple[str, list[str]]:
    '''網頁一般用戶取得歷史訂單'''

    mycol = dbmethod("buff_online","userid_order_history")
    mydoc = mycol.find_one({"nickname":nickname},{"_id":0,"order_date_history":1})
    order_date_history = mydoc["order_date_history"]
    mycol = dbmethod("buff_online","userid_points")
    mydoc = mycol.find_one({"nickname":nickname})
    userId = mydoc["_id"]

    return userId, order_date_history
'''取得用戶歷史訂單'''
def get_user_order_history(userId, order_date_history):
    '''取得用戶歷史訂單'''
    print(userId, order_date_history)
    order_history_list = []
    for date in order_date_history:
        print(date)
        mycol = dbmethod("buff_online",f"final_order_{date}")
        mydoc = mycol.find({"userId":userId},{"_id":0,"userId":0,"point":0,"time":0}).sort('time',1)
        for data in mydoc:
            temp = []
            for value in data:
                temp.append(data[value])
            order_history_list.append(temp)
    return order_history_list



'''取得當前狀態，休息or營業'''
def getNowState():
    '''取得當前狀態，休息or營業'''
    mycol = dbmethod("buff_online", "state")
    mydoc = mycol.find_one({"_id":0},{"_id":0}) 
    state = mydoc["state"]
    return state

'''剛好五點點數'''
def getFivepoints():
    '''剛好五點點數'''
    yellow_star = "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
    gray_star = "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gray_star_28.png"
    row = {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                {
                    "type": "separator"
                },
                ]
            }
    points_and_separator = [{
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                        {
                                            "type": "icon",
                                            "url": yellow_star,
                                            "size": "32px",
                                            "offsetStart": "18px"
                                        }
                                        ]
                            },
                            {
                                "type": "separator"
                            },
                            {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                        {
                                            "type": "icon",
                                            "url": gray_star,
                                            "size": "32px",
                                            "offsetStart": "18px"
                                        }
                                        ]
                            }
                           ]
    for _ in range(5):
        row["contents"].append(points_and_separator[0])
        row["contents"].append(points_and_separator[1])
    return row

'''改變用戶預定狀態'''
def getChangeUserstate(userId:str, state:int):
    '''改變用戶預定狀態'''
    lock = threading.Lock()
    with lock:    
        Reserve_willing = state
        mycol = dbmethod("buff_online", "userid_points")
        mycol.update_one({"_id":userId},{"$set":{"userid_state":Reserve_willing}},True)


'''查詢用戶預定狀態'''
def getUseridstate(userId):
    '''查詢用戶預定狀態'''
    lock = threading.Lock()
    with lock:    
        try:
            mycol = dbmethod("buff_online", "userid_points")
            mydoc = mycol.find_one({"_id":userId})
            Reserve_willing = mydoc["userid_state"]
        except:
            Reserve_willing = 0
    return Reserve_willing
        


'''不到五點'''
def getnotreachfivepoints(remainder):
    '''不到五點'''
    yellow_star = "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
    gray_star = "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gray_star_28.png"
    row = {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                {
                    "type": "separator"
                },
                ]
            }
    points_and_separator = [{
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                        {
                                            "type": "icon",
                                            "url": yellow_star,
                                            "size": "32px",
                                            "offsetStart": "18px"
                                        }
                                        ]
                            },
                            {
                                "type": "separator"
                            },
                            {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                        {
                                            "type": "icon",
                                            "url": gray_star,
                                            "size": "32px",
                                            "offsetStart": "18px"
                                        }
                                        ]
                            }
                           ]

    temp = 0
    for _ in range(5):
        if temp < remainder:
            temp += 1
            row["contents"].append(points_and_separator[0])
            row["contents"].append(points_and_separator[1])
        else:
            row["contents"].append(points_and_separator[2])
            row["contents"].append(points_and_separator[1])
    return row

'''查看點數卡'''
def getMypointsCard(userId):
    '''查看點數卡'''
    mydb = myclient["buff_online"]
    mycol = mydb["userid_points"]
    mydoc = mycol.find_one({"_id":userId})
    
    this_user_uid = mydoc["uid"]
    point = mydoc["points"]
    nickname = mydoc["nickname"]

    yellow_star = "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
    gray_star = "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gray_star_28.png"
    message = {
  "type": "flex",
  "altText": "this is a flex message",
  "contents":{
  "type": "bubble",
  "size": "giga",
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "text",
            "text": f"{nickname}的點數卡",
            "weight": "bold",
            "size": "20px"
          },
          {
            "type": "text",
            "text": f"No.{this_user_uid[:4]} {this_user_uid[4:]}",
            "weight": "bold",
            "align":"end",
            "size": "16px"
          }
          
        ]
      },
      {
            "type": "separator"
      }
    ]
  }
}

  }
    points_and_separator = [{
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                        {
                                            "type": "icon",
                                            "url": yellow_star,
                                            "size": "32px",
                                            "offsetStart": "18px"
                                        }
                                        ]
                            },
                            {
                                "type": "separator"
                            },
                            {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                        {
                                            "type": "icon",
                                            "url": gray_star,
                                            "size": "32px",
                                            "offsetStart": "18px"
                                        }
                                        ]
                            }
                           ]
    if point == 0:
        return message
    else:
        quotient = point // 5
        remainder = point % 5
        if quotient == 0:
            row = getnotreachfivepoints(remainder)
            message["contents"]["body"]["contents"].append(row)
            message["contents"]["body"]["contents"].append(points_and_separator[1])
        elif quotient ==1 :
            first_row = getFivepoints()
            second_row = getnotreachfivepoints(remainder)
            message["contents"]["body"]["contents"].append(first_row)
            message["contents"]["body"]["contents"].append(points_and_separator[1])
            message["contents"]["body"]["contents"].append(second_row)
            message["contents"]["body"]["contents"].append(points_and_separator[1])
        else:
            all_row = getFivepoints()
            message["contents"]["body"]["contents"].append(all_row)
            message["contents"]["body"]["contents"].append(points_and_separator[1])
            message["contents"]["body"]["contents"].append(all_row)
            message["contents"]["body"]["contents"].append(points_and_separator[1])
            message["contents"]["body"]["contents"].append({
                                                            "type":"text",
                                                            "text":"......"
                                                            })

            
    return message



'''拿取使用者暱稱,密碼,等級'''
def getUserdata():
    '''拿取使用者暱稱,密碼,等級'''
    mycol = dbmethod("buff_online","userid_points")
    mydoc = mycol.find()
    user_data = dict()
    for data in mydoc:
        user_data[data["nickname"]] ={"password":data["password"], "role":data["role"] }
    return user_data

'''拿取使用者名稱清單'''
def get_nickname_list():
    
    mycol = dbmethod("buff_online","userid_points")
    mydoc = mycol.find_one({'_id': '1'})
    return mydoc['nickname_list']

'''更新使用者名稱清單'''
def update_nickname_list(nickname):
    lock = threading.Lock()
    with lock:    
        try:
            nickname_list = get_nickname_list()
            nickname_list.append(nickname)
            mycol = dbmethod("buff_online","userid_points")
            mycol.update_one({'_id': '1'},{"$set":{'nickname_list': nickname_list}},True)
        except:
            pass
    
def getAllUsers():
    """獲取所有用戶數據"""
    try:
        db = myclient["buff_online"]  # 使用您的數據庫名稱
        users_collection = db["users"]  # 使用您的集合名稱
        return list(users_collection.find({}))
    except Exception as e:
        print(f"獲取用戶數據時出錯: {str(e)}")
        return []

def getUserByUsername(username):
    """根據用戶名獲取單個用戶數據"""
    try:
        db = myclient["buff_online"]
        users_collection = db["users"]
        return users_collection.find_one({"username": username})
    except Exception as e:
        print(f"獲取用戶 {username} 數據時出錯: {str(e)}")
        return None

def addUser(user_data):
    """添加新用戶"""
    try:
        db = myclient["buff_online"]
        users_collection = db["users"]
        # 檢查用戶名是否已存在
        if users_collection.find_one({"username": user_data["username"]}):
            raise Exception("用戶名已存在")
        # 插入新用戶數據
        result = users_collection.insert_one(user_data)
        return result.inserted_id
    except Exception as e:
        print(f"添加用戶時出錯: {str(e)}")
        raise e
