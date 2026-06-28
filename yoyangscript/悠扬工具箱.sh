#!/bin/bash
echo "========================================"
echo "   悠扬工具箱 - YoyangScript 启动器"
echo "========================================"
echo
if ! command -v python3 &>/dev/null; then
    echo "[错误] 未找到 Python3！请安装 Python 3.7+。"
    read -p "按 Enter 键退出..."
    exit 1
fi
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[提示] 缺少 Flask 库，运行需要安装。"
    read -p "是否现在安装 Flask？(y/N): " choice
    choice=${choice:-N}
    if [[ "$choice" =~ ^[Yy]$ ]]; then
        echo "正在安装 Flask..."
        python3 -m pip install flask
        if [ $? -ne 0 ]; then
            echo "[错误] 安装失败，请手动执行：python3 -m pip install flask"
            read -p "按 Enter 键退出..."
            exit 1
        fi
        echo "安装成功！"
    else
        echo "[取消] 未安装 Flask，程序无法继续。"
        echo "请手动执行：python3 -m pip install flask"
        read -p "按 Enter 键退出..."
        exit 1
    fi
fi
echo "依赖检查通过。"
echo "启动 YoyangScript 服务器..."
python3 start.py