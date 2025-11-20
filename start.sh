#!/bin/bash

# B站热门视频分析工具 - 一键启动脚本 (Linux/macOS)

echo "=========================================="
echo "  B站热门视频趋势分析工具"
echo "=========================================="
echo ""

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 错误: 虚拟环境不存在!"
    echo "请先运行 ./setup.sh 进行初始化"
    exit 1
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 检查激活是否成功
if [ $? -ne 0 ]; then
    echo "❌ 虚拟环境激活失败!"
    exit 1
fi

echo "✅ 虚拟环境已激活"
echo ""

# 启动Web应用
echo "🚀 启动Web应用..."
echo "访问地址: http://localhost:5000"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "=========================================="
echo ""

python web_app.py
