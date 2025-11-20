@echo off
chcp 65001 >nul
setlocal

REM B站热门视频分析工具 - 一键启动脚本 (Windows)

echo ==========================================
echo   B站热门视频趋势分析工具
echo ==========================================
echo.

REM 检查虚拟环境是否存在
if not exist "venv\" (
    echo ❌ 错误: 虚拟环境不存在!
    echo 请先运行 setup.bat 进行初始化
    pause
    exit /b 1
)

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo ❌ 虚拟环境激活失败!
    pause
    exit /b 1
)

echo ✅ 虚拟环境已激活
echo.

REM 启动Web应用
echo 🚀 启动Web应用...
echo 访问地址: http://localhost:5000
echo.
echo 按 Ctrl+C 停止服务器
echo ==========================================
echo.

python web_app.py

REM 如果Python崩溃则暂停查看错误
if errorlevel 1 (
    echo.
    echo ❌ 应用启动失败!
    pause
)

endlocal
