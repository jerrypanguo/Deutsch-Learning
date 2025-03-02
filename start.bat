@echo off
REM 德语学习助手Windows启动脚本

REM 检查虚拟环境是否存在
if not exist venv (
    echo 正在设置环境，请稍等...
    python setup.py
    if errorlevel 1 (
        echo 环境设置失败，请查看错误信息。
        pause
        exit /b 1
    )
)

REM 激活虚拟环境并运行程序
call venv\Scripts\activate.bat
python deutsch_cli.py

REM 退出虚拟环境
call deactivate
pause 