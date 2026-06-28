"""
数据管理路由：背景图片的上传、获取、设置，版本更新检测
"""
import os, uuid, re, time, shutil
from flask import Blueprint, request, jsonify, send_from_directory
from config import BG_DIR
from services.updater import check_for_update, do_update

data_bp = Blueprint('data', __name__, url_prefix='/api')
_current_bg = None
_bg_last_modified = 0

def _safe_bg_filename(filename):
    return re.match(r'^[\w\-. ]+\.(png|jpg|jpeg|gif|webp)$', filename, re.IGNORECASE)

@data_bp.route('/get-background')
def get_background():
    if _current_bg:
        return jsonify({'bg_url': f'/api/bg-image/{_current_bg}'})
    return jsonify({'bg_url': None})

@data_bp.route('/bg-last-modified')
def bg_last_modified():
    return jsonify({'last_modified': _bg_last_modified})

@data_bp.route('/set-background', methods=['POST'])
def set_background():
    if 'bg_file' not in request.files:
        return jsonify({'error': '没有图片文件'}), 400
    file = request.files['bg_file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    if not _safe_bg_filename(file.filename):
        return jsonify({'error': '不支持的图片格式，仅允许 png/jpg/gif/webp'}), 400

    # 清空整个背景图片目录，确保只有一张背景
    if os.path.exists(BG_DIR):
        shutil.rmtree(BG_DIR)
        os.makedirs(BG_DIR, exist_ok=True)

    ext = file.filename.rsplit('.', 1)[1].lower()
    new_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(BG_DIR, new_name)
    file.save(save_path)

    global _current_bg, _bg_last_modified
    _current_bg = new_name
    _bg_last_modified = time.time()
    return jsonify({'success': True, 'bg_url': f'/api/bg-image/{new_name}'})

@data_bp.route('/bg-image/<filename>')
def serve_bg_image(filename):
    response = send_from_directory(BG_DIR, filename)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@data_bp.route('/check-update')
def check_update():
    force = request.args.get('force', '0') == '1'
    info = check_for_update(force=force)
    return jsonify(info)


@data_bp.route('/version')
def current_version():
    """返回当前版本信息"""
    from services.updater import get_current_version
    return jsonify(get_current_version())


@data_bp.route('/apply-update', methods=['POST'])
def apply_update():
    """执行自动更新：下载、解压、覆盖程序文件"""
    import threading
    result = {"success": False, "message": "更新已启动"}

    def _run():
        global _update_result
        _update_result = do_update()

    _update_result = None
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=120)  # 最多等 2 分钟

    if _update_result:
        return jsonify(_update_result)
    return jsonify({"success": False, "message": "更新超时，请重试"})