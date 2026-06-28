from flask import Blueprint, render_template, jsonify, request
from services.script_manager import get_script_list, save_script_file, delete_script_file

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/list_scripts')
def list_scripts():
    try:
        scripts = get_script_list()
        return jsonify({'scripts': scripts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/upload_script', methods=['POST'])
def upload_script():
    if 'script_file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400
    file = request.files['script_file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    try:
        name = save_script_file(file)
        import os
        from config import SCRIPTS_DIR
        size = os.path.getsize(os.path.join(SCRIPTS_DIR, name))
        return jsonify({'success': True, 'name': name, 'size': size})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'保存失败: {str(e)}'}), 500

@main_bp.route('/delete_script', methods=['POST'])
def delete_script():
    data = request.get_json()
    if not data or 'script' not in data:
        return jsonify({'error': '缺少脚本名'}), 400
    name = data['script']
    try:
        delete_script_file(name)
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500