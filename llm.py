import base64
import json
import mimetypes
import os
import requests
from openai import OpenAI
import re
from tts import get_tts_audio
from config import config  # 新增
import time
import ollama
import live2d_api

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer
import numpy as np
import memory.rag
import memory.graph_memory

from langchain_ollama.chat_models import ChatOllama
from langchain.agents import create_agent

from langchain_openai import ChatOpenAI
# from tools.tools import (get_weather_tool,get_memory_tool,get_screenshot_tool,get_motion_tool,online_search_tool)  # 移到函数内部

# 读取预设（从配置获取路径）
prompt_file = config.get("llm.prompt_file", "prompt.txt")
try:
    with open(prompt_file, "r", encoding="utf-8") as file:
        system_prompt = file.read()
except FileNotFoundError:
    print(f"错误：文件 {prompt_file} 未找到。")
except Exception as e:
    print(f"读取预设文件时发生错误：{e}")

# 调用kimi api（从配置获取参数）
client = ollama

qwen = ChatOpenAI(
    api_key="sk-867816b206984424ba055bf23f25d5ad",  
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen3.5-plus-2026-02-15",
    max_completion_tokens=5000,
    extra_body={"enable_thinking": False}
)

def get_agent():
    from tools.tools import (get_weather_tool,get_screenshot_tool,get_motion_tool,online_search_tool,graph_search_tool)
    return create_agent(
        #model=ChatOllama(model="qwen3.5:2b",reasoning=False),
        model=qwen,
        system_prompt=prompt_file,
        tools=[get_weather_tool,get_screenshot_tool,get_motion_tool,online_search_tool,graph_search_tool],
        middleware=[],
    )

def get_agent_nopic():
    return create_agent(
        #model=ChatOllama(model="qwen3.5:2b",reasoning=False),
        model=qwen,
        tools=[],
        middleware=[],
    )

# agent = create_agent(
#     #model=ChatOllama(model="qwen3.5:2b",reasoning=False),
#     model=qwen,
#     system_prompt=prompt_file,
#     tools=[get_weather_tool,get_memory_tool,get_screenshot_tool,get_motion_tool,online_search_tool],
#     middleware=[],
# )

# agent_nopic = create_agent(
#     #model=ChatOllama(model="qwen3.5:2b",reasoning=False),
#     model=qwen,
#     tools=[],
#     middleware=[],
# )
# kimi = OpenAI(
#     api_key="sk-4GrkzGCvJaHAT0OqOxXMYMXMCX4U4TBNQa7sbPYaN5XVG66y",  
#     base_url="https://api.moonshot.cn/v1",
# )

# 连接到本地 Qdrant（默认端口 6333），也可以改为托管地址
QdrantClient = QdrantClient(host="localhost", port=6333)

# 使用 sentence-transformers 生成文本嵌入，括号内模型可上huggingface寻找替换
model = SentenceTransformer('shibing624/text2vec-base-chinese')

# 预设信息
system_messages = [
    {"role": "system", "content": system_prompt},
]

# 聊天记录
messages = []

# 从 memory.txt 中读取历史对话并填充到 messages 列表
def read_memory(messages:list):
    memory_path = os.path.join(os.path.dirname(__file__), "memory.txt")
    if os.path.exists(memory_path):
        try:
            # 读取整个文件并按空行分块，每个块内合并连续的非role行为同一消息的内容
            with open(memory_path, "r", encoding="utf-8") as f:
                raw = f.read()

            # 按一个或多个空行分割成块
            blocks = re.split(r"\n\s*\n", raw)

            timestamp_pattern = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
            role_pattern = re.compile(r'^(master:|AI:|prompt:)(.*)', re.IGNORECASE)

            for block in blocks:
                lines = [ln.rstrip() for ln in block.splitlines() if ln.strip()]
                if not lines:
                    continue

                i = 0
                while i < len(lines):
                    line = lines[i]
                    # 跳过纯时间戳行
                    if timestamp_pattern.match(line):
                        i += 1
                        continue

                    m = role_pattern.match(line)
                    if m:
                        label = m.group(1).lower()
                        content_lines = [m.group(2).lstrip()]
                        i += 1
                        # 合并随后属于同一消息的行，直到遇到下一个 role 或 timestamp
                        while i < len(lines) and (not role_pattern.match(lines[i])) and (not timestamp_pattern.match(lines[i])):
                            content_lines.append(lines[i])
                            i += 1

                        content = "\n".join(content_lines).strip()
                        if not content:
                            continue

                        if label == 'master:':
                            messages.append({"role": "user", "content": content})
                        elif label == 'ai:':
                            messages.append({"role": "assistant", "content": content})
                        # 对于 prompt: 我们当前不将其作为对话消息导入
                        continue
                    else:
                        i += 1
        except Exception as e:
            print(f"读取记忆文件时出错: {e}")

