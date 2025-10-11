#!/bin/bash

# OTRS Ticket Analysis Web Application Installer for Linux
# 版本: 2.0.0 - 支持系统服务部署
# 作者: 自动生成

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 应用配置
APP_NAME="otrs-web"
APP_USER="www-data"
APP_GROUP="www-data"
APP_PORT="15001"
APP_DIR="$(pwd)"

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
        version=$("$python_cmd" -c "import sys; print('.'.join(map(str, sys.version_info[:2])))" 2>/dev/null)
        if [ $? -eq 0 ] && [ -n "$version" ]; then
            # 使用awk进行版本比较，避免bc依赖
            if awk -v ver="$version" 'BEGIN {split(ver, parts, "."); major=parts[1]; minor=parts[2]; if (major > 3 || (major == 3 && minor >= 9)) exit 0; else exit 1}'; then
                echo "$python_cmd"
                return 0
            fi
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
    echo "  - Python包依赖 (Flask, pandas, matplotlib, gunicorn等)"
    echo "  - 创建虚拟环境"
    echo "  - 设置上传目录权限"
    echo "  - 配置系统服务 (systemd)"
    echo ""
}

# 检查系统要求
check_system_requirements() {
    log_info "检查系统要求..."
    
    # 检查操作系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        log_info "检测到操作系统: $NAME $VERSION"
        OS_NAME="$NAME"
        OS_VERSION="$VERSION_ID"
    else
        log_warning "无法确定操作系统类型"
        OS_NAME="unknown"
    fi
    
    # 检查Python
    local python_cmd
    if python_cmd=$(check_python_version "python3"); then
        log_success "找到 Python: $python_cmd"
    elif python_cmd=$(check_python_version "python"); then
        log_success "找到 Python: $python_cmd"
    else
        log_info "未找到 Python 3.9+，开始自动安装..."
        install_python
        if python_cmd=$(check_python_version "python3"); then
            log_success "Python 安装成功: $python_cmd"
        else
            log_error "Python 安装失败，请手动安装 Python 3.9+"
        fi
    fi
    
    # 检查pip
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        log_info "pip 未安装，开始自动安装..."
        install_pip
        if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
            log_error "pip 安装失败，请手动安装 pip"
        else
            log_success "pip 安装成功"
        fi
    fi
    
    PYTHON_CMD="$python_cmd"
}

# 安装Python
install_python() {
    log_info "安装 Python 3.9+..."
    
    if [[ "$OS_NAME" == *"Ubuntu"* ]] || [[ "$OS_NAME" == *"Debian"* ]]; then
        # Ubuntu/Debian
        sudo apt-get update
        sudo apt-get install -y software-properties-common
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt-get update
        sudo apt-get install -y python3.9 python3.9-venv python3.9-dev
        sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1
        
    elif [[ "$OS_NAME" == *"CentOS"* ]] || [[ "$OS_NAME" == *"Red Hat"* ]]; then
        # CentOS/RHEL
        sudo yum install -y epel-release
        sudo yum install -y python39 python39-devel
        
    elif [[ "$OS_NAME" == *"Fedora"* ]]; then
        # Fedora
        sudo dnf install -y python39 python39-devel
        
    else
        log_error "无法自动安装 Python，请手动安装 Python 3.9+"
        exit 1
    fi
}

# 安装pip
install_pip() {
    log_info "安装 pip..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-pip
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3-pip
    else
        # 使用get-pip.py作为备用方案
        curl -sS https://bootstrap.pypa.io/get-pip.py | python3
    fi
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
            python3-venv \
            python3-devel \
            gcc \
            openssl-devel \
            libffi-devel
    elif command -v dnf &> /dev/null; then
        # Fedora
        sudo dnf install -y \
            python3-venv \
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
    
    # 设置所有权
    if id "$APP_USER" &>/dev/null; then
        sudo chown -R $APP_USER:$APP_GROUP uploads
        log_success "设置上传目录所有权: $APP_USER:$APP_GROUP"
    else
        log_warning "用户 $APP_USER 不存在，跳过所有权设置"
    fi
    
    log_success "目录权限设置完成"
}

