import pyaudio
import numpy as np
import time
import wave
import os
from config import config  # 新增

class VAD:
    def __init__(self):
        # 从配置获取音频参数
        vad_config = config.get("vad", {})
        self.CHUNK = vad_config.get("chunk", 1024)
        self.FORMAT = pyaudio.paInt16 if vad_config.get("format") == "paInt16" else pyaudio.paInt16
        self.CHANNELS = vad_config.get("channels", 1)
        self.RATE = vad_config.get("rate", 16000)

        # 从配置获取VAD参数
        self.THRESHOLD = vad_config.get("threshold", 1000)
        self.SPEECH_TIMEOUT = vad_config.get("speech_timeout", 10.0)
        self.MIN_SPEECH_DURATION = vad_config.get("min_speech_duration", 0.8)
        self.SILENCE_LIMIT = vad_config.get("silence_limit", 1.5)
        self.PRE_SPEECH = vad_config.get("pre_speech", 1)
        self.temp_prefix = vad_config.get("temp_recording_prefix", "temp_recording_")

        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_listening = False
        self.audio_buffer = []
        self.speech_started = False
        self.last_speech_time = 0
        self.speech_start_time = 0

    def start_listening(self, on_speech_ended):
        """开始监听"""
        self.is_listening = True
        self.on_speech_ended = on_speech_ended
        
        try:
            self.stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
                input_device_index=None
            )
            
            print("开始语音监听...")
            consecutive_silence = 0
            min_speech_frames = int(self.MIN_SPEECH_DURATION * self.RATE / self.CHUNK)
            speech_frames = 0
            
            while self.is_listening:
                try:
                    data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    volume = np.abs(audio_data).mean()
                    
                    # 检测语音开始
                    if volume > self.THRESHOLD and not self.speech_started:
                        print("开始说话")
                        self.speech_started = True
                        self.speech_start_time = time.time()
                        self.last_speech_time = time.time()
                        self.audio_buffer = [data]
                        speech_frames = 1
                        consecutive_silence = 0
                    
                    # 持续录音
                    elif self.speech_started:
                        self.audio_buffer.append(data)
                        speech_frames += 1
                        
                        if volume > self.THRESHOLD:
                            self.last_speech_time = time.time()
                            consecutive_silence = 0
                        else:
                            consecutive_silence += 1
                        
                        # 检查是否应该结束说话
                        silence_duration = time.time() - self.last_speech_time
                        total_duration = time.time() - self.speech_start_time + self.PRE_SPEECH
                        
                        # 条件1: 静音时间超过阈值 且 总时长足够
                        if (silence_duration > self.SILENCE_LIMIT and total_duration > self.MIN_SPEECH_DURATION):
                            print(f"检测到语音结束 - 总时长: {total_duration:.2f}s")
                            self._process_speech()
                            self.speech_started = False
                            self.audio_buffer = []
                        
                        # 条件2: 超时保护
                        elif total_duration > self.SPEECH_TIMEOUT:
                            print(f"语音超时 - 总时长: {total_duration:.2f}s")
                            self._process_speech()
                            self.speech_started = False
                            self.audio_buffer = []
                            
                except Exception as e:
                    print(f"读取音频数据时出错: {e}")
                    break
                    
        except Exception as e:
            print(f"打开音频流时出错: {e}")

    def _process_speech(self):
        """处理检测到的语音"""
        if not self.audio_buffer or len(self.audio_buffer) < 5:
            print("音频数据太少，忽略")
            return
            
        try:
            # 生成唯一文件名
            timestamp = int(time.time())
            filename = f"{self.temp_prefix}{timestamp}.wav"
            
            # 保存音频文件
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
                wf.setframerate(self.RATE)
                wf.writeframes(b''.join(self.audio_buffer))
            
            # 检查文件有效性
            file_size = os.path.getsize(filename)
            duration = len(self.audio_buffer) * self.CHUNK / self.RATE
            print(f"音频已保存: {filename}, 大小: {file_size} bytes, 时长: {duration:.2f}s")
            
            if file_size < 1000:
                print("音频文件太小，可能无效")
                os.remove(filename)
                return
                
            # 调用回调函数
            self.on_speech_ended(filename)
            
        except Exception as e:
            print(f"处理语音时出错: {e}")

    def stop_listening(self):
        """停止监听"""
        self.is_listening = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        print("停止语音监听")