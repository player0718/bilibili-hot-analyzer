#!/bin/bash
# B站热门视频趋势分析工具 - 一键部署脚本
# Bilibili Hot Video Trend Analyzer - Setup Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 打印横幅
print_banner() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║        B站热门视频趋势分析工具 - 一键部署脚本               ║"
    echo "║        Bilibili Hot Video Analyzer - Setup Script           ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查Python版本
check_python() {
    print_info "检查Python环境..."

    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "未找到Python，请先安装Python 3.8+"
        exit 1
    fi

    # 检查版本
    PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    MAJOR_VERSION=$($PYTHON_CMD -c 'import sys; print(sys.version_info[0])')
    MINOR_VERSION=$($PYTHON_CMD -c 'import sys; print(sys.version_info[1])')

    if [ "$MAJOR_VERSION" -lt 3 ] || ([ "$MAJOR_VERSION" -eq 3 ] && [ "$MINOR_VERSION" -lt 8 ]); then
        print_error "Python版本过低: $PYTHON_VERSION，需要3.8+"
        exit 1
    fi

    print_success "Python版本: $PYTHON_VERSION"
}

# 创建虚拟环境
create_venv() {
    print_info "创建虚拟环境..."

    if [ -d "venv" ]; then
        print_warning "虚拟环境已存在，跳过创建"
    else
        $PYTHON_CMD -m venv venv
        print_success "虚拟环境创建成功"
    fi

    # 激活虚拟环境
    source venv/bin/activate
    print_success "虚拟环境已激活"
}

# 安装依赖
install_dependencies() {
    print_info "安装Python依赖..."

    # 升级pip
    pip install --upgrade pip -q

    # 安装依赖
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt -q
        print_success "Python依赖安装完成"
    else
        print_error "未找到requirements.txt"
        exit 1
    fi
}

# 安装中文字体 (Linux)
install_fonts() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_info "检查中文字体..."

        # 检查是否已安装字体
        if fc-list :lang=zh 2>/dev/null | grep -q "."; then
            print_success "中文字体已安装"
        else
            print_warning "未检测到中文字体，尝试安装..."

            # 检测包管理器
            if command_exists apt-get; then
                sudo apt-get update -qq
                sudo apt-get install -y fonts-wqy-microhei fonts-wqy-zenhei -qq
                print_success "中文字体安装完成 (apt)"
            elif command_exists yum; then
                sudo yum install -y wqy-microhei-fonts wqy-zenhei-fonts -q
                print_success "中文字体安装完成 (yum)"
            elif command_exists dnf; then
                sudo dnf install -y wqy-microhei-fonts wqy-zenhei-fonts -q
                print_success "中文字体安装完成 (dnf)"
            elif command_exists pacman; then
                sudo pacman -S --noconfirm wqy-microhei wqy-zenhei
                print_success "中文字体安装完成 (pacman)"
            else
                print_warning "无法自动安装字体，请手动安装中文字体"
            fi
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_info "macOS系统自带中文字体，跳过安装"
    fi
}

# 创建输出目录
create_directories() {
    print_info "创建输出目录..."

    mkdir -p output
    print_success "输出目录创建完成"
}

# 测试API连接
test_api() {
    print_info "测试B站API连接..."

    $PYTHON_CMD -c "
import requests
try:
    r = requests.get('https://api.bilibili.com/x/web-interface/popular?ps=1&pn=1',
                     headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
    if r.json()['code'] == 0:
        print('API连接成功')
    else:
        print('API返回异常')
except Exception as e:
    print(f'API连接失败: {e}')
"
}

# 显示使用说明
show_usage() {
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    print_success "部署完成！"
    echo ""
    echo "使用方法:"
    echo ""
    echo "  1. 激活虚拟环境:"
    echo "     source venv/bin/activate"
    echo ""
    echo "  2. 运行命令行分析:"
    echo "     python bilibili_analyzer.py -p 5"
    echo ""
    echo "  3. 启动Web界面:"
    echo "     python web_app.py"
    echo "     然后访问 http://localhost:5000"
    echo ""
    echo "  4. 更多选项:"
    echo "     python bilibili_analyzer.py --help"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo ""
}

# 快速启动菜单
quick_start_menu() {
    echo ""
    echo "是否现在启动程序？"
    echo ""
    echo "  1) 启动Web界面 (推荐)"
    echo "  2) 运行命令行分析"
    echo "  3) 退出"
    echo ""
    read -p "请选择 [1-3]: " choice

    case $choice in
        1)
            print_info "启动Web界面..."
            echo ""
            $PYTHON_CMD web_app.py
            ;;
        2)
            print_info "运行命令行分析..."
            echo ""
            $PYTHON_CMD bilibili_analyzer.py -p 3
            ;;
        3)
            print_info "退出部署脚本"
            ;;
        *)
            print_warning "无效选择，退出"
            ;;
    esac
}

# 主函数
main() {
    print_banner

    # 获取脚本所在目录
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR"

    print_info "工作目录: $SCRIPT_DIR"
    echo ""

    # 执行部署步骤
    check_python
    create_venv
    install_dependencies
    install_fonts
    create_directories
    test_api

    show_usage

    # 询问是否启动
    if [ -t 0 ]; then
        quick_start_menu
    fi
}

# 运行主函数
main "$@"