read_memory(messages)


# 限制记忆消息数 ———— 超过上限浓缩
def make_new_messages(input: str , n: int = None) -> list[dict]:
    global messages

    new_messages = []
    new_messages.extend(system_messages)

    n = n or config.get("llm.max_memory", 30)  # 使用配置的最大记忆数
    print("当前对话数："+str(len(messages)))

    # if len(messages) >= n:
    #     prompt = f"在此之前我们有若干条对话，现在已经超过容量上限，请你将此前的对话提炼为新的prompt文件,200字以内，保持你的认知观念和语言风格，以及此前master与你之间的约定等等,不要提及任何关于你是agent或ai的内容，提炼出来的对话记忆一定要严格关于此前的对话记忆而不是关于你ai的道德、伦理等的套话."
    #     messages.append({"role": "user", "content": prompt})
    #     completion = client.chat(
    #         model=config.get("llm.model"),  # 从配置获取模型
    #         messages=messages,
    #         #temperature=0.1,
    #         think = False
    #     )
    #     answer = completion.message.content
    #     new_messages.append({"role": "user", "content": prompt})
    #     new_messages.append({"role": "assistant", "content": answer})
    #     #直接覆盖掉原有的记忆体，从30变为1
    #     #在此之前做个备份，舍不得真删掉啊QAQ
    #     with open("memory.txt", "r", encoding="utf-8") as f:
    #         with open("memory_copy.txt", "a+", encoding="utf-8") as f_c:
    #             for raw in f:
    #                 line = raw.strip()
    #                 f_c.write(line)
    #     with open("memory.txt","w",encoding='utf-8') as f:
    #         f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"\n"+"user:"+prompt+"\n"+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"\n"+"AI:"+answer+"\n"+"\n") 
    #     messages=[]
        
    messages.append({"role":"user","content":input})
    new_messages.extend(messages)
    print(new_messages)
    return new_messages

# 聊天函数
def chat(input: str):
    from tools.tools import motion_id
    # answer = check_weather_intent(input)
    # if answer == "是":
    #     weather_data = weather.get_weather(0)
    #     input = f"今天是{time.localtime()},用户问：{input}\n天气api的调用结果：{weather_data}\n请根据天气数据回答用户的问题。"
    # elif answer == "未来":
    #     weather_data = weather.get_weather(1)
    #     input = f"今天是{time.localtime()},用户问：{input}\n天气api的调用结果：{weather_data}\n请根据天气数据回答用户的问题。"
    
    res = get_agent().invoke({
        "messages":make_new_messages(input)
    })
    print(res)
    latest_message = res["messages"][-1]
    if latest_message.content:
        res=latest_message.content.strip()

    messages.append({
        "role": "assistant",
        "content": res
    })

    # completion = kimi.chat.completions.create(
    #     model="moonshot-v1-8k",
    #     messages=make_new_messages(input),
    #     # temperature=config.get("llm.temperature", 0.3),  # 从配置获取温度
    #     #think = False
    # )

    # message = completion.choices[0].message.content
    # #message = completion.message.content
    # messages.append({
    #     "role": "assistant",
    #     "content": message
    # })

    # message_en = message
    # pure_text_en = handle_text(message_en)  # 提取纯净text
    # if config.get("tts.text_lang")!="zh":
    #     get_tts_audio(pure_text_en)
    # message_zh = translate(message_en)
    # pure_text_zh = handle_text(message_zh)
    # if config.get("tts.text_lang")=="zh":
    #     get_tts_audio(pure_text_zh)
    print(res)
    get_tts_audio(res)
    # print("英文回复:" + message_en)

    # 发送回复到Live2D
    live2d_api.send_json_message(res)
    live2d_api.send_sound()
    live2d_api.send_motion(motion_id)

    # 短期记忆
    with open("memory.txt","a+",encoding='utf-8') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"\n"+"master:"+input+"\n") 
        f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"\n"+"AI:"+res+"\n"+"\n") 

    # RAG记忆
    hybrid_text = "Master:"+input+" "+"AI:"+res
    memory.rag.store_chat(hybrid_text)

    # 五元组Graph记忆
    quintuples = memory.graph_memory.extract_quintuples(hybrid_text)
    memory.graph_memory.store_quintuples(quintuples)

    return res

