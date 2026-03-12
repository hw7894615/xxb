@echo off
chcp 65001 >nul
cd /d "D:\git_xxb\xxb\mayilian"

echo ========================================
echo 蚂蚁链存证系统(企业版) 启动脚本
echo ========================================
echo.

REM 检查虚拟环境是否存在
if not exist ".venv\Scripts\activate.bat" (
    echo [错误] 虚拟环境不存在！
    echo 请先创建虚拟环境：
    echo   python -m venv .venv
    echo.
    pause
    exit /b 1
)

REM 检查Python文件是否存在
if not exist "app_new_enterprise.py" (
    echo [错误] 应用文件不存在：app_new_enterprise.py
    echo 请确保在正确的目录下运行此脚本
    echo.
    pause
    exit /b 1
)

REM 激活虚拟环境
echo [1/3] 激活虚拟环境...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 激活虚拟环境失败！
    echo.
    pause
    exit /b 1
)
echo [完成] 虚拟环境已激活
echo.

REM 检查必要的依赖
echo [2/3] 检查依赖...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [警告] Flask 未安装，正在安装...
    pip install flask flask-sqlalchemy
    if errorlevel 1 (
        echo [错误] 安装依赖失败！
        echo.
        pause
        exit /b 1
    )
)

python -c "import antchain_sdk_twc" 2>nul
if errorlevel 1 (
    echo [警告] 蚂蚁链SDK未安装，正在安装...
    pip install antchain_sdk_twc
    if errorlevel 1 (
        echo [错误] 安装蚂蚁链SDK失败！
        echo 请手动安装：pip install antchain_sdk_twc
        echo.
        pause
        exit /b 1
    )
)
echo [完成] 依赖检查通过
echo.

REM 创建上传目录
if not exist "uploads" (
    mkdir uploads
    echo [信息] 已创建上传目录
)

REM 启动应用
echo [3/3] 启动应用...
echo.
echo ========================================
echo 应用启动成功！
echo ========================================
echo 访问地址：
echo   - 本地访问：http://127.0.0.1:5002
echo   - 局域网访问：http://10.99.52.51:5002
echo.
echo 按 Ctrl+C 停止应用
echo ========================================
echo.

python app_new_enterprise.py

if errorlevel 1 (
    echo.
    echo [错误] 应用运行失败！
    echo 请检查错误信息并重试
    echo.
    pause
)

echo.
echo 应用已停止
pause
