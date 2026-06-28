# ==========================================
# 悠扬工具箱 (YoyangScript)
# 作者：冯凯颖 (2026)
# 本源码遵循 MIT 协议开源，使用请保留原作者版权声明。
# ==========================================
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 🆕 用户数据根目录（所有用户产生的文件都放这里）
USERDATA_DIR = os.path.join(BASE_DIR, 'userdata')

# 各子目录基于 USERDATA_DIR
SCRIPTS_DIR = os.path.join(USERDATA_DIR, 'scripts')
LOGS_DIR = os.path.join(USERDATA_DIR, 'logs')
DATA_DIR = os.path.join(USERDATA_DIR, 'data')          # 背景图等（可选统一）
BG_DIR = os.path.join(USERDATA_DIR, 'bg')               # 背景图片专用

MAX_UPLOAD_SIZE_MB = 50
SAFE_FILENAME_PATTERN = r'^[\w\-. \u4e00-\u9fff]+$'
HOST = '0.0.0.0'
PORT = 5000
DEBUG = False
AUTO_OPEN_BROWSER = True

VERSION = '2.0.0'

# 更新源配置：格式为 "平台/用户名/仓库名"
#   GitHub 示例: "github/fengkaiying/yoyangscript"
#   Gitee  示例: "gitee/fengkaiying/yoyangscript"
#   留空可禁用更新检测
UPDATE_SOURCE = 'github/youyang145/yoyangscript'

# 自动创建所有需要的目录
for d in [SCRIPTS_DIR, LOGS_DIR, DATA_DIR, BG_DIR]:
    os.makedirs(d, exist_ok=True)