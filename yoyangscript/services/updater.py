"""
版本检测与更新模块
支持：GitHub Releases / Gitee Releases / 自定义 URL
跨平台（Windows / Linux / Termux / macOS）

自动更新流程：
  1. 下载 GitHub Release 的 zip 包
  2. 解压到临时目录
  3. 只覆盖程序文件，保护 userdata/、config.py、__pycache__/
  4. 用户重启后生效
"""
import json
import urllib.request
import re
import time
import os
import sys
import shutil
import zipfile
import tempfile
from config import VERSION, UPDATE_SOURCE, BASE_DIR

# 更新时保护的文件/目录（不会覆盖）
_PROTECTED_PATHS = {
    "userdata",       # 用户数据（脚本、日志、背景）
    "config.py",      # 用户配置
    "__pycache__",    # Python 缓存
    ".git",           # Git 仓库
    ".claude",        # Claude 配置
}

# 缓存：避免频繁请求
_cache = {"data": None, "time": 0}
_CACHE_TTL = 600  # 10 分钟内不重复请求


def _parse_version(ver: str) -> tuple:
    """解析语义化版本号，返回可比较的元组，如 'v2.1.0' → (2, 1, 0)"""
    v = ver.lstrip("v").strip()
    parts = re.split(r"[.\-]", v)
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            result.append(0)
    while len(result) < 3:
        result.append(0)
    return tuple(result[:3])


def _is_newer(latest: str, current: str) -> bool:
    """latest 版本是否比 current 更新"""
    return _parse_version(latest) > _parse_version(current)


def _fetch_github(owner: str, repo: str) -> dict | None:
    """从 GitHub Releases API 获取最新版本信息"""
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "YoyangScript-Updater")

    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            # 检查限流
            remaining = resp.headers.get("X-RateLimit-Remaining")
            if remaining is not None and int(remaining) < 5:
                reset_time = int(resp.headers.get("X-RateLimit-Reset", 0))
                wait_min = max(1, (reset_time - int(time.time())) // 60 + 1)
                print(f"[updater] GitHub API 限流，需等待 {wait_min} 分钟")
                return {
                    "error": f"GitHub API 请求次数用尽，约 {wait_min} 分钟后恢复",
                    "rate_limited": True,
                }
            data = json.loads(resp.read().decode())
            return {
                "version": data.get("tag_name", "0.0.0").lstrip("v"),
                "changelog": data.get("body", ""),
                "download_url": data.get("html_url", ""),
                "published_at": data.get("published_at", ""),
            }
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print("[updater] GitHub API 403 (可能是限流)")
            return {"error": "GitHub API 访问被拒（限流或网络问题），请稍后重试"}
        elif e.code == 404:
            print("[updater] 仓库或 Release 不存在 (404)")
            return {"error": "未找到 Release，请先在 GitHub 上创建 Release"}
        print(f"[updater] GitHub 请求失败: HTTP {e.code}")
        return {"error": f"GitHub 请求失败 (HTTP {e.code})"}
    except urllib.error.URLError as e:
        print(f"[updater] 网络连接失败: {e.reason}")
        return {"error": f"网络不可达: {e.reason}"}
    except Exception as e:
        print(f"[updater] GitHub 请求异常: {e}")
        return {"error": f"请求异常: {e}"}


def _fetch_gitee(owner: str, repo: str) -> dict | None:
    """从 Gitee Releases API 获取最新版本信息"""
    url = f"https://gitee.com/api/v5/repos/{owner}/{repo}/releases/latest"
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            return {
                "version": data.get("tag_name", "0.0.0").lstrip("v"),
                "changelog": data.get("body", ""),
                "download_url": data.get("html_url", ""),
                "published_at": data.get("created_at", ""),
            }
    except Exception as e:
        print(f"[updater] Gitee 请求失败: {e}")
        return None


def check_for_update(force: bool = False) -> dict:
    """
    检查是否有新版本。

    参数:
        force: 强制刷新，忽略缓存

    返回:
        {
            has_update: bool,
            current_version: str,
            latest_version: str | None,
            changelog: str,
            download_url: str,
            published_at: str,
            cached: bool,
        }
    """
    # 检查缓存
    now = time.time()
    if not force and _cache["data"] and (now - _cache["time"]) < _CACHE_TTL:
        cached = _cache["data"].copy()
        cached["cached"] = True
        return cached

    # 解析仓库配置
    try:
        source_type, owner, repo = UPDATE_SOURCE.split("/", 2)
    except ValueError:
        return {
            "has_update": False,
            "current_version": VERSION,
            "latest_version": None,
            "changelog": "",
            "download_url": "",
            "published_at": "",
            "cached": False,
            "error": "UPDATE_SOURCE 配置格式错误，应为 github/owner/repo 或 gitee/owner/repo",
        }

    # 获取远端版本
    if source_type == "gitee":
        remote = _fetch_gitee(owner, repo)
    else:
        remote = _fetch_github(owner, repo)

    if not remote:
        return {
            "has_update": False,
            "current_version": VERSION,
            "latest_version": None,
            "changelog": "",
            "download_url": "",
            "published_at": "",
            "cached": False,
            "error": "无法获取远端版本信息",
        }

    # 远端返回了错误（如限流、404）
    if "error" in remote:
        return {
            "has_update": False,
            "current_version": VERSION,
            "latest_version": None,
            "changelog": "",
            "download_url": "",
            "published_at": "",
            "cached": False,
            "error": remote["error"],
        }

    latest = remote["version"]
    result = {
        "has_update": _is_newer(latest, VERSION),
        "current_version": VERSION,
        "latest_version": latest,
        "changelog": remote.get("changelog", ""),
        "download_url": remote.get("download_url", ""),
        "published_at": remote.get("published_at", ""),
        "cached": False,
    }

    # 写入缓存
    _cache["data"] = result.copy()
    _cache["time"] = now

    return result


def get_current_version() -> dict:
    """返回当前版本信息（供 UI 展示）"""
    return {
        "version": VERSION,
        "update_source": UPDATE_SOURCE,
    }


def _get_zip_download_url() -> str | None:
    """获取 Release 的 zip 包下载地址"""
    try:
        source_type, owner, repo = UPDATE_SOURCE.split("/", 2)
    except ValueError:
        return None

    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "YoyangScript-Updater")
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            # 优先取上传的 asset，否则用源码 zip
            assets = data.get("assets", [])
            if assets:
                return assets[0].get("browser_download_url")
            return data.get("zipball_url")
    except Exception as e:
        print(f"[updater] 获取下载地址失败: {e}")
        return None


