#!/bin/bash

# 德语学习助手启动脚本

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "正在设置环境，请稍等..."
    python setup.py
    if [ $? -ne 0 ]; then
        echo "环境设置失败，请查看错误信息。"
        exit 1
    fi
fi

# 激活虚拟环境并运行程序
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows环境
    source venv/Scripts/activate
else
    # Unix/Linux/MacOS环境
    source venv/bin/activate
fi

# 运行程序
python deutsch_cli.py

# 退出虚拟环境
deactivate 