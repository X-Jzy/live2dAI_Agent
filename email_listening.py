import time
import threading
import imapclient
import pyzmail
from datetime import date
from PySide6.QtCore import Signal, QObject
import llm
from config import config  # 新增
import re

class EmailSignal(QObject):
    new_email = Signal(str, str,str, bool)  # 用于传递新邮件信息

# 实例化信号对象（供全局使用）
email_signal = EmailSignal()

# 全局集合，记录已处理的UID
PROCESSED_UIDS = set()

def get_data():
    global PROCESSED_UIDS
    # 从配置获取邮件参数
    email_config = config.get("email", {})
    imap_server = email_config.get("imap_server", "imap.qq.com")
    ssl = email_config.get("ssl", True)
    port = email_config.get("port", 993)
    username = email_config.get("username")
    password = email_config.get("password")
    folder = email_config.get("folder", "INBOX")

    if not username or not password:
        print("邮件配置不完整（缺少username或password）")
        return

    try:
        imap_object = imapclient.IMAPClient(imap_server, port=port, ssl=ssl)
        imap_object.login(username, password)
        imap_object.select_folder(folder, readonly=False)

        # 只查找今日所有未读邮件
        since_date = date.today().strftime('%d-%b-%Y')
        UIDs = imap_object.search(['SINCE', since_date, 'UNSEEN'])

        # 只处理未处理过的新邮件
        new_UIDs = [uid for uid in UIDs if uid not in PROCESSED_UIDS]
        #print(f"[INFO] 检测到 {len(new_UIDs)} 封新邮件：")
        for uid in new_UIDs:
            raw_message = imap_object.fetch(uid, ['BODY[]'])
            message_object = pyzmail.PyzMessage.factory(raw_message[uid][b'BODY[]'])
            if message_object.text_part:
                text = message_object.text_part.get_payload().decode(message_object.text_part.charset)
            elif message_object.html_part:
                html = message_object.html_part.get_payload().decode(message_object.html_part.charset)
                text = f"HTML内容: {html[:100]}..."
            else:
                text = "无正文内容"

            # 构建完整的邮件信息字符串
            email_info = f"有邮件发来，主题：{message_object.get_subject()}，发件人是：{str(message_object.get_addresses('from')[0][0])}。文本内容是：{text}"
            response = llm.chat(email_info, source="proactive")
            if response is None:
                print("[INFO] 邮件主动播报已跳过，等待用户对话完成")
                continue
            pattern = r'【[^】]*】'
            pure_text = re.sub(pattern, '', response)
            if pure_text != response:
                expression = response.split("【")[1][:2]
                print("表情"+expression)
            email_signal.new_email.emit("AI", pure_text,expression, False)
            
            # 标记为已读
            imap_object.add_flags(uid, [b'\\Seen'])
            PROCESSED_UIDS.add(uid)
        imap_object.logout()
    except Exception as e:
        print(f"邮件处理错误: {str(e)}")


def listen_email():
    # 从配置获取检查间隔
    check_interval = config.get("email.check_interval", 1)
    while True:
        get_data()
        time.sleep(check_interval)