def _should_skip(rel_path: str) -> bool:
    """判断某个相对路径是否应该被保护（不覆盖）"""
    parts = rel_path.replace("\\", "/").split("/")
    for part in parts:
        if part in _PROTECTED_PATHS:
            return True
    return False


def do_update() -> dict:
    """
    执行自动更新：
        1. 下载最新 Release zip
        2. 解压到临时目录
        3. 覆盖程序文件（保护 userdata/、config.py）
        4. 清理临时文件

    返回:
        { success: bool, message: str, updated_files: int, new_version: str }
    """
    # 1. 获取下载地址
    zip_url = _get_zip_download_url()
    if not zip_url:
        return {"success": False, "message": "无法获取更新包下载地址"}

    print(f"[updater] 下载: {zip_url}")

    # 2. 下载 zip
    tmp_dir = tempfile.mkdtemp(prefix="yoyang_update_")
    zip_path = os.path.join(tmp_dir, "update.zip")
    try:
        req = urllib.request.Request(zip_url)
        req.add_header("User-Agent", "YoyangScript-Updater")
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(zip_path, "wb") as f:
                f.write(resp.read())
        print(f"[updater] 下载完成: {os.path.getsize(zip_path)} bytes")
    except Exception as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return {"success": False, "message": f"下载失败: {e}"}

    # 3. 解压
    extract_dir = os.path.join(tmp_dir, "extracted")
    os.makedirs(extract_dir, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
    except Exception as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return {"success": False, "message": f"解压失败: {e}"}

    # 4. 找到源码根目录（GitHub zip 会有一层包装目录）
    entries = os.listdir(extract_dir)
    source_root = extract_dir
    if len(entries) == 1:
        single = os.path.join(extract_dir, entries[0])
        if os.path.isdir(single):
            source_root = single

    # 5. 拷贝文件（保护 userdata/、config.py）
    updated = 0
    errors = []
    for dirpath, dirnames, filenames in os.walk(source_root):
        # 跳过受保护的目录
        dirnames[:] = [d for d in dirnames if not _should_skip(
            os.path.relpath(os.path.join(dirpath, d), source_root)
        )]

        for filename in filenames:
            src = os.path.join(dirpath, filename)
            rel = os.path.relpath(src, source_root)

            # 跳过受保护的文件
            if _should_skip(rel):
                continue

            dst = os.path.join(BASE_DIR, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            try:
                shutil.copy2(src, dst)
                updated += 1
            except Exception as e:
                errors.append(f"{rel}: {e}")

    # 6. 清理临时目录
    shutil.rmtree(tmp_dir, ignore_errors=True)

    if errors:
        return {
            "success": True,
            "message": f"更新完成（{len(errors)} 个文件失败）",
            "updated_files": updated,
            "errors": errors[:10],
        }
    return {
        "success": True,
        "message": f"已更新 {updated} 个文件，重启后生效",
        "updated_files": updated,
    }
