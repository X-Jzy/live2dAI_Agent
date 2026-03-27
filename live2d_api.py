import json
import os
from pydub import AudioSegment
from config import config  # 新增

def send_json_message(json_message: str):
    # 从配置获取WebSocket地址
    ws_uri = config.get("live2d.websocket_uri", "ws://127.0.0.1:10086/api")
    tts_output = config.get("tts.output_file", "output.wav")

    data = {
        "msg": 11000,
        "msgId": 1,
        "data": {
            "id": 0,
            "text": json_message,
            "textFrameColor": 0x000000,
            "textColor": 0xFFFFFF,
            "duration": (get_duration_pydub(tts_output) + 4) * 1000
        }
    }

    try:
        from websocket import create_connection  # 延迟导入，避免启动依赖
        ws = create_connection(ws_uri)
        ws.send(json.dumps(data))
    except Exception as e:
        print("Live2D消息发送错误:", str(e))

def get_duration_pydub(file_path):
    if not os.path.exists(file_path):
        print(f"音频文件不存在: {file_path}")
        return 0
    audio = AudioSegment.from_file(file_path)
    return len(audio) / 1000.0  # 转换为秒

def send_sound(sound_path: str = None):
    # 从配置获取WebSocket地址和音频路径
    ws_uri = config.get("live2d.websocket_uri", "ws://127.0.0.1:10086/api")
    tts_output = sound_path or config.get("tts.output_file", "output.wav")

    data = {
        "msg": 13500,
        "msgId": 1,
        "data": {
            "id": 0,
            "channel": 0,
            "volume": 1,
            "delay": 0,
            "type": 0,
            "sound": tts_output
        }
    }

    try:
        from websocket import create_connection  # 延迟导入
        ws = create_connection(ws_uri)
        ws.send(json.dumps(data))
    except Exception as e:
        print("Live2D音频发送错误:", str(e))

def send_motion(id:int):
    ws_uri = config.get("live2d.websocket_uri", "ws://127.0.0.1:10086/api")

    data = {
        "msg": 13200,
        "msgId": 1,
        "data": {
            "id": 0,
            "type": 1,
            "mtn": "C:\\Users\\X.J\\Desktop\\hiyori-main\\hiyori_m0"+str(id)+".motion3.json"
        }
    }

    try:
        from websocket import create_connection  # 延迟导入
        ws = create_connection(ws_uri)
        ws.send(json.dumps(data))
        print("live2d动作发送成功")
    except Exception as e:
        print("Live2D动作发送错误:", str(e))