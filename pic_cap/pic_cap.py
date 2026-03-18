import base64
import mimetypes
import os

import numpy as np
from PIL import ImageGrab, Image
import cv2
from . import pic_resize

import tkinter as tk

def pic_cap():
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    img = ImageGrab.grab(bbox=(0, 0,screen_width, screen_height))  # bbox 定义左、上、右和下像素的4元组
    print(img.size[1], img.size[0])
    img = np.array(img.getdata(), np.uint8).reshape(img.size[1], img.size[0], 3)
    print("屏幕获取成功!")
    img=cv2.cvtColor(img,cv2.COLOR_RGB2BGR)
    cv2.imwrite('screenshot1.jpg', img)

    # 截图压缩，节省token，视情况使用
    pic_size = pic_resize.pic_compress('screenshot1.jpg', 'screenshot1.jpg', target_size=200)
    print("图片压缩后的大小为(KB)：", pic_size)

    if os.path.exists("screenshot1.jpg"):
        mime = mimetypes.guess_type("screenshot1.jpg")[0] or "image/png"
        with open("screenshot1.jpg", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        # 使用 data URI 字符串，API 要求 image_url.url 是字符串
        image_repr = f"data:{mime};base64,{b64}"
    else:
        image_repr = "screenshot1.jpg"

    return image_repr

# img = Image.fromarray(img)
# img.save('screenshot1.jpg')