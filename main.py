from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QTextCursor
from PySide6.QtCore import Signal, QObject
import tools.tools
import vad
import sys
import html  
import threading
import re
import llm
import live2d_api
import email_listening
import time_listening
import game_listening
import audio_record
import asr
from email_listening import email_signal  
from game_listening import game_signal
from time_listening import time_signal
from config import config
from config import ConfigLoader

class ChatGUI(QObject):
    update_ui_signal = Signal(str, str,str, bool)
    email_notify_signal = Signal(str,str, str, bool)  # 用于传递邮件提醒文本
    def __init__(self):
        super().__init__()
        # 加载UI界面
        self.ui = QUiLoader().load('main.ui')
        
        # 绑定信号与槽（按钮点击/回车触发发送消息）
        self.ui.sendButton.clicked.connect(self.send_message)
        self.ui.inputField.returnPressed.connect(self.send_message)
        self.ui.audioButton.clicked.connect(self.handle_audio)
        email_signal.new_email.connect(self.add_message_to_display)
        game_signal.game_detected.connect(self.add_message_to_display)
        time_signal.time_detected.connect(self.add_message_to_display)
        self.email_notify_signal.connect(self.add_message_to_display)
        self.update_ui_signal.connect(self.add_message_to_display)
        self.ui.chatButton.clicked.connect(self.toggle_realtime_chat)
        self.ui.languageBox.currentIndexChanged.connect(self.change_audio_language)
        self.ui.snedFileButton.clicked.connect(self.handle_send_file)
        # 启动邮件监听线程（守护线程，随主程序退出）
        self.start_email_listener()
        # 启动游戏监听线程
        self.start_game_listener()
        # 启动时间监听线程
        self.start_time_listener()

        # 初始化VAD
        self.vad = vad.VAD()
        self.is_realtime_chat = False
        self.is_ai_responding = False  # 防止重叠请求
        self.pending_file = None  # 记录已选择但尚未发送的文件路径

    def start_email_listener(self):
        """启动邮件监听线程"""
        listener_thread = threading.Thread(target=email_listening.listen_email, daemon=True)
        listener_thread.start()
        print('[INFO] 邮件监听线程已启动')

    def start_game_listener(self):
        """启动游戏监听线程"""
        listener_thread = threading.Thread(target=game_listening.listen_game, daemon=True)
        listener_thread.start()
        print('[INFO] 游戏监听线程已启动')

    def start_time_listener(self):
        """启动游戏监听线程"""
        listener_thread = threading.Thread(target=time_listening.listen_time, daemon=True)
        listener_thread.start()
        print('[INFO] 时间监听线程已启动')

    def add_message_to_display(self, sender: str, content: str, expression: str , is_user: bool):
        """添加消息到聊天区域"""
        # 转义HTML特殊字符，防止格式错乱
        escaped_content = html.escape(content).replace('\n', '<br>')
        
        # 获取当前时间
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")
        
        # 根据消息类型设置不同的样式
        if is_user:
            # 用户消息 - 右侧
            message_html = f'''
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td width="30%"></td>
                    <td width="70%" align="right">
                        <div style="background: #95EC69; color: #000; padding: 10px 15px; 
                                    border-radius: 18px; border-bottom-right-radius: 5px; 
                                    max-width: 100%;">
                            <strong>{sender}</strong><br>{escaped_content}
                        </div>
                        <div style="font-size: 11px; color: #999; margin: 5px 8px;">
                            {timestamp}
                        </div>
                    </td>
                </tr>
            </table>
            '''
        else:
            # AI消息 - 左侧
            message_html = f'''
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td width="70%" align="left">
                        <div style="background: #FF0; color: #000; padding: 10px 15px; 
                                    border-radius: 18px; border-bottom-left-radius: 5px; 
                                    border: 1px solid #E5E5EA; max-width: 100%;">
                            <strong>{sender}</strong><br>{escaped_content}
                        </div>
                        <div style="font-size: 11px; color: #999; margin: 5px 8px;">
                            {timestamp}
                        </div>
                    </td>
                    <td width="30%"></td>
                </tr>
            </table>
            
            '''
        
        #<img style="width:20%; height:auto; max-width:160px; display:block; margin-top:130px;" src="expressions/{expression}.png">

        # 在现有内容后追加新消息
        cursor = self.ui.chatDisplay.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # 插入新消息
        cursor.insertHtml(message_html)
        
        # 添加换行以便后续消息可以正确插入
        cursor.insertBlock()
        
        # 滚动到底部
        self.ui.chatDisplay.moveCursor(QTextCursor.End)

    def send_message(self):
        """处理用户输入，调用LLM并联动Live2D"""
        user_input = self.ui.inputField.text().strip()

        # 如果存在待发送的文件，则要求必须有文本内容才发送
        if self.pending_file:
            if not user_input:
                # 提示用户先输入文本描述
                self.add_message_to_display("系统", "已选择文件，请在输入框填写描述后点击发送。", "", False)
                return

            # 清空输入框并记录用户消息（包含文件信息）
            self.ui.inputField.setText("")
            print(f"用户输入（附带文件）：{user_input}")
            self.add_message_to_display("你", f"{user_input} (附带文件)", "", True)

            # 异步处理图片分析请求，避免阻塞UI
            def _do_picture_analysis(file_path, user_text):
                try:
                    response = llm.picture_analysis(file_path, user_text)
                except Exception as e:
                    self.update_ui_signal.emit("系统", f"图片分析出错：{e}", "", False)
                    return

                pattern = r'【[^】]*】'
                pure_text = re.sub(pattern, '', response)
                expression = ""
                if pure_text != response:
                    try:
                        expression = response.split("【")[1][:2]
                    except Exception:
                        expression = ""
                # 在主线程显示AI回复
                self.update_ui_signal.emit("AI", pure_text, expression, False)
                live2d_api.send_json_message(pure_text)
                live2d_api.send_sound()

            threading.Thread(target=_do_picture_analysis, args=(self.pending_file, user_input), daemon=True).start()

            # 发送完成，清除 pending_file 和恢复占位提示
            self.pending_file = None
            self.ui.inputField.setPlaceholderText("")
            return

        # 普通文本消息处理（无文件）
        if not user_input:
            return
        self.ui.inputField.setText("")  # 清空输入框
        print(f"用户输入：{user_input}")
        
        self.add_message_to_display("你", user_input, "",True)

        # 调用LLM获取回复
        response = llm.chat(user_input)

        """表情传递规则：好吧【害羞】"""
        # 提取纯净text(日文无需)
        pattern = r'【[^】]*】'
        pure_text = re.sub(pattern, '', response)
        expression = ""
        if pure_text != response:
            try:
                expression = response.split("【")[1][:2]
                print("表情" + expression)
            except Exception:
                expression = ""
        # 无论是否有表情，都将 AI 回复显示到聊天框
        self.add_message_to_display("AI", pure_text, expression, False)
        
        # 发送回复到Live2D（文字+音频）
        live2d_api.send_json_message(pure_text)
        live2d_api.send_sound()
        live2d_api.send_motion(tools.tools.motion_id)
        
    #语音识别
    def handle_audio(self):         
        if audio_record.is_recording == 0:     # 未录制中，开始
            """用户按下按钮开始录音，并自动发送"""
            # 创建录音线程，避免阻塞UI
            self.ui.audioButton.setText("停止录音")
            self.record_thread = threading.Thread(
                target=self._record_and_process,
                daemon=True
            )
            self.record_thread.start()
        elif audio_record.is_recording == 1:    # 录制中，打断
            self.ui.audioButton.setText("开始录音")
            audio_record.is_recording = 0   # 置0，打断
            
    def _record_and_process(self):
        audio_record.record_audio("record.wav", 20)
        if audio_record.is_recording == 0:
            user_input = asr.audio_to_text()[0].get("text","")
            print("用户输入"+user_input)
            if user_input:
                # 通过信号通知主线程更新UI
                self.update_ui_signal.emit("你", user_input,"", True)
                
                # 调用LLM获取回复
                response = llm.chat(user_input)
                pattern = r'【[^】]*】'
                pure_text = re.sub(pattern, '', response)
                expression = ""
                if pure_text != response:
                    try:
                        expression = response.split("【")[1][:2]
                        print("表情" + expression)
                    except Exception:
                        expression = ""
                self.update_ui_signal.emit("AI", pure_text, expression, False)
                
            if not user_input:
                self.update_ui_signal.emit("AI", "未识别到语音内容，请重试","", False)
                return
            
    def toggle_realtime_chat(self):
        """切换实时对话状态"""
        if self.is_realtime_chat:
            self.stop_realtime_chat()
            self.ui.chatButton.setText("开始人机对话")
        else:
            self.start_realtime_chat()
            self.ui.chatButton.setText("停止人机对话")
    
    def start_realtime_chat(self):
        """开始实时对话模式"""
        self.is_realtime_chat = True
        self.add_message_to_display("系统", "开始实时对话模式，正在监听您的声音...", "", False)
        
        # 启动VAD监听线程
        self.listener_thread = threading.Thread(
            target=self.vad.start_listening,
            args=(self.process_realtime_speech,),
            daemon=True
        )
        self.listener_thread.start()
    
    def stop_realtime_chat(self):
        """停止实时对话模式"""
        self.is_realtime_chat = False
        self.vad.stop_listening()
        self.add_message_to_display("系统", "已停止实时对话模式", "", False)
    
    def process_realtime_speech(self, audio_path):
        """处理实时检测到的语音"""
        if self.is_ai_responding:
            return
            
        # 避免在AI响应时处理新语音
        self.is_ai_responding = True
        
        try:
            # 调用ASR识别语音
            user_input = asr.audio_to_text(audio_path)[0].get("text", "")
            
            if not user_input:
                self.update_ui_signal.emit("系统", "未识别到有效语音", "", False)
                self.is_ai_responding = False
                return
            
            # 显示用户输入
            self.update_ui_signal.emit("你", user_input, "", True)
            
            # 调用LLM获取回复
            response = llm.chat(user_input)
            
            # 提取表情
            pattern = r'【[^】]*】'
            pure_text = re.sub(pattern, '', response)
            expression = ""
            if pure_text != response:
                expression = response.split("【")[1][:2]
            
            # 显示AI回复
            self.update_ui_signal.emit("AI", pure_text, expression, False)
            
            # 发送到Live2D
            live2d_api.send_json_message(pure_text)
            live2d_api.send_sound()
            
        finally:
            # 无论成功失败都标记为可响应状态
            self.is_ai_responding = False

    def change_audio_language(self):
        cur_language = self.ui.languageBox.currentText()
        print(cur_language)
        config = ConfigLoader() 
        if cur_language=="日文":
            config.set("tts.text_lang","ja")
        elif cur_language=="中文":
            config.set("tts.text_lang","zh")
        elif cur_language=="英文":
            config.set("tts.text_lang","en")
        from config import config
            

    def handle_send_file(self):
        """打开文件选择对话框，选择图片后调用 vision.picture_analysis 并展示结果。"""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(self.ui, "选择图片文件", "", "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)")
        if not file_path:
            return

        # 保存为待发送文件，要求用户在输入框填写文本后再发送
        self.pending_file = file_path
        # 显示提示并提醒用户在输入框输入描述后发送
        self.add_message_to_display("系统", f"已选择文件: {file_path}。请在输入框填写描述后点击发送。", "", False)
        self.ui.inputField.setPlaceholderText("已选择文件，输入描述后点击发送以分析图片")
        self.ui.inputField.setFocus()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_gui = ChatGUI()
    chat_gui.ui.show()
    sys.exit(app.exec())  # 启动Qt事件循环