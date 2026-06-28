from flask import Blueprint, jsonify, request
from services.executor import run_script, get_log_content, get_running_scripts, stop_all_scripts

exec_bp = Blueprint('execute', __name__)

@exec_bp.route('/run_script', methods=['POST'])
def run_script_route():
    data = request.get_json()
    if not data or 'script' not in data:
        return jsonify({'error': '缺少脚本名'}), 400
    name = data['script']
    try:
        log_id = run_script(name)
        return jsonify({
            'started': True,
            'log_id': log_id,
            'view_url': f'/view_log/{log_id}'
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@exec_bp.route('/view_log/<log_id>')
def view_log(log_id):
    try:
        content = get_log_content(log_id)
    except FileNotFoundError:
        return "日志不存在", 404
    html = f"""\
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="2">
    <title>日志 {log_id}</title>
    <style>
        body {{ background:#0a0a1a; color:#0f0; font-family:monospace; padding:20px; white-space:pre-wrap; }}
    </style>
</head>
<body>{content}</body>
</html>"""
    return html

@exec_bp.route('/script_output')
def script_output():
    log_id = request.args.get('log_id')
    if not log_id:
        return jsonify({'error': '缺少 log_id'}), 400
    try:
        content = get_log_content(log_id)
        return jsonify({'output': content})
    except FileNotFoundError:
        return jsonify({'error': '日志不存在'}), 404

@exec_bp.route('/running_scripts')
def running_scripts():
    return jsonify({'scripts': get_running_scripts()})

@exec_bp.route('/stop_all_scripts', methods=['POST'])
def stop_all():
    stopped = stop_all_scripts()
    return jsonify({'stopped': len(stopped), 'scripts': stopped})