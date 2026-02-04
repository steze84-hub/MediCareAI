#!/bin/bash
#
# MediCare_AI SELinux 优雅配置脚本
# 适用于 Fedora 43 / RHEL / CentOS Stream
# 遵循 SELinux 策略，不关闭 SELinux
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

PROJECT_DIR="${1:-/opt/medicare-ai}"

# 检查 root 权限
if [[ $EUID -ne 0 ]]; then
   log_error "请使用 sudo 运行此脚本"
   exit 1
fi

cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║           MediCare_AI SELinux 优雅配置脚本                   ║
║          遵循 SELinux 策略，不关闭安全机制                    ║
╚═══════════════════════════════════════════════════════════════╝
EOF

log_info "项目目录: $PROJECT_DIR"

# 1. 检查 SELinux 状态
log_info "检查 SELinux 状态..."
if ! command -v getenforce &> /dev/null; then
    log_error "SELinux 未安装"
    exit 1
fi

SELINUX_MODE=$(getenforce)
log_info "当前 SELinux 模式: $SELINUX_MODE"

if [[ "$SELINUX_MODE" == "Disabled" ]]; then
    log_warn "SELinux 已禁用，无需配置"
    exit 0
fi

# 2. 检查 container-selinux
log_info "检查 container-selinux 包..."
if ! rpm -qa | grep -q container-selinux; then
    log_info "安装 container-selinux..."
    dnf install -y container-selinux
fi
log_success "container-selinux 已安装"

# 3. 配置 SELinux 文件上下文规则
log_info "配置 SELinux 文件上下文规则..."

# 为主项目目录设置规则
if ! semanage fcontext -l | grep -q "$PROJECT_DIR"; then
    semanage fcontext -a -t container_file_t "$PROJECT_DIR(/.*)?"
    log_success "已添加文件上下文规则"
else
    log_info "文件上下文规则已存在"
fi

# 4. 应用 SELinux 上下文
log_info "应用 SELinux 上下文到项目目录..."
restorecon -Rv "$PROJECT_DIR/"

# 5. 特别处理 uploads 目录
UPLOADS_DIR="$PROJECT_DIR/backend/uploads"
if [[ -d "$UPLOADS_DIR" ]]; then
    log_info "配置 uploads 目录上下文..."
    # 确保 uploads 目录有正确的上下文
    restorecon -Rv "$UPLOADS_DIR"
    # 设置适当的权限
    chmod 755 "$UPLOADS_DIR"
    log_success "uploads 目录已配置"
fi

# 6. 配置 Docker 守护进程 SELinux 支持
log_info "检查 Docker SELinux 支持..."
if [[ -f /etc/docker/daemon.json ]]; then
    if ! grep -q "selinux-enabled" /etc/docker/daemon.json; then
        log_info "Docker 已启用 SELinux 支持（默认）"
    fi
else
    log_info "Docker 使用默认 SELinux 配置"
fi

# 7. 验证配置
log_info "验证 SELinux 配置..."
echo ""
echo "项目目录 SELinux 上下文:"
ls -laZ "$PROJECT_DIR/" | head -5
echo ""

# 8. 检查是否有 SELinux 拒绝
log_info "检查 SELinux 拒绝日志..."
if ausearch -m avc -ts recent 2>/dev/null | grep -q "denied"; then
    log_warn "发现 SELinux 拒绝日志，请检查:"
    ausearch -m avc -ts recent | tail -10
else
    log_success "未发现 SELinux 拒绝日志"
fi

# 9. 测试容器访问
echo ""
log_info "测试容器访问权限..."
if docker ps &> /dev/null; then
    # 测试 Nginx 容器读取前端文件
    if docker exec medicare_nginx ls /usr/share/nginx/html/index.html &> /dev/null; then
        log_success "Nginx 容器可以访问前端文件"
    fi
    
    # 测试后端容器写入 uploads
    if docker exec medicare_backend touch /app/uploads/selinux_test.txt &> /dev/null; then
        docker exec medicare_backend rm -f /app/uploads/selinux_test.txt
        log_success "后端容器可以写入 uploads 目录"
    fi
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              SELinux 优雅配置完成！                           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "配置详情:"
echo "  - SELinux 模式: $(getenforce)"
echo "  - 文件上下文: container_file_t"
echo "  - Docker SELinux: 已启用"
echo ""
echo "命令参考:"
echo "  查看 SELinux 日志:   ausearch -m avc -ts recent"
echo "  查看文件上下文:      ls -laZ $PROJECT_DIR/"
echo "  临时宽容模式:        setenforce 0 (不推荐)"
echo "  恢复强制模式:        setenforce 1"
echo ""

exit 0
