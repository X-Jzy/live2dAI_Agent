import tools.tools
import time
import llm
from pic_cap.pic_cap import pic_cap
import live2d_api

game_listening = 0

game_msgs = [msg.copy() for msg in llm.system_messages]

# 多模态直接拿上下文和图片
def game_listen_circle_agent():
    """按时间轮询用户屏幕获取信息"""
    print("屏幕监听启动")
    while True:
        time.sleep(10)
        if game_listening==0:
            print("退出屏幕监听")
            break
        live2d_api.send_json_message("开始屏幕识别")
        uri = pic_cap()
        llm.picture_analysis(uri,"这是用户的屏幕截图，请你根据截图的内容与Master主动对话，或是吐槽、或是闲谈，尤其是master正在打游戏时，可以主动往游戏话题上靠,注意话不要太多，最好不要超过80字")
        time.sleep(50)

# 区分llm与vlm
def game_listen_circle_depart():
    """按时间轮询用户屏幕获取信息"""
    print("屏幕监听启动")
    while True:
        time.sleep(10)
        if game_listening==0:
            print("退出屏幕监听")
            break
        uri = pic_cap()
        response = llm.pic_agent.chat.completions.create(
            model="glm-4.6v-flash", 
            messages=[
                {
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": uri
                            }
                        },
                        {
                            "type": "text",
                            "text": "这是用户屏幕的截图,详细描述图片上的内容,尤其是与游戏相关的画面要详细描述,仅仅是描述即可,不要有其他任何多余的输出,仅输出'这张图片描述了xxxxxx'即可"
                        }
                    ],
                    "role": "user"
                }
            ],
            thinking={
                "type": "disabled"
            }
        )
        res = response.choices[0].message.content or ""
        if not isinstance(res, str):
            res = str(res)

        print(f"中段vlm识别结果:{res}")

        from tools.tools import motion_id

        global game_msgs

        # 清洗历史消息，确保传给模型的消息结构合法（role + string content）
        safe_messages = []
        for msg in game_msgs:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if not isinstance(content, str):
                content = "" if content is None else str(content)
            safe_messages.append({"role": role, "content": content})
        game_msgs = safe_messages
        master_input = f"[game_screen]{res}"
        
        game_msgs.append({
            "role": "user",
            "content": f"你已进入游戏监听模式，在此模式下你将不时收到master的屏幕内容描述，请你根据master屏幕的内容做出合适的对话,或是吐槽、或是闲谈，内容如下{res}"
        })
       
        agent_result = llm.get_agent().invoke({
            "messages":game_msgs
        })

        print(agent_result)
        
        latest_message = agent_result["messages"][-1]
        content = latest_message.content
        if isinstance(content, str):
            result = content.strip()
        elif content is None:
            result = ""
        else:
            result = str(content).strip()

        game_msgs.append({
            "role": "assistant",
            "content": result
        })

        print(result)

        import tts

        tts.get_tts_audio(result)

        # 发送回复到Live2D
        live2d_api.send_json_message(result)
        live2d_api.send_sound()
        print(motion_id)
        live2d_api.send_motion(motion_id)

        # 短期记忆
        with open("memory.txt","a+",encoding='utf-8') as f:
            f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"\n"+"master:"+master_input+"\n") 
            f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"\n"+"AI:"+result+"\n"+"\n") 

        import memory.rag
        import memory.graph_memory

        # RAG记忆
        hybrid_text = "Master:"+master_input+" "+"AI:"+result
        memory.rag.store_chat(hybrid_text)

        # 五元组Graph记忆
        quintuples = memory.graph_memory.extract_quintuples(hybrid_text)
        memory.graph_memory.store_quintuples(quintuples)

        time.sleep(50)