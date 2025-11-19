@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: B站热门视频趋势分析工具 - Windows一键部署脚本
:: Bilibili Hot Video Trend Analyzer - Windows Setup Script

title B站热门视频分析工具 - 部署脚本

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║        B站热门视频趋势分析工具 - 一键部署脚本               ║
echo ║        Bilibili Hot Video Analyzer - Setup Script           ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: 获取脚本所在目录
cd /d "%~dp0"
echo [INFO] 工作目录: %CD%
echo.

:: 检查Python
echo [INFO] 检查Python环境...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到Python，请先安装Python 3.8+
    echo        下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 获取Python版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python版本: %PYTHON_VERSION%

:: 检查版本号
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% lss 3 (
    echo [ERROR] Python版本过低，需要3.8+
    pause
    exit /b 1
)

if %MAJOR% equ 3 if %MINOR% lss 8 (
    echo [ERROR] Python版本过低，需要3.8+
    pause
    exit /b 1
)

:: 创建虚拟环境
echo.
echo [INFO] 创建虚拟环境...

if exist "venv" (
    echo [WARNING] 虚拟环境已存在，跳过创建
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo [SUCCESS] 虚拟环境创建成功
)

:: 激活虚拟环境
echo [INFO] 激活虚拟环境...
call venv\Scripts\activate.bat
echo [SUCCESS] 虚拟环境已激活

:: 升级pip
echo.
echo [INFO] 升级pip...
python -m pip install --upgrade pip -q
if %errorlevel% neq 0 (
    echo [WARNING] pip升级失败，继续安装依赖
)

:: 安装依赖
echo.
echo [INFO] 安装Python依赖...

if not exist "requirements.txt" (
    echo [ERROR] 未找到requirements.txt
    pause
    exit /b 1
)

pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [ERROR] 依赖安装失败
    echo [INFO] 尝试使用清华源安装...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple -q
    if %errorlevel% neq 0 (
        echo [ERROR] 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
)
echo [SUCCESS] Python依赖安装完成

:: 创建输出目录
echo.
echo [INFO] 创建输出目录...
if not exist "output" mkdir output
echo [SUCCESS] 输出目录创建完成

:: 测试API连接
echo.
echo [INFO] 测试B站API连接...
python -c "import requests; r = requests.get('https://api.bilibili.com/x/web-interface/popular?ps=1&pn=1', headers={'User-Agent': 'Mozilla/5.0'}, timeout=10); print('[SUCCESS] API连接成功' if r.json()['code'] == 0 else '[WARNING] API返回异常')" 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] API连接测试失败，请检查网络
)

:: 显示使用说明
echo.
echo ════════════════════════════════════════════════════════════════
echo.
echo [SUCCESS] 部署完成！
echo.
echo 使用方法:
echo.
echo   1. 激活虚拟环境:
echo      venv\Scripts\activate
echo.
echo   2. 运行命令行分析:
echo      python bilibili_analyzer.py -p 5
echo.
echo   3. 启动Web界面:
echo      python web_app.py
echo      然后访问 http://localhost:5000
echo.
echo   4. 更多选项:
echo      python bilibili_analyzer.py --help
echo.
echo ════════════════════════════════════════════════════════════════
echo.

:: 快速启动菜单
:menu
echo 是否现在启动程序？
echo.
echo   1) 启动Web界面 (推荐)
echo   2) 运行命令行分析
echo   3) 退出
echo.
set /p choice="请选择 [1-3]: "

if "%choice%"=="1" (
    echo.
    echo [INFO] 启动Web界面...
    echo [INFO] 请在浏览器中访问 http://localhost:5000
    echo.
    python web_app.py
    goto end
)

if "%choice%"=="2" (
    echo.
    echo [INFO] 运行命令行分析...
    echo.
    python bilibili_analyzer.py -p 3
    goto end
)

if "%choice%"=="3" (
    echo.
    echo [INFO] 退出部署脚本
    goto end
)

echo [WARNING] 无效选择，请重新选择
echo.
goto menu

:end
echo.
pause
