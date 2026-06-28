#!/usr/bin/env python3
# ==========================================
# 悠扬工具箱 (YoyangScript)
# 作者：冯凯颖 (2026)
# 本源码遵循 MIT 协议开源，使用请保留原作者版权声明。
# ==========================================
"""
悠扬工具箱启动核心
"""
import os, sys, webbrowser, threading, time, subprocess

os.chdir(os.path.dirname(os.path.abspath(__file__)))
from config import HOST, PORT, DEBUG, AUTO_OPEN_BROWSER

def open_browser():
    time.sleep(2)
    url = f"http://localhost:{PORT}"
    try:
        if os.path.exists('/data/data/com.termux/files/home'):
            subprocess.run(['termux-open-url', url], check=True)
        else:
            webbrowser.open(url)
        print(f"✅ 已打开浏览器访问 {url}")
    except Exception as e:
        print(f"⚠️ 自动打开浏览器失败: {e}")
        print(f"请手动打开 {url}")

print(f"🚀 正在启动 YoyangScript... 浏览器访问 http://localhost:{PORT}")
if AUTO_OPEN_BROWSER:
    threading.Thread(target=open_browser, daemon=True).start()

import app
app.app.run(host=HOST, port=PORT, debug=DEBUG)