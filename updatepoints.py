#ver1.0每日23:30就會執行以便更新點數，用crontab設定
from datetime import datetime, timedelta, timezone
import threading
import pymongo
import configparser
from datetime import datetime

config = configparser.ConfigParser()
config.read('/home/linebot008/Buffonline/config.ini')


tzone = timezone(timedelta(hours=8))
yeardate = datetime.now(tz=tzone)
yeardate = yeardate.isoformat().split("T")[0]
yeardate = yeardate.replace("-","")[2:]
username = config.get('mongodb', 'username')
password = config.get('mongodb', 'password')
hostlocation = config.get('mongodb', 'hostlocation')
# myclient = pymongo.MongoClient("mongodb://localhost:27017/")
cluster_url =f"mongodb+srv://{username}:{password}@{hostlocation}/?retryWrites=true&w=majority&appName=GueiMing"
myclient = pymongo.MongoClient(cluster_url, username=username,password=password)
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
            date = datetime.now().isoformat()[:10]
            print(f"{date}更新點數成功。")
        except:
            print(f"{date}更新點數失敗。")