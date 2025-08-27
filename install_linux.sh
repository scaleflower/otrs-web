#!/bin/bash

# OTRS Ticket Analysis Web Application Installer for Linux
# 版本: 1.0.0
# 作者: 自动生成

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "命令 '$1' 未找到，请先安装"
    fi
}

# 检查Python版本
check_python_version() {
    local python_cmd="$1"
    if command -v "$python_cmd" &> /dev/null; then
        local version
        version=$("$python_cmd" -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
        if [ "$(echo "$version >= 3.9" | bc -l)" -eq 1 ]; then
            echo "$python_cmd"
            return 0
        fi
    fi
    return 1
}

# 显示欢迎信息
show_welcome() {
    echo "=========================================="
    echo "  OTRS工单数据分析Web应用安装程序"
    echo "=========================================="
    echo "这个脚本将安装以下组件："
    echo "  - Python 3.9+ (如果未安装)"
    echo "  - 必要的系统依赖"
    echo "  - Python包依赖 (Flask, pandas, matplotlib等)"
    echo "  - 创建虚拟环境"
    echo "  - 设置上传目录权限"
    echo ""
}

# 检查系统要求
check_system_requirements() {
    log_info "检查系统要求..."
    
    # 检查操作系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        log_info "检测到操作系统: $NAME $VERSION"
    else
        log_warning "无法确定操作系统类型"
    fi
    
    # 检查Python
    local python_cmd
    if python_cmd=$(check_python_version "python3"); then
        log_success "找到 Python: $python_cmd"
    elif python_cmd=$(check_python_version "python"); then
        log_success "找到 Python: $python_cmd"
    else
        log_error "需要 Python 3.9 或更高版本，请先安装 Python"
    fi
    
    # 检查pip
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        log_error "pip 未安装，请先安装 pip"
    fi
    
    PYTHON_CMD="$python_cmd"
}

# 安装系统依赖
install_system_dependencies() {
    log_info "安装系统依赖..."
    
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y \
            python3-venv \
            python3-pip \
            gcc \
            libffi-dev \
            libssl-dev \
            python3-dev
    elif command -v yum &> /dev/null; then
        # RHEL/CentOS
        sudo yum install -y \
            python3-devel \
            gcc \
            openssl-devel \
            libffi-devel
    elif command -v dnf &> /dev/null; then
        # Fedora
        sudo dnf install -y \
            python3-devel \
            gcc \
            openssl-devel \
            libffi-devel
    else
        log_warning "无法自动安装系统依赖，请手动安装：python3-venv python3-pip gcc libffi-dev libssl-dev python3-dev"
    fi
}

# 创建虚拟环境
create_virtualenv() {
    log_info "创建Python虚拟环境..."
    
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        log_success "虚拟环境创建成功"
    else
        log_warning "虚拟环境已存在，跳过创建"
    fi
}

# 安装Python依赖
install_python_dependencies() {
    log_info "安装Python依赖..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "Python依赖安装完成"
    else
        log_error "requirements.txt 文件未找到"
    fi
    
    # 停用虚拟环境
    deactivate
}

# 设置目录权限
setup_directories() {
    log_info "设置目录权限..."
    
    # 创建上传目录
    mkdir -p uploads
    chmod 755 uploads
    
    # 设置脚本执行权限
    if [ -f "run_web.sh" ]; then
        chmod +x run_web.sh
    fi
    
    log_success "目录权限设置完成"
}

# 创建启动脚本
create_startup_script() {
    log_info "创建启动脚本..."
    
    cat > run_web.sh << 'EOF'
#!/bin/bash

# OTRS Web应用启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "错误: 虚拟环境未找到，请先运行 install.sh"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 启动应用
echo "启动 OTRS 工单数据分析Web应用..."
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止应用"

python app.py

# 停用虚拟环境
deactivate
EOF

    chmod +x run_web.sh
    log_success "启动脚本创建完成"
}

# 显示安装完成信息
show_completion() {
    echo ""
    echo "=========================================="
    echo "  安装完成！"
    echo "=========================================="
    echo ""
    echo "下一步操作："
    echo "  1. 启动应用: ./run_web.sh"
    echo "  2. 在浏览器中访问: http://localhost:5000"
    echo ""
    echo "或者使用以下命令直接启动："
    echo "  source venv/bin/activate && python app.py"
    echo ""
    echo "应用功能："
    echo "  - 上传Excel格式的OTRS工单数据"
    echo "  - 分析工单统计信息"
    echo "  - 生成可视化图表"
    echo "  - 导出分析结果"
    echo ""
}

# 主安装函数
main_install() {
    show_welcome
    check_system_requirements
    install_system_dependencies
    create_virtualenv
    install_python_dependencies
    setup_directories
    create_startup_script
    show_completion
}

# 显示帮助信息
show_help() {
    echo "使用说明:"
    echo "  ./install_linux.sh        - 安装应用"
    echo "  ./install_linux.sh --help - 显示帮助信息"
    echo ""
    echo "环境要求:"
    echo "  - Linux 系统"
    echo "  - Python 3.9+"
    echo "  - pip"
    echo ""
}

# 主程序
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# 检查是否以root运行
if [ "$EUID" -eq 0 ]; then
    log_warning "不建议以root用户运行此脚本"
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 执行安装
main_install

log_success "OTRS工单数据分析Web应用安装完成！"
