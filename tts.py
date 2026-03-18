from funasr import AutoModel
from config import config  # 新增
import requests

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