# 创建系统服务
create_systemd_service() {
    log_info "创建系统服务..."
    
    local service_file="/etc/systemd/system/${APP_NAME}.service"
    
    if [ ! -f "$service_file" ]; then
        sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=OTRS Ticket Analysis Web Application
After=network.target
Requires=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_GROUP
WorkingDirectory=$APP_DIR
Environment=PYTHONPATH=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn -w 4 -b 0.0.0.0:$APP_PORT --access-logfile - --error-logfile - app:app
Restart=always
RestartSec=5
TimeoutStopSec=30
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$APP_NAME

# 安全设置
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=full
ProtectHome=yes

[Install]
WantedBy=multi-user.target
EOF

        log_success "系统服务文件创建完成: $service_file"
        
        # 重新加载systemd配置
        sudo systemctl daemon-reload
        log_success "systemd配置已重新加载"
        
    else
        log_warning "系统服务文件已存在: $service_file"
    fi
}

# 启用并启动服务
enable_and_start_service() {
    log_info "启用并启动系统服务..."
    
    local service_name="${APP_NAME}.service"
    
    # 启用服务
    sudo systemctl enable "$service_name"
    log_success "服务已启用: $service_name"
    
    # 启动服务
    sudo systemctl start "$service_name"
    
    # 检查服务状态
    if sudo systemctl is-active --quiet "$service_name"; then
        log_success "服务启动成功: $service_name"
        sudo systemctl status "$service_name" --no-pager -l
    else
        log_error "服务启动失败，请检查日志: journalctl -u $service_name"
    fi
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    if command -v ufw &> /dev/null && sudo ufw status | grep -q "Status: active"; then
        sudo ufw allow $APP_PORT
        log_success "防火墙已配置，允许端口: $APP_PORT"
    elif command -v firewall-cmd &> /dev/null; then
        sudo firewall-cmd --permanent --add-port=${APP_PORT}/tcp
        sudo firewall-cmd --reload
        log_success "防火墙已配置，允许端口: $APP_PORT"
    else
        log_warning "未检测到活动的防火墙，跳过配置"
    fi
}

# 显示安装完成信息
show_completion() {
    local service_name="${APP_NAME}.service"
    local ip_address=$(hostname -I | awk '{print $1}')
    
    echo ""
    echo "=========================================="
    echo "  安装完成！"
    echo "=========================================="
    echo ""
    echo "应用信息："
    echo "  - 服务名称: $service_name"
    echo "  - 运行用户: $APP_USER"
    echo "  - 监听端口: $APP_PORT"
    echo "  - 访问地址: http://$ip_address:$APP_PORT"
    echo ""
    echo "管理命令："
    echo "  # 启动服务"
    echo "  sudo systemctl start $service_name"
    echo ""
    echo "  # 停止服务"
    echo "  sudo systemctl stop $service_name"
    echo ""
    echo "  # 重启服务"
    echo "  sudo systemctl restart $service_name"
    echo ""
    echo "  # 查看状态"
    echo "  sudo systemctl status $service_name"
    echo ""
    echo "  # 查看日志"
    echo "  journalctl -u $service_name -f"
    echo ""
    echo "  # 开机自启"
    echo "  sudo systemctl enable $service_name"
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
    create_systemd_service
    enable_and_start_service
    configure_firewall
    show_completion
}

# 显示帮助信息
show_help() {
    echo "使用说明:"
    echo "  ./install.sh        - 安装应用并配置系统服务"
    echo "  ./install.sh --help - 显示帮助信息"
    echo ""
    echo "选项:"
    echo "  --no-service    - 仅安装应用，不配置系统服务"
    echo "  --help, -h      - 显示帮助信息"
    echo ""
    echo "环境要求:"
    echo "  - Linux 系统"
    echo "  - Python 3.9+"
    echo "  - pip"
    echo ""
}

# 检查是否以root运行
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_warning "此脚本需要root权限来配置系统服务"
        log_info "请使用sudo重新运行此脚本: sudo ./install.sh"
        exit 1
    fi
}

# 主程序
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# 检查是否配置系统服务
CONFIGURE_SERVICE=true
if [ "$1" = "--no-service" ]; then
    CONFIGURE_SERVICE=false
    log_info "跳过系统服务配置"
fi

# 如果需要配置系统服务，检查root权限
if [ "$CONFIGURE_SERVICE" = true ]; then
    check_root
fi

# 执行安装
main_install

log_success "OTRS工单数据分析Web应用安装完成！"
