import os
import time
import live2d_api
from langchain_core.tools import tool
from tts import get_tts_audio
import requests
from config import config 
import random
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer
import numpy as np
import memory.rag
import weather.weather
from pic_cap.pic_cap import pic_cap
import memory.graph_memory

motion_id=0

@tool(description="天气查询")
def get_weather_tool(is_future:bool) -> str:
    return weather.weather.get_weather(is_future)

@tool(description="查询历史记忆")
def get_memory_tool(input:str)->list[str]:
    return memory.rag.rag_search(input)

# 不能直接传base64,会爆token
# 目前能用,先用着吧,两套方案:1,agent仅做调用判断,对话转移给其他模型 2,其他模型做图片分析,内容转回给agent用于对话
@tool(description="捕获用户桌面并响应")
def get_screenshot_tool():
    import llm

    # 调用截图模块，返回 data URI 字符串
    img_data_uri = pic_cap()

    msg = [{"role": "user", "content": [
        {"type": "text", "text": "这是用户屏幕的截图,详细描述图片上的内容,仅仅是描述即可,不要有其他任何多余的输出,仅输出'这张图片描述了xxxxxx'即可"},
        {"type": "image_url", "image_url": {"url": img_data_uri}},
    ]}]

    res = llm.get_agent_nopic().invoke({
        "messages":msg
    })

    latest_message = res["messages"][-1]
    if latest_message.content:
        res=latest_message.content.strip()

    print("图像识别Tool中段输出:"+res)

    return res

@tool(description="根据对话展示心情")
def get_motion_tool(emotion:str):
    global motion_id
    print("当前心情:"+emotion)
    if emotion=="happy":
        list1 = [1,2,3,5]
        motion_id = random.choice(list1) 
    elif emotion =="sad":
        list1 = [4,7,8]
        motion_id = random.choice(list1)
    elif emotion == "surprised":
        list1 = [6]
        motion_id = random.choice(list1)
    return emotion

@tool(description="联网搜索")
def online_search_tool(input:str):
    from langchain_community.tools import DuckDuckGoSearchResults
    search = DuckDuckGoSearchResults()
    result = search.invoke(input)
    print("搜索结果:"+result)
    return result

@tool(description="知识图谱记忆搜索")
def graph_search_tool(input:str):
    return memory.graph_memory.search_quintuples(input)