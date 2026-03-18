from funasr import AutoModel
from config import config  # 新增

# 从配置获取ASR参数
asr_config = config.get("asr", {})
model = AutoModel(
    model=asr_config.get("model", "paraformer-zh"),
    vad_model=asr_config.get("vad_model", "fsmn-vad"),
    punc_model=asr_config.get("punc_model", "ct-punc-c"),
    spk_model=asr_config.get("spk_model", "cam++"),  # 可选，如果需说话人分离
    disable_update=True
)


def audio_to_text(audio_path=None):
    """将音频转换为文本（默认使用配置的路径）"""
    # 从配置获取默认音频路径
    default_path = asr_config.get("default_audio_path", "record.wav")
    audio_path = audio_path or default_path
    
    res = model.generate(
        input=audio_path,
        batch_size_s=60,
    )
    print(res)
    return res
                