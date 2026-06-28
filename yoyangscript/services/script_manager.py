import os, re
from config import SCRIPTS_DIR, SAFE_FILENAME_PATTERN

def is_safe_filename(name: str) -> bool:
    return bool(re.match(SAFE_FILENAME_PATTERN, name))

def get_script_list() -> list:
    files = []
    try:
        os.makedirs(SCRIPTS_DIR, exist_ok=True)
        for f in os.listdir(SCRIPTS_DIR):
            full_path = os.path.join(SCRIPTS_DIR, f)
            if os.path.isfile(full_path):
                files.append({
                    'name': f,
                    'size': os.path.getsize(full_path),
                    'mtime': os.path.getmtime(full_path)
                })
    except Exception as e:
        print(f"[script_manager] 读取失败: {e}")
    files.sort(key=lambda x: x['mtime'], reverse=True)
    return files

def save_script_file(file) -> str:
    filename = file.filename
    if not is_safe_filename(filename):
        raise ValueError(f"非法文件名: {filename}")
    save_path = os.path.join(SCRIPTS_DIR, filename)
    file.save(save_path)
    try:
        os.chmod(save_path, 0o755)
    except (OSError, NotImplementedError):
        pass  # Windows 不支持 POSIX 权限，忽略
    return filename

def delete_script_file(name: str) -> None:
    if not is_safe_filename(name):
        raise ValueError(f"非法文件名: {name}")
    file_path = os.path.join(SCRIPTS_DIR, name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"脚本不存在: {name}")
    os.remove(file_path)