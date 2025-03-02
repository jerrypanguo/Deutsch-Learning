#!/bin/bash

# 德语学习助手 - Mac安装脚本

echo -e "\033[1;34m===== 德语学习助手 Mac安装程序 =====\033[0m"

# 检查Python版本
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
required_major=3
required_minor=8

echo -e "\033[1;36m检查Python版本...\033[0m"
major=$(echo $python_version | cut -d. -f1)
minor=$(echo $python_version | cut -d. -f2)

if [ "$major" -lt "$required_major" ] || ([ "$major" -eq "$required_major" ] && [ "$minor" -lt "$required_minor" ]); then
    echo -e "\033[1;31m错误: 需要Python 3.8或更高版本，当前版本为$python_version\033[0m"
    exit 1
fi
echo -e "\033[1;32mPython版本检查通过: $python_version\033[0m"

# 创建虚拟环境
echo -e "\033[1;36m创建虚拟环境...\033[0m"
if [ -d "venv" ]; then
    echo -e "\033[1;33m虚拟环境已存在，跳过创建步骤。\033[0m"
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "\033[1;31m创建虚拟环境失败\033[0m"
        exit 1
    fi
    echo -e "\033[1;32m虚拟环境创建成功！\033[0m"
fi

# 激活虚拟环境
source venv/bin/activate

# 升级pip
echo -e "\033[1;36m升级pip...\033[0m"
pip install --upgrade pip

# 安装依赖包 - 为Mac版本特别定制的安装方式
echo -e "\033[1;36m安装依赖包...\033[0m"

# 首先安装基本依赖
echo "安装基本依赖..."
pip install deep-translator spacy python-dotenv gtts pydub colorama click rich requests

# 安装德语spaCy模型
echo "安装德语spaCy模型..."
pip install https://github.com/explosion/spacy-models/releases/download/de_core_news_sm-3.5.0/de_core_news_sm-3.5.0.tar.gz

# 安装特定包
echo "安装language-tool-python..."
pip install language-tool-python

# 安装音频播放依赖
echo "安装音频播放依赖..."
pip install simpleaudio || echo -e "\033[1;33m注意: simpleaudio安装失败，将使用系统命令播放音频\033[0m"

# 检查安装结果
if [ $? -eq 0 ]; then
    echo -e "\033[1;32m依赖包安装成功！\033[0m"
else
    echo -e "\033[1;33m部分依赖安装可能有问题，但程序应该能够运行。\033[0m"
fi

# 停用虚拟环境
deactivate

echo -e "\033[1;32m\n===== 安装完成！=====\033[0m"
echo -e "\033[1;36m\n使用方法：\033[0m"
echo -e "\033[1;33m1. 运行程序：\033[0m"
echo -e "\033[1;32m   ./start.sh\033[0m"
echo -e "\033[1;33m\n如果遇到运行权限问题，请执行：\033[0m"
echo -e "\033[1;32m   chmod +x start.sh deutsch_cli.py\033[0m"
echo -e "\033[1;36m\n祝您学习愉快！Viel Spaß beim Deutschlernen!\033[0m" 