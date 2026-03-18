import time
from PySide6.QtCore import Signal, QObject
import llm
from config import config
import re
import os

class TimeSignal(QObject):
    time_detected = Signal(str, str, str, bool)  # 用于传递时间检测信息

time_signal = TimeSignal()

listening_date = [[1,1],[2,14],[4,1],[5,1],[6,1],[7,1],[8,1],[9,1],[10,1],[12,27],[3,18]]
listening_time=[0,8,12,14,17,20,22]

localtime = time.localtime(time.time())

# 节日播报记录文件
HOLIDAY_RECORD_FILE = "holiday_broadcasted.txt"

def get_current_date_str():
    """获取当前日期字符串，格式为YYYY-MM-DD"""
    return time.strftime("%Y-%m-%d", localtime)

def has_broadcasted_today():
    """检查今天是否已经播报过节日"""
    if not os.path.exists(HOLIDAY_RECORD_FILE):
        return False
    try:
        with open(HOLIDAY_RECORD_FILE, "r", encoding="utf-8") as f:
            last_broadcast_date = f.read().strip()
        return last_broadcast_date == get_current_date_str()
    except:
        return False

def record_broadcast():
    """记录今天的播报"""
    with open(HOLIDAY_RECORD_FILE, "w", encoding="utf-8") as f:
        f.write(get_current_date_str())

def listen_time():
    while True:
        localtime = time.localtime(time.time())
        #特殊节日播报
        for date in listening_date:
            if date[0]==localtime.tm_mon and date[1]==localtime.tm_mday:
                if not has_broadcasted_today():
                    print("今天是"+str(date[0])+"月"+str(date[1])+"日，触发特殊节日播报")
                    response = llm.chat("今天是"+str(date[0])+"月"+str(date[1])+"日，开始AI主动对话")
                    pattern = r'【[^】]*】'
                    pure_text = re.sub(pattern, '', response)
                    if pure_text != response:
                        expression = response.split("【")[1][:2]
                        print("表情" + expression)
                    record_broadcast()
                    print("节日播报完成，已记录今天不再重复播报")
                break
            
        #特殊时间播报
        for cur_time in listening_time:
            if cur_time == localtime.tm_hour and localtime.tm_min==0:     #仅准点触发
                print("现在是"+str(cur_time)+",触发主动报时")
                response = llm.chat("现在是"+str(cur_time)+"点，和Master主动打个招呼吧")
                pattern = r'【[^】]*】'
                pure_text = re.sub(pattern, '', response)
                if pure_text != response:
                    expression = response.split("【")[1][:2]
                    print("表情" + expression)
                print("时间播报完成，已记录今天不再重复播报")
                time.sleep(90)
            
