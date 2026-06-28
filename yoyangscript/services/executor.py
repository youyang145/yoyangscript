"""
后台执行器：支持单实例覆盖（Windows / Linux / Termux 通用）
"""
import os, re, subprocess, threading, uuid, time, sys
from config import SCRIPTS_DIR, LOGS_DIR, SAFE_FILENAME_PATTERN

_running_scripts = {}

def _run_script_background(script_name, script_path, log_id):
    log_file = os.path.join(LOGS_DIR, f"{log_id}.log")
    # 用二进制模式写入头部，避免编码混用
    header = f"=== 启动: {script_path} ===\n=== 时间: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n"
    with open(log_file, 'wb') as f:
        f.write(header.encode('utf-8'))
    try:
        ext = os.path.splitext(script_name)[1].lower()
        if ext == '.py': cmd = [sys.executable, script_path]
        elif ext in ['.sh', '.bash', '.zsh']: cmd = ['bash', script_path]
        elif ext == '.pl': cmd = ['perl', script_path]
        elif ext == '.rb': cmd = ['ruby', script_path]
        elif ext == '.lua': cmd = ['lua', script_path]
        else: cmd = [script_path]
        # 强制子进程使用 UTF-8 输出，避免 Windows GBK 乱码
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=SCRIPTS_DIR,
            env=env
        )
        _running_scripts[script_name] = (proc, log_id)
        # 逐行读取，用 errors='replace' 处理非 UTF-8 字节，追加写入日志
        with open(log_file, 'ab') as f:
            for line in iter(proc.stdout.readline, b''):
                f.write(line)
        proc.wait()
    except Exception as e:
        with open(log_file, 'ab') as f:
            f.write(f"\n!!! 错误: {e}\n".encode('utf-8'))
    finally:
        if _running_scripts.get(script_name) and _running_scripts[script_name][1] == log_id:
            del _running_scripts[script_name]
        with open(log_file, 'ab') as f:
            f.write(f"\n=== 结束: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n".encode('utf-8'))

def run_script(script_name):
    if not re.match(SAFE_FILENAME_PATTERN, script_name):
        raise ValueError(f"非法脚本名: {script_name}")
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"脚本不存在: {script_name}")
    if script_name in _running_scripts:
        old_proc, _ = _running_scripts[script_name]
        try:
            old_proc.terminate()
            try: old_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                old_proc.kill()
                old_proc.wait()
        except: pass
        finally:
            if script_name in _running_scripts: del _running_scripts[script_name]
    log_id = uuid.uuid4().hex[:12]
    os.makedirs(LOGS_DIR, exist_ok=True)
    t = threading.Thread(target=_run_script_background, args=(script_name, script_path, log_id), daemon=True)
    t.start()
    return log_id

def get_log_content(log_id):
    log_file = os.path.join(LOGS_DIR, f"{log_id}.log")
    if not os.path.exists(log_file):
        raise FileNotFoundError("日志不存在")
    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def get_running_scripts():
    """返回当前正在运行的脚本名称列表"""
    return list(_running_scripts.keys())

def stop_all_scripts():
    """终止所有正在运行的脚本，返回被终止的脚本名列表"""
    stopped = []
    for name in list(_running_scripts.keys()):
        proc, _ = _running_scripts[name]
        try:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        except Exception:
            pass
        finally:
            if name in _running_scripts:
                del _running_scripts[name]
        stopped.append(name)
    return stopped