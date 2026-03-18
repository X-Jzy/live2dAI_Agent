import pyaudio
import wave
from config import config  # 新增

# 从配置获取音频参数
audio_config = config.get("audio_record", {})
CHUNK = audio_config.get("chunk", 1024)
FORMAT = pyaudio.paInt16 if audio_config.get("format") == "paInt16" else pyaudio.paInt16
CHANNELS = audio_config.get("channels", 1)
RATE = audio_config.get("rate", 44100)
DEFAULT_OUTPUT = audio_config.get("default_output", "record.wav")
MAX_DURATION = audio_config.get("max_duration", 20)

is_recording = 0  # 状态判断，主要用于打断

def record_audio(wave_out_path=None, record_second=None):
    """录音功能（使用配置的默认参数）"""
    global is_recording
    # 优先使用传入参数，否则使用配置
    wave_out_path = wave_out_path or DEFAULT_OUTPUT
    record_second = record_second or MAX_DURATION

    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    print("开始录制")
    is_recording = 1
    wf = wave.open(wave_out_path, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)

    for _ in range(0, int(RATE * record_second / CHUNK)):
        data = stream.read(CHUNK)
        wf.writeframes(data)
        if is_recording == 0:
            print("录音打断")
            break
    stream.stop_stream()
    stream.close()
    print("完成录制")
    is_recording = 0
    p.terminate()
    wf.close()