def handle_text(text: str):
    pattern = r'【[^】]*】'
    return re.sub(pattern, '', text)

# def check_weather_intent(text: str):
#     """基于输入文本的关键词匹配判断用户是否在询问天气。

#     返回值严格为三个之一：'是'（表示查询当前天气）、'未来'（表示查询未来天气）、'否'（非天气查询）。
#     此函数不再调用 LLM，而是直接从用户输入提取关键词进行判断。
#     """
#     if not text or not isinstance(text, str):
#         return "否"

#     s = text.lower()

#     # 先检测表示未来的关键词
#     # 例如，“明天我有个会”，这类不涉及天气倾向的，也可以使用天气预报提醒你明天的天气
#     if re.search(r"明天|后天|tomorrow|after tomorrow", s):
#         print("天气于此倾向:未来")
#         return "未来"

#     # 再检测明显的天气查询关键词
#     if re.search(r"天气|气温|温度|下雨|下雪|降雨|降水|湿度|风力|刮风|预报|晴|阴|多云|会不会雨|会下雨|会下雪", s):
#         print("天气于此倾向:是")
#         return "是"

#     # 默认认为不是天气查询
#     print("天气于此倾向:否")
#     return "否"

# 不再在prompt写翻译要求了，而是独立给llm翻译吧
def translate(text:str):
    prompt = f"将这段文字原封不动翻译为中文，输出仅包含这句话的译文，不要逐字逐句翻译，而是在含义相同的情况下用中文的语言习惯说出，不要包含其他任何内容:/{text}/"
    message=[]
    message.append({"role": "system","content": prompt})
    completion = client.chat(
        model=config.get("llm.model"), 
        messages=message,
        # temperature=0.1,
        think = False
    )
    # answer = completion.choices[0].message.content
    answer = completion.message.content
    return answer

#图像分析
def picture_analysis(pic_url: str, input: str):
    """对图片进行分析并返回模型的文本回答。"""
    prompt = input 

    global messages

    if os.path.exists(pic_url):
        mime = mimetypes.guess_type(pic_url)[0] or "image/png"
        with open(pic_url, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        # 使用 data URI 字符串，API 要求 image_url.url 是字符串
        image_repr = f"data:{mime};base64,{b64}"
    else:
        image_repr = pic_url

    msg = {"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": image_repr}},
    ]}
    messages.append(msg)

    res = get_agent_nopic().invoke({
        "messages":messages
    })

    print(res)

    latest_message = res["messages"][-1]
    if latest_message.content:
        res=latest_message.content.strip()

    with open("memory.txt","a+",encoding='utf-8') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"\n"+"master:"+input+"传入图像:"+pic_url+"\n") 
        f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"\n"+"AI:"+res+"\n"+"\n") 

    print(res)

    # answer = completion.message.content
    get_tts_audio(res)
    live2d_api.send_sound()
    return res