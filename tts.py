import queue
import threading
import time
import uuid

from funasr import AutoModel
from config import config  # 新增
import requests
import live2d_api

live2d_text = ""

# 从配置获取ASR参数
asr_config = config.get("asr", {})
model = AutoModel(
    model=asr_config.get("model", "paraformer-zh"),
    vad_model=asr_config.get("vad_model", "fsmn-vad"),
    punc_model=asr_config.get("punc_model", "ct-punc-c"),
    spk_model=asr_config.get("spk_model", "cam++"),  # 可选，如果需说话人分离
    disable_update=True
)

# 调用TTS API生成音频
def get_tts_audio(text: str, output_file: str = None) -> bool:
    """
    调用TTS API的GET方法生成音频并保存
    :param text: 待合成的文本
    :param output_file: 音频输出路径
    :return: 成功返回True，失败返回False
    """
    tts_config = config.get("tts", {})
    if output_file is None:
        output_file = tts_config.get("output_file", "output.wav")
    
    params = {
        "text": text,
        "text_lang": tts_config.get("text_lang", "zh"),
        "ref_audio_path": tts_config.get("ref_audio_path", ""),
        "prompt_lang": tts_config.get("prompt_lang", "en"),
        "prompt_text": tts_config.get("prompt_text", ""),
        "text_split_method": tts_config.get("text_split_method", "cut2"),
        "batch_size": tts_config.get("batch_size", 1),
        "media_type": tts_config.get("media_type", "wav"),
        "streaming_mode": tts_config.get("streaming_mode", False)
    }

    api_url = tts_config.get("api_url", "http://127.0.0.1:9880/tts")
    
    try:
        response = requests.get(api_url, params=params)
        if response.status_code == 200:
            with open(output_file, "wb") as f:
                f.write(response.content)
            print(f"音频已保存至：{output_file}")
            return True
        else:
            print(f"TTS API调用失败：{response.json().get('message', '未知错误')}")
            return False
    except Exception as e:
        print(f"调用TTS API时发生错误：{str(e)}")
        return False
    

def get_tts_audio_stream(input:str):
    # input符号分块
    import re

    global live2d_text 
    live2d_text = input

    chunks = re.findall(r'[^,，;；?？!！~。\.]+[,，;；?？!！~。\.]*', input.strip())
    _ensure_audio_consumer()
    for chunk in chunks:
        chunk = chunk.strip()
        print(chunk)
        if not chunk:
            continue
        output_file = _make_chunk_output_path()
        ok = get_tts_audio(chunk, output_file=output_file)
        if ok:
            _audio_queue.put(output_file)
        else:
            print("TTS分块生成失败，跳过播放")


_audio_queue = queue.Queue()
_audio_worker = None
_audio_worker_lock = threading.Lock()


def _ensure_audio_consumer():
    global _audio_worker
    with _audio_worker_lock:
        if _audio_worker is None or not _audio_worker.is_alive():
            _audio_worker = threading.Thread(
                target=_audio_consumer_loop,
                name="tts_audio_consumer",
                daemon=True,
            )
            _audio_worker.start()


def _make_chunk_output_path() -> str:
    tts_config = config.get("tts", {})
    output_file = tts_config.get("output_file", "output.wav")
    base, ext = output_file.rsplit(".", 1) if "." in output_file else (output_file, "wav")
    return f"{base}_chunk_{uuid.uuid4().hex}.{ext}"


def _audio_consumer_loop():
    while True:
        audio_path = _audio_queue.get()
        try:
            from tools.tools import motion_id
            live2d_api.send_sound(audio_path)
            live2d_api.send_json_message(live2d_text)
            live2d_api.send_motion(motion_id)
            duration = live2d_api.get_duration_pydub(audio_path)
            # 留一点缓冲，避免连播抢占
            time.sleep(max(0.1, duration-1.8))
        except Exception as e:
            print(f"音频播放队列处理失败: {e}")
        finally:
            _audio_queue.task_done()

