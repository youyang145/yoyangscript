# ==========================================
# 悠扬工具箱 (YoyangScript)
# 作者：冯凯颖 (2026)
# 本源码遵循 MIT 协议开源，使用请保留原作者版权声明。
# ==========================================
"""
==========================================================================
 app.py - YoyangScript 应用入口
==========================================================================
"""
from flask import Flask
from routes.main_routes import main_bp
from routes.execute_routes import exec_bp
from routes.data_routes import data_bp

app = Flask(__name__)
from config import MAX_UPLOAD_SIZE_MB
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE_MB * 1024 * 1024

app.register_blueprint(main_bp)
app.register_blueprint(exec_bp)
app.register_blueprint(data_bp)

if __name__ == '__main__':
    from config import HOST, PORT, DEBUG
    print(f"YoyangScript 启动中... 访问 http://localhost:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)