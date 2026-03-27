import psutil
import time
from PySide6.QtCore import Signal, QObject
import llm
from config import config
import re

class GameSignal(QObject):
    game_detected = Signal(str, str, str, bool)  # 用于传递游戏检测信息

# 实例化信号对象（供全局使用）
game_signal = GameSignal()

# 全局字典，记录每个游戏进程是否已检测到
detected_games = {}

def listen_game():
    # 从配置获取游戏参数
    game_config = config.get("game", {})
    game_process_names = game_config.get("process_names")
    check_interval = game_config.get("check_interval", 2)

    # 记录应用启动时的所有进程ID
    initial_pids = set(psutil.pids())

    while True:
        for process_name in game_process_names:
            # 获取当前所有匹配的进程ID
            current_pids = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() == process_name[0].lower():
                        current_pids.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # 检查是否有新启动的进程（PID不在初始列表中）
            new_pids = [pid for pid in current_pids if pid not in initial_pids]
            key = process_name[0].lower()
            if new_pids and not detected_games.get(key, False):
                print(f"检测到新游戏 {process_name[1]} 已打开，开始AI主动对话。")
                # AI主动对话逻辑
                game_info = f"检测到程序 {process_name[1]} 已打开，开始AI主动对话。"
                response = llm.chat(game_info, source="proactive")
                if response is None:
                    print("[INFO] 游戏主动播报已跳过，等待用户对话完成")
                    continue
                pattern = r'【[^】]*】'
                pure_text = re.sub(pattern, '', response)
                if pure_text != response:
                    expression = response.split("【")[1][:2]
                    print("表情" + expression)
                else:
                    expression = "normal"
                game_signal.game_detected.emit("AI", pure_text, expression, False)
                detected_games[key] = True
            elif not current_pids:
                detected_games[key] = False
        time.sleep(check_interval)