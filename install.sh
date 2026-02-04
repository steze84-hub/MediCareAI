#!/bin/bash
#==============================================================================
# MediCare_AI One-Click Deployment Script
# Supported Distributions: Ubuntu 24.04, Fedora 43, openSUSE Leap 16.0,
#            openSUSE Tumbleweed, AOSC OS 13.0.7, openEuler 24.03, Deepin 25
# Version: 1.1.0
# Date: 2026-02-04
#==============================================================================

set -o pipefail
set -o errexit

#==============================================================================
# Color Definitions
#==============================================================================
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

#==============================================================================
# Global Variables
#==============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="MediCare_AI"
PROJECT_VERSION="v1.0.2"

# Language Setting
CURRENT_LANG="auto"

# Distribution Info
DISTRO_ID=""
DISTRO_NAME=""
DISTRO_VERSION=""
DISTRO_PRETTY_NAME=""
PACKAGE_MANAGER=""

# Special Flags
SELINUX_ENABLED=false
BUILDKIT_ISSUE=false
NEEDS_DOCKER_COMPOSE_UPGRADE=false

# Configuration
AI_API_URL=""
AI_API_KEY=""
MINERU_TOKEN=""
JWT_SECRET_KEY=""
DEPLOYMENT_TYPE=""
DOMAIN_NAME=""
SERVER_IP=""
HTTP_PORT=80
HTTPS_PORT=443
API_PORT=8000
FRONTEND_PORT=3000
POSTGRES_PORT=5432
REDIS_PORT=6379
DATA_PERSISTENCE=true
USE_CN_MIRROR=false

# Log File
LOG_FILE="/tmp/medicare_ai_deploy_$(date +%Y%m%d_%H%M%S).log"

#==============================================================================
# Multi-Language Support
#==============================================================================

# Translation Dictionary
declare -A I18N

# Initialize Chinese translations
init_i18n_zh() {
    I18N[zh_title]="MediCare_AI 智能医疗诊断系统"
    I18N[zh_subtitle]="一键部署脚本"
    I18N[zh_version]="版本"
    I18N[zh_welcome_info]="本脚本将帮助您在 Linux 系统上部署 MediCare_AI"
    I18N[zh_supported_distros]="支持的发行版"
    I18N[zh_language_select]="请选择语言 / Please select language"
    I18N[zh_option_zh]="1. 中文"
    I18N[zh_option_en]="2. English"
    I18N[zh_option_auto]="3. Auto-detect (自动检测)"
    I18N[zh_enter_choice]="请输入选项"
    I18N[zh_selected]="已选择"
    
    I18N[zh_check_admin]="检查管理员权限"
    I18N[zh_check_sudo]="正在检查 sudo 权限..."
    I18N[zh_need_admin]="需要管理员权限来执行安装操作"
    I18N[zh_admin_ops]="提示: 此脚本需要安装 Docker、系统依赖等"
    I18N[zh_sudo_ok]="sudo 权限验证通过"
    I18N[zh_root_user]="当前以 root 用户运行"
    
    I18N[zh_detect_distro]="检测 Linux 发行版"
    I18N[zh_distro_not_found]="无法找到 /etc/os-release 文件，无法识别发行版"
    I18N[zh_detected_system]="检测到系统"
    I18N[zh_unsupported_distro]="不支持的 Linux 发行版"
    I18N[zh_supported_list]="当前支持的发行版"
    I18N[zh_distro_complete]="发行版检测完成"
    
    I18N[zh_check_requirements]="检查系统要求"
    I18N[zh_check_memory]="检查内存"
    I18N[zh_memory_low]="内存不足"
    I18N[zh_memory_recommended]="推荐至少 4GB"
    I18N[zh_memory_ok]="内存检查通过"
    I18N[zh_check_disk]="检查磁盘空间"
    I18N[zh_disk_low]="磁盘空间不足"
    I18N[zh_disk_recommended]="推荐至少 10GB"
    I18N[zh_disk_ok]="磁盘空间检查通过"
    I18N[zh_continue_prompt]="是否继续"
    
    I18N[zh_user_agreement]="用户协议和风险提示"
    I18N[zh_license_title]="开源协议"
    I18N[zh_license_content]="MediCare_AI 采用 MIT License 开源协议"
    I18N[zh_license_rights]="您有权"
    I18N[zh_license_free_use]="- 自由使用、修改和分发本软件"
    I18N[zh_license_commercial]="- 用于商业或个人用途"
    I18N[zh_license_obligations]="您必须"
    I18N[zh_license_copyright]="- 保留版权声明和许可声明"
    I18N[zh_license_same_license]="- 修改后的软件必须同样使用 MIT 协议"
    
    I18N[zh_risk_title]="部署风险提示"
    I18N[zh_risk_system]="1. 系统变更"
    I18N[zh_risk_system_detail]="- 本脚本将安装 Docker 和 Docker Compose"
    I18N[zh_risk_selinux_detail]="- 可能需要配置 SELinux（Fedora/openSUSE）"
    I18N[zh_risk_config]="- 将创建系统服务和配置文件"
    I18N[zh_risk_network]="2. 网络访问"
    I18N[zh_risk_network_detail]="- 需要访问 Docker Hub 下载容器镜像"
    I18N[zh_risk_repo]="- 需要访问软件包仓库安装依赖"
    I18N[zh_risk_ports]="- 将开放指定的网络端口（HTTP/HTTPS/应用端口）"
    I18N[zh_risk_data]="3. 数据安全"
    I18N[zh_risk_data_detail]="- 数据库将存储在 Docker 卷中（可选择持久化）"
    I18N[zh_risk_api_key]="- 请妥善保管 API 密钥等敏感信息"
    I18N[zh_risk_backup]="- 建议定期备份重要数据"
    I18N[zh_risk_disclaimer]="4. 免责声明"
    I18N[zh_risk_not_medical]="- 本软件仅供学习和研究使用，不构成医疗建议"
    I18N[zh_risk_consult_doctor]="- 实际医疗决策请咨询专业医生"
    I18N[zh_risk_no_liability]="- 作者不对使用本软件造成的任何损失承担责任"
    
    I18N[zh_agree_prompt]="您是否已阅读并同意上述协议和风险提示"
    I18N[zh_agree_yes]="yes"
    I18N[zh_agree_confirm]="协议确认完成"
    I18N[zh_agree_reject]="未同意协议，退出部署"
    
    I18N[zh_api_config]="AI 服务配置（可选，可跳过）"
    I18N[zh_api_description]="配置AI服务和MinerU文档解析服务（可跳过，后续手动配置）"
    I18N[zh_api_ai_config]="AI 大模型 API 配置"
    I18N[zh_api_ai_url]="AI API 地址 [回车跳过]"
    I18N[zh_api_ai_key]="AI API 密钥"
    I18N[zh_api_model_id]="AI 模型 ID [默认"
    I18N[zh_api_skip_warning]="跳过 AI API 配置，请在部署完成后手动编辑 .env 文件"
    I18N[zh_api_mineru_config]="MinerU 文档解析配置"
    I18N[zh_api_mineru_token]="MinerU API 令牌 [回车跳过]"
    I18N[zh_api_skip_mineru]="跳过 MinerU 配置，请在部署完成后手动编辑 .env 文件"
    I18N[zh_api_jwt_generated]="已生成 JWT 密钥"
    
    I18N[zh_network_config]="网络配置"
    I18N[zh_network_type]="部署类型选择"
    I18N[zh_network_domain]="1. 域名部署    - 使用您的域名访问（需要配置 DNS）"
    I18N[zh_network_lan]="2. 局域网部署  - 使用局域网 IP 访问（适合内部使用）"
    I18N[zh_network_local]="3. 本地测试    - 使用 127.0.0.1（仅本机访问）"
    I18N[zh_network_choice]="请选择部署类型"
    I18N[zh_network_invalid]="无效的选择"
    I18N[zh_network_domain_input]="请输入您的域名"
    I18N[zh_network_domain_empty]="域名不能为空"
    I18N[zh_network_domain_use]="使用域名部署"
    I18N[zh_network_lan_default]="默认"
    I18N[zh_network_lan_input]="请输入局域网 IP 地址"
    I18N[zh_network_lan_use]="使用局域网 IP"
    I18N[zh_network_local_use]="使用本地测试模式"
    I18N[zh_network_complete]="网络配置完成"
    I18N[zh_network_port_info]="端口配置（使用默认值直接回车）"
    I18N[zh_network_http_port]="HTTP 端口 [默认"
    I18N[zh_network_https_port]="HTTPS 端口 [默认"
    I18N[zh_network_api_port]="API 端口 [默认"
    I18N[zh_network_frontend_port]="前端端口 [默认"
    I18N[zh_network_port_conflict]="端口冲突"
    I18N[zh_network_port_repeat]="端口与其他端口重复"
    
    I18N[zh_data_config]="数据持久化配置"
    I18N[zh_data_description]="启用数据持久化后，数据库和上传的文件将保存在 Docker 卷中"
    I18N[zh_data_recommend]="建议: 生产环境务必启用数据持久化"
    I18N[zh_data_enable]="是否启用数据持久化"
    I18N[zh_data_disabled]="数据持久化已禁用，容器删除后数据将丢失"
    I18N[zh_data_enabled]="数据持久化已启用"
    
    I18N[zh_mirror_config]="镜像源配置"
    I18N[zh_mirror_prompt]="是否使用中国镜像源加速下载"
    I18N[zh_mirror_enabled]="将使用中国镜像源"
    
    I18N[zh_docker_install]="安装 Docker"
    I18N[zh_docker_check]="Docker 已安装"
    I18N[zh_docker_skip]="跳过安装"
    I18N[zh_docker_installing]="正在安装 Docker..."
    I18N[zh_docker_complete]="Docker 安装完成"
    I18N[zh_docker_start]="启动 Docker 服务"
    I18N[zh_docker_add_group]="将当前用户添加到 docker 组"
    
    I18N[zh_compose_install]="安装 Docker Compose v2"
    I18N[zh_compose_check_v2]="Docker Compose v2 已安装"
    I18N[zh_compose_upgrade]="Docker Compose v1 检测到，将升级"
    I18N[zh_compose_installing]="正在安装 Docker Compose v2..."
    I18N[zh_compose_remove_old]="移除旧版本"
    I18N[zh_compose_verify]="验证安装"
    I18N[zh_compose_fail]="Docker Compose 安装失败"
    I18N[zh_compose_complete]="Docker Compose v2 安装完成"
    
    I18N[zh_selinux_config]="配置 SELinux"
    I18N[zh_selinux_not_installed]="SELinux 工具未安装，跳过配置"
    I18N[zh_selinux_status]="SELinux 状态"
    I18N[zh_selinux_enforcing]="SELinux 处于 enforcing 模式"
    I18N[zh_selinux_set_permissive]="正在设置为 permissive 模式..."
    I18N[zh_selinux_complete]="SELinux 已设置为 permissive 模式"
    
    I18N[zh_docker_test]="测试 Docker 运行"
    I18N[zh_docker_test_fail]="Docker 测试失败，请检查 Docker 安装"
    I18N[zh_docker_test_ok]="Docker 运行正常"
    
    I18N[zh_gen_config]="生成配置文件"
    I18N[zh_gen_env]="生成 .env 配置文件"
    I18N[zh_gen_random_pass]="生成随机密码"
    I18N[zh_gen_env_complete]=".env 配置文件已生成"
    I18N[zh_gen_compose_update]="更新 Docker Compose 配置"
    I18N[zh_gen_compose_backup]="创建备份"
    I18N[zh_gen_port_update]="更新端口为"
    I18N[zh_gen_data_disable]="数据持久化已禁用，将使用临时存储"
    I18N[zh_gen_compose_complete]="Docker Compose 配置已更新"
    
    I18N[zh_deploy_pull]="拉取 Docker 镜像"
    I18N[zh_deploy_pull_postgres]="拉取 PostgreSQL..."
    I18N[zh_deploy_pull_redis]="拉取 Redis..."
    I18N[zh_deploy_pull_nginx]="拉取 Nginx..."
    I18N[zh_deploy_pull_complete]="基础镜像拉取完成"
    I18N[zh_deploy_build]="构建和启动服务"
    I18N[zh_deploy_set_env]="设置环境变量"
    I18N[zh_deploy_building]="正在构建应用镜像（这可能需要几分钟）..."
    I18N[zh_deploy_starting]="正在启动服务..."
    I18N[zh_deploy_complete]="服务启动完成"
    
    I18N[zh_wait_postgres]="等待 PostgreSQL..."
    I18N[zh_wait_ready]="就绪"
    I18N[zh_wait_timeout]="启动超时，继续等待..."
    I18N[zh_wait_backend]="等待后端服务..."
    I18N[zh_wait_init_complete]="服务初始化完成"
    
    I18N[zh_health_check]="健康检查"
    I18N[zh_health_api_check]="检查 API 服务..."
    I18N[zh_health_api_ok]="API 服务健康"
    I18N[zh_health_timeout]="健康检查超时，请手动检查服务状态"
    I18N[zh_health_container_status]="容器状态"
    
    I18N[zh_complete_title]="部署成功"
    I18N[zh_complete_access]="访问信息"
    I18N[zh_complete_frontend]="前端地址"
    I18N[zh_complete_api]="API 地址"
    I18N[zh_complete_service_ports]="服务端口"
    I18N[zh_complete_http]="HTTP"
    I18N[zh_complete_https]="HTTPS"
    I18N[zh_complete_api_port]="API"
    I18N[zh_complete_frontend_port]="Frontend"
    I18N[zh_complete_postgres]="Postgres"
    I18N[zh_complete_redis]="Redis"
    I18N[zh_complete_commands]="管理命令"
    I18N[zh_complete_cmd_logs]="查看日志"
    I18N[zh_complete_cmd_stop]="停止服务"
    I18N[zh_complete_cmd_restart]="重启服务"
    I18N[zh_complete_cmd_status]="查看状态"
    I18N[zh_complete_config_files]="配置文件"
    I18N[zh_complete_env]="环境变量"
    I18N[zh_complete_docker]="Docker"
    I18N[zh_complete_next_steps]="后续配置"
    I18N[zh_complete_skip_config]="如果跳过了 API 配置，请编辑 .env 文件配置 AI 服务和 MinerU"
    I18N[zh_complete_log_file]="日志文件"
    I18N[zh_complete_finished]="部署完成"
    I18N[zh_complete_visit]="请访问"
    
    I18N[zh_error]="错误"
    I18N[zh_error_script_fail]="脚本执行失败"
    I18N[zh_error_exit_code]="退出码"
    I18N[zh_error_check_log]="查看日志文件"
    I18N[zh_error_interrupted]="脚本被用户中断"
    
    I18N[zh_version_not_supported]="版本可能不完全支持"
    I18N[zh_version_recommended]="推荐版本"
}

# Initialize English translations
init_i18n_en() {
    I18N[en_title]="MediCare_AI Intelligent Medical Diagnosis System"
    I18N[en_subtitle]="One-Click Deployment Script"
    I18N[en_version]="Version"
    I18N[en_welcome_info]="This script will help you deploy MediCare_AI on Linux"
    I18N[en_supported_distros]="Supported Distributions"
    I18N[en_language_select]="Please select language / 请选择语言"
    I18N[en_option_zh]="1. 中文"
    I18N[en_option_en]="2. English"
    I18N[en_option_auto]="3. Auto-detect (自动检测)"
    I18N[en_enter_choice]="Enter your choice"
    I18N[en_selected]="Selected"
    
    I18N[en_check_admin]="Checking Administrator Privileges"
    I18N[en_check_sudo]="Checking sudo privileges..."
    I18N[en_need_admin]="Administrator privileges required"
    I18N[en_admin_ops]="Note: This script needs to install Docker and system dependencies"
    I18N[en_sudo_ok]="sudo privileges verified"
    I18N[en_root_user]="Running as root user"
    
    I18N[en_detect_distro]="Detecting Linux Distribution"
    I18N[en_distro_not_found]="Cannot find /etc/os-release, unable to identify distribution"
    I18N[en_detected_system]="Detected system"
    I18N[en_unsupported_distro]="Unsupported Linux distribution"
    I18N[en_supported_list]="Currently supported distributions"
    I18N[en_distro_complete]="Distribution detection complete"
    
    I18N[en_check_requirements]="Checking System Requirements"
    I18N[en_check_memory]="Checking memory"
    I18N[en_memory_low]="Insufficient memory"
    I18N[en_memory_recommended]="Recommended at least 4GB"
    I18N[en_memory_ok]="Memory check passed"
    I18N[en_check_disk]="Checking disk space"
    I18N[en_disk_low]="Insufficient disk space"
    I18N[en_disk_recommended]="Recommended at least 10GB"
    I18N[en_disk_ok]="Disk space check passed"
    I18N[en_continue_prompt]="Continue"
    
    I18N[en_user_agreement]="User Agreement and Risk Notice"
    I18N[en_license_title]="Open Source License"
    I18N[en_license_content]="MediCare_AI is licensed under MIT License"
    I18N[en_license_rights]="Your Rights"
    I18N[en_license_free_use]="- Free to use, modify, and distribute this software"
    I18N[en_license_commercial]="- Use for commercial or personal purposes"
    I18N[en_license_obligations]="Your Obligations"
    I18N[en_license_copyright]="- Retain copyright and license notices"
    I18N[en_license_same_license]="- Modified software must also use MIT license"
    
    I18N[en_risk_title]="Deployment Risk Notice"
    I18N[en_risk_system]="1. System Changes"
    I18N[en_risk_system_detail]="- This script will install Docker and Docker Compose"
    I18N[en_risk_selinux_detail]="- May need to configure SELinux (Fedora/openSUSE)"
    I18N[en_risk_config]="- Will create system services and configuration files"
    I18N[en_risk_network]="2. Network Access"
    I18N[en_risk_network_detail]="- Requires access to Docker Hub to download images"
    I18N[en_risk_repo]="- Requires access to package repositories"
    I18N[en_risk_ports]="- Will open specified network ports (HTTP/HTTPS/application)"
    I18N[en_risk_data]="3. Data Security"
    I18N[en_risk_data_detail]="- Database will be stored in Docker volumes (optional persistence)"
    I18N[en_risk_api_key]="- Please keep API keys and sensitive information secure"
    I18N[en_risk_backup]="- Regular backups of important data recommended"
    I18N[en_risk_disclaimer]="4. Disclaimer"
    I18N[en_risk_not_medical]="- This software is for research and learning only, not medical advice"
    I18N[en_risk_consult_doctor]="- Consult professional doctors for actual medical decisions"
    I18N[en_risk_no_liability]="- Authors are not liable for any damages from using this software"
    
    I18N[en_agree_prompt]="Have you read and agree to the above agreement and risks"
    I18N[en_agree_yes]="yes"
    I18N[en_agree_confirm]="Agreement confirmed"
    I18N[en_agree_reject]="Agreement not accepted, exiting deployment"
    
    I18N[en_api_config]="AI Service Configuration (Optional)"
    I18N[en_api_description]="Configure AI service and MinerU document parsing (can skip, configure manually later)"
    I18N[en_api_ai_config]="AI Model API Configuration"
    I18N[en_api_ai_url]="AI API URL [Enter to skip]"
    I18N[en_api_ai_key]="AI API Key"
    I18N[en_api_model_id]="AI Model ID [Default"
    I18N[en_api_skip_warning]="Skipped AI API config. Please edit .env file after deployment"
    I18N[en_api_mineru_config]="MinerU Document Parsing Configuration"
    I18N[en_api_mineru_token]="MinerU API Token [Enter to skip]"
    I18N[en_api_skip_mineru]="Skipped MinerU config. Please edit .env file after deployment"
    I18N[en_api_jwt_generated]="JWT key generated"
    
    I18N[en_network_config]="Network Configuration"
    I18N[en_network_type]="Select Deployment Type"
    I18N[en_network_domain]="1. Domain    - Use your domain (requires DNS configuration)"
    I18N[en_network_lan]="2. LAN IP    - Use LAN IP (suitable for internal use)"
    I18N[en_network_local]="3. Local     - Use 127.0.0.1 (localhost only)"
    I18N[en_network_choice]="Please select deployment type"
    I18N[en_network_invalid]="Invalid selection"
    I18N[en_network_domain_input]="Please enter your domain"
    I18N[en_network_domain_empty]="Domain cannot be empty"
    I18N[en_network_domain_use]="Using domain deployment"
    I18N[en_network_lan_default]="Default"
    I18N[en_network_lan_input]="Please enter LAN IP address"
    I18N[en_network_lan_use]="Using LAN IP"
    I18N[en_network_local_use]="Using local test mode"
    I18N[en_network_complete]="Network configuration complete"
    I18N[en_network_port_info]="Port Configuration (Press Enter for defaults)"
    I18N[en_network_http_port]="HTTP Port [Default"
    I18N[en_network_https_port]="HTTPS Port [Default"
    I18N[en_network_api_port]="API Port [Default"
    I18N[en_network_frontend_port]="Frontend Port [Default"
    I18N[en_network_port_conflict]="Port conflict"
    I18N[en_network_port_repeat]="port conflicts with other ports"
    
    I18N[en_data_config]="Data Persistence Configuration"
    I18N[en_data_description]="When enabled, database and uploaded files will be saved in Docker volumes"
    I18N[en_data_recommend]="Recommendation: Enable data persistence for production"
    I18N[en_data_enable]="Enable data persistence"
    I18N[en_data_disabled]="Data persistence disabled, data will be lost when containers are removed"
    I18N[en_data_enabled]="Data persistence enabled"
    
    I18N[en_mirror_config]="Mirror Source Configuration"
    I18N[en_mirror_prompt]="Use China mirror source for faster downloads"
    I18N[en_mirror_enabled]="Will use China mirror source"
    
    I18N[en_docker_install]="Installing Docker"
    I18N[en_docker_check]="Docker already installed"
    I18N[en_docker_skip]="Skipping installation"
    I18N[en_docker_installing]="Installing Docker..."
    I18N[en_docker_complete]="Docker installation complete"
    I18N[en_docker_start]="Starting Docker service"
    I18N[en_docker_add_group]="Adding current user to docker group"
    
    I18N[en_compose_install]="Installing Docker Compose v2"
    I18N[en_compose_check_v2]="Docker Compose v2 already installed"
    I18N[en_compose_upgrade]="Docker Compose v1 detected, will upgrade"
    I18N[en_compose_installing]="Installing Docker Compose v2..."
    I18N[en_compose_remove_old]="Removing old version"
    I18N[en_compose_verify]="Verifying installation"
    I18N[en_compose_fail]="Docker Compose installation failed"
    I18N[en_compose_complete]="Docker Compose v2 installation complete"
    
    I18N[en_selinux_config]="Configuring SELinux"
    I18N[en_selinux_not_installed]="SELinux tools not installed, skipping"
    I18N[en_selinux_status]="SELinux status"
    I18N[en_selinux_enforcing]="SELinux is in enforcing mode"
    I18N[en_selinux_set_permissive]="Setting to permissive mode..."
    I18N[en_selinux_complete]="SELinux set to permissive mode"
    
    I18N[en_docker_test]="Testing Docker"
    I18N[en_docker_test_fail]="Docker test failed, please check Docker installation"
    I18N[en_docker_test_ok]="Docker running normally"
    
    I18N[en_gen_config]="Generating Configuration Files"
    I18N[en_gen_env]="Generating .env configuration file"
    I18N[en_gen_random_pass]="Generating random passwords"
    I18N[en_gen_env_complete]=".env configuration file generated"
    I18N[en_gen_compose_update]="Updating Docker Compose configuration"
    I18N[en_gen_compose_backup]="Creating backup"
    I18N[en_gen_port_update]="Updating port to"
    I18N[en_gen_data_disable]="Data persistence disabled, will use temporary storage"
    I18N[en_gen_compose_complete]="Docker Compose configuration updated"
    
    I18N[en_deploy_pull]="Pulling Docker Images"
    I18N[en_deploy_pull_postgres]="Pulling PostgreSQL..."
    I18N[en_deploy_pull_redis]="Pulling Redis..."
    I18N[en_deploy_pull_nginx]="Pulling Nginx..."
    I18N[en_deploy_pull_complete]="Base images pulled"
    I18N[en_deploy_build]="Building and Starting Services"
    I18N[en_deploy_set_env]="Setting environment variables"
    I18N[en_deploy_building]="Building application images (this may take a few minutes)..."
    I18N[en_deploy_starting]="Starting services..."
    I18N[en_deploy_complete]="Services started"
    
    I18N[en_wait_postgres]="Waiting for PostgreSQL..."
    I18N[en_wait_ready]="Ready"
    I18N[en_wait_timeout]="Timeout, continuing to wait..."
    I18N[en_wait_backend]="Waiting for backend service..."
    I18N[en_wait_init_complete]="Service initialization complete"
    
    I18N[en_health_check]="Health Check"
    I18N[en_health_api_check]="Checking API service..."
    I18N[en_health_api_ok]="API service healthy"
    I18N[en_health_timeout]="Health check timeout, please check service status manually"
    I18N[en_health_container_status]="Container Status"
    
    I18N[en_complete_title]="Deployment Complete"
    I18N[en_complete_access]="Access Information"
    I18N[en_complete_frontend]="Frontend"
    I18N[en_complete_api]="API"
    I18N[en_complete_service_ports]="Service Ports"
    I18N[en_complete_http]="HTTP"
    I18N[en_complete_https]="HTTPS"
    I18N[en_complete_api_port]="API"
    I18N[en_complete_frontend_port]="Frontend"
    I18N[en_complete_postgres]="Postgres"
    I18N[en_complete_redis]="Redis"
    I18N[en_complete_commands]="Management Commands"
    I18N[en_complete_cmd_logs]="View logs"
    I18N[en_complete_cmd_stop]="Stop services"
    I18N[en_complete_cmd_restart]="Restart services"
    I18N[en_complete_cmd_status]="View status"
    I18N[en_complete_config_files]="Configuration Files"
    I18N[en_complete_env]="Environment"
    I18N[en_complete_docker]="Docker"
    I18N[en_complete_next_steps]="Next Steps"
    I18N[en_complete_skip_config]="If you skipped API config, please edit .env to configure AI and MinerU"
    I18N[en_complete_log_file]="Log File"
    I18N[en_complete_finished]="Deployment finished"
    I18N[en_complete_visit]="Please visit"
    
    I18N[en_error]="Error"
    I18N[en_error_script_fail]="Script execution failed"
    I18N[en_error_exit_code]="Exit code"
    I18N[en_error_check_log]="Check log file"
    I18N[en_error_interrupted]="Script interrupted by user"
    
    I18N[en_version_not_supported]="Version may not be fully supported"
    I18N[en_version_recommended]="Recommended version"
}

# Initialize translations
init_translations() {
    init_i18n_zh
    init_i18n_en
}

# Get translated text
_() {
    local key="${CURRENT_LANG}_$1"
    local text="${I18N[$key]}"
    
    # Fallback to English if translation not found
    if [[ -z "$text" ]]; then
        text="${I18N["en_$1"]}"
    fi
    
    # Final fallback to key name
    if [[ -z "$text" ]]; then
        text="$1"
    fi
    
    echo "$text"
}

# Select language
select_language() {
    clear
    echo -e "${BOLD}"
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                     MediCare_AI Intelligent System                        ║
║                     MediCare_AI 智能医疗诊断系统                           ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

EOF
    echo -e "${NC}"
    
    echo -e "${BLUE}[LANGUAGE / 语言]${NC} ${BOLD}Please select language / 请选择语言${NC}\n"
    echo "  1. 中文 (Chinese)"
    echo "  2. English"
    echo "  3. Auto-detect / 自动检测"
    echo
    
    local choice
    read -p "$(echo -e "${CYAN}>>>${NC} Enter choice / 输入选项 [1-3]: ")" choice
    
    case "$choice" in
        1)
            CURRENT_LANG="zh"
            ;;
        2)
            CURRENT_LANG="en"
            ;;
        3|"")
            # Auto-detect from system locale
            local sys_lang
            sys_lang=$(echo "$LANG" | cut -d'_' -f1)
            if [[ "$sys_lang" == "zh" ]]; then
                CURRENT_LANG="zh"
            else
                CURRENT_LANG="en"
            fi
            ;;
        *)
            CURRENT_LANG="en"
            ;;
    esac
    
    echo
    log_info "$(_ selected): $CURRENT_LANG"
    echo
}

#==============================================================================
# Log Functions
#==============================================================================
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" | tee -a "$LOG_FILE"
}

log_step() {
    echo -e "\n${BLUE}[STEP]${NC} ${BOLD}$1${NC}" | tee -a "$LOG_FILE"
}

#==============================================================================
# Error Handling
#==============================================================================
cleanup_on_exit() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "$(_ error_script_fail), $(_ error_exit_code): $exit_code"
        log_info "$(_ error_check_log): $LOG_FILE"
    fi
}

trap cleanup_on_exit EXIT
trap 'log_error "$(_ error_interrupted)"; exit 130' INT TERM

exit_with_error() {
    log_error "$1"
    exit 1
}

#==============================================================================
# System Check Functions
#==============================================================================

check_admin_privileges() {
    log_step "$(_ check_admin)"
    
    if [[ $EUID -ne 0 ]]; then
        log_warning "$(_ check_sudo)"
        
        if ! sudo -n true 2>/dev/null; then
            log_info "$(_ need_admin)"
            log_info "$(_ admin_ops)"
            
            if ! sudo -v; then
                exit_with_error "$(_ error)"
            fi
        fi
        
        log_success "$(_ sudo_ok)"
    else
        log_success "$(_ root_user)"
    fi
}

detect_distro() {
    log_step "$(_ detect_distro)"
    
    if [[ ! -f /etc/os-release ]]; then
        exit_with_error "$(_ distro_not_found)"
    fi
    
    while IFS='=' read -r key value; do
        value="${value%\"}"
        value="${value#\"}"
        case "$key" in
            ID) DISTRO_ID="$value" ;;
            NAME) DISTRO_NAME="$value" ;;
            VERSION_ID) DISTRO_VERSION="$value" ;;
            PRETTY_NAME) DISTRO_PRETTY_NAME="$value" ;;
        esac
    done < /etc/os-release
    
    log_info "$(_ detected_system): ${DISTRO_PRETTY_NAME:-$DISTRO_NAME}"
    
    case "$DISTRO_ID" in
        ubuntu)
            PACKAGE_MANAGER="apt"
            check_version_supported "$DISTRO_VERSION" "24.04" "Ubuntu"
            ;;
        fedora)
            PACKAGE_MANAGER="dnf"
            check_version_supported "$DISTRO_VERSION" "43" "Fedora"
            SELINUX_ENABLED=true
            ;;
        opensuse-leap|opensuse|suse)
            DISTRO_ID="opensuse-leap"
            PACKAGE_MANAGER="zypper"
            SELINUX_ENABLED=true
            ;;
        opensuse-tumbleweed)
            PACKAGE_MANAGER="zypper"
            SELINUX_ENABLED=true
            BUILDKIT_ISSUE=true
            log_warning "openSUSE Tumbleweed detected, will handle BuildKit compatibility"
            ;;
        aosc)
            PACKAGE_MANAGER="apt"
            log_warning "AOSC OS may require manual Docker installation"
            ;;
        openeuler)
            PACKAGE_MANAGER="dnf"
            NEEDS_DOCKER_COMPOSE_UPGRADE=true
            log_warning "openEuler detected, will upgrade Docker Compose to v2"
            ;;
        deepin)
            PACKAGE_MANAGER="apt"
            NEEDS_DOCKER_COMPOSE_UPGRADE=true
            log_warning "Deepin detected, will upgrade Docker Compose to v2"
            ;;
        debian)
            PACKAGE_MANAGER="apt"
            log_warning "Debian not fully tested but should work"
            ;;
        *)
            log_error "$(_ unsupported_distro): $DISTRO_ID"
            log_info "$(_ supported_list):"
            log_info "  - Ubuntu 24.04 LTS"
            log_info "  - Fedora 43 Server"
            log_info "  - openSUSE Leap 16.0"
            log_info "  - openSUSE Tumbleweed"
            log_info "  - AOSC OS 13.0.7"
            log_info "  - openEuler 24.03 LTS-SP3"
            log_info "  - Deepin 25"
            exit 1
            ;;
    esac
    
    log_success "$(_ distro_complete): $DISTRO_ID ($PACKAGE_MANAGER)"
}

check_version_supported() {
    local current_version="$1"
    local min_version="$2"
    local distro_name="$3"
    
    local current_major="${current_version%%.*}"
    local min_major="${min_version%%.*}"
    
    if [[ "$current_major" -lt "$min_major" ]]; then
        log_warning "${distro_name} $(_ version_not_supported): ${current_version}"
        log_warning "$(_ version_recommended): ${min_version}+"
        
        read -p "$(_ continue_prompt)? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi
}

check_system_requirements() {
    log_step "$(_ check_requirements)"
    
    local total_mem
    total_mem=$(free -m | awk '/^Mem:/{print $2}')
    if [[ $total_mem -lt 2048 ]]; then
        log_warning "$(_ memory_low): ${total_mem}MB ($(_ memory_recommended))"
        read -p "$(_ continue_prompt)? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    else
        log_success "$(_ memory_ok): ${total_mem}MB"
    fi
    
    local available_space
    available_space=$(df -m "$SCRIPT_DIR" 2>/dev/null | awk 'NR==2 {print $4}')
    if [[ -z "$available_space" ]]; then
        available_space=$(df -m / | awk 'NR==2 {print $4}')
    fi
    
    if [[ $available_space -lt 10240 ]]; then
        log_warning "$(_ disk_low): ${available_space}MB ($(_ disk_recommended))"
        read -p "$(_ continue_prompt)? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    else
        log_success "$(_ disk_ok): ${available_space}MB"
    fi
}

#==============================================================================
# User Agreement
#==============================================================================
display_welcome() {
    clear
    echo -e "${BOLD}"
    cat << EOF
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                     $(_ title)                            ║
║                            $(_ subtitle)                                   ║
║                              $(_ version) $PROJECT_VERSION                                  ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

EOF
    echo -e "${NC}"

    log_info "$(_ welcome_info)"
    log_info "$(_ supported_distros): Ubuntu 24.04, Fedora 43, openSUSE, AOSC OS, openEuler, Deepin 25"
    echo
}

prompt_user_agreement() {
    log_step "$(_ user_agreement)"
    
    cat << EOF
┌─────────────────────────────────────────────────────────────────────────────┐
│ $(_ license_title)                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  $(_ license_content)                                                        │
│                                                                             │
│  $(_ license_rights):                                                        │
│  $(_ license_free_use)                                                       │
│  $(_ license_commercial)                                                     │
│                                                                             │
│  $(_ license_obligations):                                                    │
│  $(_ license_copyright)                                                      │
│  $(_ license_same_license)                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ $(_ risk_title)                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  $(_ risk_system)                                                            │
│     $(_ risk_system_detail)                                                  │
│     $(_ risk_selinux_detail)                                                 │
│     $(_ risk_config)                                                         │
│                                                                             │
│  $(_ risk_network)                                                           │
│     $(_ risk_network_detail)                                                 │
│     $(_ risk_repo)                                                           │
│     $(_ risk_ports)                                                          │
│                                                                             │
│  $(_ risk_data)                                                              │
│     $(_ risk_data_detail)                                                    │
│     $(_ risk_api_key)                                                        │
│     $(_ risk_backup)                                                         │
│                                                                             │
│  $(_ risk_disclaimer)                                                        │
│     $(_ risk_not_medical)                                                    │
│     $(_ risk_consult_doctor)                                                 │
│     $(_ risk_no_liability)                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

EOF

    local agreement
    read -p "$(_ agree_prompt)? [yes/no]: " agreement
    
    if [[ "$agreement" != "yes" && "$agreement" != "YES" ]]; then
        log_error "$(_ agree_reject)"
        exit 1
    fi
    
    log_success "$(_ agree_confirm)"
}

#==============================================================================
# Interactive Configuration
#==============================================================================

generate_jwt_secret() {
    openssl rand -base64 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1
}

collect_api_config() {
    log_step "$(_ api_config)"
    
    cat << EOF
┌─────────────────────────────────────────────────────────────────────────────┐
│ $(_ api_description)                                                         │
│                                                                             │
│  MediCare_AI requires AI model API for intelligent diagnosis.               │
│  Supports OpenAI-compatible APIs, such as:                                  │
│  - GLM-4.7-Flash (local deployment)                                         │
│  - OpenAI GPT series                                                        │
│  - Other OpenAI API compatible services                                     │
│                                                                             │
│  MinerU is used for document parsing, requires MinerU API token.            │
│                                                                             │
│  Tip: You can skip this step and edit .env file later.                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

EOF

    echo -e "${CYAN}$(_ api_ai_config)${NC}"
    read -p "  $(_ api_ai_url): " AI_API_URL
    
    if [[ -n "$AI_API_URL" ]]; then
        read -p "  $(_ api_ai_key): " AI_API_KEY
        read -p "  $(_ api_model_id): unsloth/GLM-4.7-Flash-GGUF:BF16]: " AI_MODEL_ID
        AI_MODEL_ID=${AI_MODEL_ID:-"unsloth/GLM-4.7-Flash-GGUF:BF16"}
    else
        log_warning "$(_ api_skip_warning)"
        AI_MODEL_ID="unsloth/GLM-4.7-Flash-GGUF:BF16"
    fi
    
    echo
    
    echo -e "${CYAN}$(_ api_mineru_config)${NC}"
    read -p "  $(_ api_mineru_token): " MINERU_TOKEN
    
    if [[ -z "$MINERU_TOKEN" ]]; then
        log_warning "$(_ api_skip_mineru)"
    fi
    
    JWT_SECRET_KEY=$(generate_jwt_secret)
    log_info "$(_ api_jwt_generated)"
}

prompt_network_config() {
    log_step "$(_ network_config)"
    
    cat << EOF
┌─────────────────────────────────────────────────────────────────────────────┐
│ $(_ network_type)                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  $(_ network_domain)                                                         │
│  $(_ network_lan)                                                            │
│  $(_ network_local)                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

EOF

    local choice
    read -p "$(_ network_choice) [1-3]: " choice
    
    case "$choice" in
        1)
            DEPLOYMENT_TYPE="domain"
            read -p "$(_ network_domain_input) (e.g., medicare.example.com): " DOMAIN_NAME
            if [[ -z "$DOMAIN_NAME" ]]; then
                exit_with_error "$(_ network_domain_empty)"
            fi
            log_success "$(_ network_domain_use): $DOMAIN_NAME"
            ;;
        2)
            DEPLOYMENT_TYPE="lan"
            local detected_ip
            detected_ip=$(hostname -I 2>/dev/null | awk '{print $1}' || ip route get 1 2>/dev/null | awk '{print $7}' | head -1)
            read -p "$(_ network_lan_input) [$(_ network_lan_default): $detected_ip]: " SERVER_IP
            SERVER_IP=${SERVER_IP:-$detected_ip}
            log_success "$(_ network_lan_use): $SERVER_IP"
            ;;
        3)
            DEPLOYMENT_TYPE="local"
            SERVER_IP="127.0.0.1"
            log_success "$(_ network_local_use): 127.0.0.1"
            ;;
        *)
            exit_with_error "$(_ network_invalid)"
            ;;
    esac
    
    echo
    log_info "$(_ network_port_info)"
    
    read -p "  $(_ network_http_port): 80]: " input_port
    HTTP_PORT=${input_port:-80}
    
    read -p "  $(_ network_https_port): 443]: " input_port
    HTTPS_PORT=${input_port:-443}
    
    read -p "  $(_ network_api_port): 8000]: " input_port
    API_PORT=${input_port:-8000}
    
    read -p "  $(_ network_frontend_port): 3000]: " input_port
    FRONTEND_PORT=${input_port:-3000}
    
    if [[ "$HTTP_PORT" -eq "$API_PORT" ]] || [[ "$HTTP_PORT" -eq "$FRONTEND_PORT" ]]; then
        exit_with_error "$(_ network_port_conflict)"
    fi
    
    log_success "$(_ network_complete)"
}

prompt_data_persistence() {
    log_step "$(_ data_config)"
    
    cat << EOF
┌─────────────────────────────────────────────────────────────────────────────┐
│ $(_ data_description)                                                        │
│                                                                             │
│  $(_ data_recommend)                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

EOF

    read -p "$(_ data_enable)? [Y/n]: " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        DATA_PERSISTENCE=false
        log_warning "$(_ data_disabled)"
    else
        DATA_PERSISTENCE=true
        log_success "$(_ data_enabled)"
    fi
}

prompt_cn_mirror() {
    log_step "$(_ mirror_config)"
    
    read -p "$(_ mirror_prompt)? [y/N]: " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        USE_CN_MIRROR=true
        log_success "$(_ mirror_enabled)"
    else
        USE_CN_MIRROR=false
    fi
}

#==============================================================================
# Docker Management
#==============================================================================

check_docker_installed() {
    if command -v docker &> /dev/null; then
        local docker_version
        docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
        log_info "$(_ docker_check): $docker_version"
        return 0
    else
        return 1
    fi
}

install_docker() {
    log_step "$(_ docker_install)"
    
    if check_docker_installed; then
        log_success "$(_ docker_skip)"
        return 0
    fi
    
    log_info "$(_ docker_installing)"
    
    case "$DISTRO_ID" in
        ubuntu|debian|deepin)
            sudo apt-get update
            sudo apt-get install -y docker.io
            ;;
        fedora)
            sudo dnf install -y docker
            ;;
        opensuse-leap|opensuse-tumbleweed)
            sudo zypper install -y docker
            ;;
        aosc)
            sudo apt install -y docker
            ;;
        openeuler)
            sudo dnf install -y docker
            ;;
        *)
            exit_with_error "$(_ unsupported_distro): $DISTRO_ID"
            ;;
    esac
    
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker "$USER" 2>/dev/null || true
    
    log_success "$(_ docker_complete)"
}

check_docker_compose_version() {
    if command -v docker-compose &> /dev/null; then
        local version_output
        version_output=$(docker-compose version --short 2>/dev/null || docker-compose version 2>/dev/null | head -1)
        
        if [[ "$version_output" =~ ^1\. ]]; then
            log_warning "$(_ compose_upgrade): $version_output"
            return 1
        elif [[ "$version_output" =~ ^2\. ]]; then
            log_success "$(_ compose_check_v2): $version_output"
            return 0
        fi
    fi
    
    if docker compose version &> /dev/null; then
        log_success "$(_ compose_check_v2)"
        return 0
    fi
    
    return 1
}

install_docker_compose_v2() {
    log_step "$(_ compose_install)"
    
    if check_docker_compose_version && [[ "$NEEDS_DOCKER_COMPOSE_UPGRADE" == false ]]; then
        log_success "$(_ compose_check_v2)"
        return 0
    fi
    
    log_info "$(_ compose_installing)"
    
    if [[ "$DISTRO_ID" == "openeuler" ]] || [[ "$DISTRO_ID" == "deepin" ]]; then
        case "$DISTRO_ID" in
            openeuler)
                sudo dnf remove -y docker-compose 2>/dev/null || true
                ;;
            deepin|ubuntu|debian|aosc)
                sudo apt-get remove -y docker-compose 2>/dev/null || true
                ;;
        esac
    fi
    
    local compose_url="https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64"
    
    if [[ "$USE_CN_MIRROR" == true ]]; then
        compose_url="https://mirrors.tuna.tsinghua.edu.cn/github-release/docker/compose/v2.24.0/docker-compose-linux-x86_64"
    fi
    
    sudo curl -fsSL "$compose_url" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    hash -r
    
    if docker-compose version &> /dev/null; then
        log_success "$(_ compose_complete): $(docker-compose version --short)"
    else
        exit_with_error "$(_ compose_fail)"
    fi
}

configure_selinux() {
    if [[ "$SELINUX_ENABLED" == false ]]; then
        return 0
    fi
    
    log_step "$(_ selinux_config)"
    
    if ! command -v getenforce &> /dev/null; then
        log_warning "$(_ selinux_not_installed)"
        return 0
    fi
    
    local selinux_status
    selinux_status=$(getenforce 2>/dev/null || echo "Disabled")
    
    if [[ "$selinux_status" == "Enforcing" ]]; then
        log_warning "$(_ selinux_enforcing)"
        log_info "$(_ selinux_set_permissive)"
        
        sudo setenforce 0
        sudo sed -i 's/SELINUX=enforcing/SELINUX=permissive/' /etc/selinux/config 2>/dev/null || true
        
        log_success "$(_ selinux_complete)"
    else
        log_info "$(_ selinux_status): $selinux_status"
    fi
}

test_docker() {
    log_step "$(_ docker_test)"
    
    if ! sudo docker run --rm hello-world &> /dev/null; then
        exit_with_error "$(_ docker_test_fail)"
    fi
    
    log_success "$(_ docker_test_ok)"
}

#==============================================================================
# Configuration Generation
#==============================================================================

generate_env_file() {
    log_step "$(_ gen_env)"
    
    local env_file="$SCRIPT_DIR/.env"
    local postgres_password
    local redis_password
    
    postgres_password=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
    redis_password=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
    
    cat > "$env_file" << EOF
# MediCare_AI Environment Configuration
# Generated: $(date)

# Database Configuration
POSTGRES_PASSWORD=$postgres_password
DATABASE_URL=postgresql+asyncpg://medicare_user:${postgres_password}@medicare_postgres:5432/medicare_ai

# Redis Configuration
REDIS_PASSWORD=$redis_password
REDIS_URL=redis://:${redis_password}@medicare_redis:6379/0

# JWT Secret
JWT_SECRET_KEY=${JWT_SECRET_KEY}

# MinerU Configuration
MINERU_TOKEN=${MINERU_TOKEN}

# AI Service Configuration
AI_API_KEY=${AI_API_KEY}
AI_API_URL=${AI_API_URL}
AI_MODEL_ID=${AI_MODEL_ID:-unsloth/GLM-4.7-Flash-GGUF:BF16}

# Deployment Configuration
DEPLOYMENT_TYPE=${DEPLOYMENT_TYPE}
DOMAIN_NAME=${DOMAIN_NAME}
SERVER_IP=${SERVER_IP}

# Port Configuration
HTTP_PORT=${HTTP_PORT}
HTTPS_PORT=${HTTPS_PORT}
API_PORT=${API_PORT}
FRONTEND_PORT=${FRONTEND_PORT}
POSTGRES_PORT=${POSTGRES_PORT}
REDIS_PORT=${REDIS_PORT}

# Other Configuration
DEBUG=false
USE_CN_MIRROR=${USE_CN_MIRROR}
EOF

    log_success "$(_ gen_env_complete): $env_file"
    chmod 600 "$env_file"
}

update_docker_compose() {
    log_step "$(_ gen_compose_update)"
    
    local compose_file="$SCRIPT_DIR/docker-compose.yml"
    
    if [[ ! -f "$compose_file" ]]; then
        exit_with_error "docker-compose.yml not found"
    fi
    
    cp "$compose_file" "${compose_file}.backup.$(date +%Y%m%d)"
    
    if [[ "$HTTP_PORT" != "80" ]]; then
        log_info "$(_ gen_port_update) HTTP: $HTTP_PORT"
        sudo sed -i "s/\"80:80\"/\"${HTTP_PORT}:80\"/g" "$compose_file"
    fi
    
    if [[ "$HTTPS_PORT" != "443" ]]; then
        log_info "$(_ gen_port_update) HTTPS: $HTTPS_PORT"
        sudo sed -i "s/\"443:443\"/\"${HTTPS_PORT}:443\"/g" "$compose_file"
    fi
    
    if [[ "$DATA_PERSISTENCE" == false ]]; then
        log_warning "$(_ gen_data_disable)"
    fi
    
    log_success "$(_ gen_compose_complete)"
}

#==============================================================================
# Deployment
#==============================================================================

pull_images() {
    log_step "$(_ deploy_pull)"
    
    log_info "$(_ deploy_pull_postgres)"
    sudo docker pull postgres:17-alpine
    
    log_info "$(_ deploy_pull_redis)"
    sudo docker pull redis:7.4-alpine
    
    log_info "$(_ deploy_pull_nginx)"
    sudo docker pull nginx:alpine
    
    log_success "$(_ deploy_pull_complete)"
}

deploy_services() {
    log_step "$(_ deploy_build)"
    
    local compose_file="$SCRIPT_DIR/docker-compose.yml"
    
    export DOCKER_BUILDKIT=${BUILDKIT_ISSUE:+0}
    
    log_info "$(_ deploy_building)"
    sudo docker-compose -f "$compose_file" build --no-cache
    
    log_info "$(_ deploy_starting)"
    sudo docker-compose -f "$compose_file" up -d
    
    log_success "$(_ deploy_complete)"
}

wait_for_services() {
    log_step "Waiting for Services"
    
    log_info "$(_ wait_postgres)"
    local attempts=0
    while [[ $attempts -lt 30 ]]; do
        if sudo docker exec medicare_postgres pg_isready -U medicare_user &> /dev/null; then
            log_success "PostgreSQL $(_ wait_ready)"
            break
        fi
        sleep 2
        attempts=$((attempts + 1))
        echo -n "."
    done
    
    if [[ $attempts -eq 30 ]]; then
        log_warning "$(_ wait_timeout)"
    fi
    
    log_info "$(_ wait_backend)"
    sleep 5
    
    log_success "$(_ wait_init_complete)"
}

health_check() {
    log_step "$(_ health_check)"
    
    local api_url="http://localhost:$API_PORT"
    
    log_info "$(_ health_api_check)"
    local attempts=0
    while [[ $attempts -lt 10 ]]; do
        if curl -sf "$api_url/health" &> /dev/null; then
            log_success "$(_ health_api_ok)"
            break
        fi
        sleep 3
        attempts=$((attempts + 1))
        echo -n "."
    done
    
    if [[ $attempts -eq 10 ]]; then
        log_warning "$(_ health_timeout)"
    fi
    
    echo
    log_info "$(_ health_container_status):"
    sudo docker-compose ps
}

#==============================================================================
# Completion
#==============================================================================

display_completion_info() {
    log_step "$(_ complete_title)"
    
    local access_url
    
    cat << EOF

╔═══════════════════════════════════════════════════════════════════════════╗
║                     $(_ complete_title)                      ║
╚═══════════════════════════════════════════════════════════════════════════╝

$(_ complete_access):
EOF

    if [[ "$DEPLOYMENT_TYPE" == "domain" ]]; then
        access_url="http://$DOMAIN_NAME:$HTTP_PORT"
        echo "  $(_ complete_frontend): http://$DOMAIN_NAME:$HTTP_PORT"
        echo "  $(_ complete_api): http://$DOMAIN_NAME:$API_PORT"
    elif [[ "$DEPLOYMENT_TYPE" == "lan" ]]; then
        access_url="http://$SERVER_IP:$HTTP_PORT"
        echo "  $(_ complete_frontend): http://$SERVER_IP:$HTTP_PORT"
        echo "  $(_ complete_api): http://$SERVER_IP:$API_PORT"
    else
        access_url="http://127.0.0.1:$HTTP_PORT"
        echo "  $(_ complete_frontend): http://127.0.0.1:$HTTP_PORT"
        echo "  $(_ complete_api): http://127.0.0.1:$API_PORT"
    fi
    
    cat << EOF

$(_ complete_service_ports):
  - $(_ complete_http):     $HTTP_PORT
  - $(_ complete_https):    $HTTPS_PORT
  - $(_ complete_api_port):      $API_PORT
  - $(_ complete_frontend_port): $FRONTEND_PORT
  - $(_ complete_postgres):  $POSTGRES_PORT
  - $(_ complete_redis):     $REDIS_PORT

$(_ complete_commands):
  $(_ complete_cmd_logs):   sudo docker-compose logs -f
  $(_ complete_cmd_stop):   sudo docker-compose down
  $(_ complete_cmd_restart): sudo docker-compose restart
  $(_ complete_cmd_status): sudo docker-compose ps

$(_ complete_config_files):
  - $(_ complete_env): $SCRIPT_DIR/.env
  - $(_ complete_docker):   $SCRIPT_DIR/docker-compose.yml

$(_ complete_next_steps):
  $(_ complete_skip_config)

$(_ complete_log_file): $LOG_FILE

EOF

    log_success "$(_ complete_finished)! $(_ complete_visit): $access_url"
}

#==============================================================================
# Main Function
#==============================================================================
main() {
    # Initialize translations
    init_translations
    
    # Language selection
    select_language
    
    # Display welcome
    display_welcome
    
    # System checks
    check_admin_privileges
    detect_distro
    check_system_requirements
    
    # User agreement
    prompt_user_agreement
    
    # Interactive configuration
    collect_api_config
    prompt_network_config
    prompt_data_persistence
    prompt_cn_mirror
    
    # Environment preparation
    install_docker
    install_docker_compose_v2
    configure_selinux
    test_docker
    
    # Generate configurations
    generate_env_file
    update_docker_compose
    
    # Deploy services
    pull_images
    deploy_services
    wait_for_services
    health_check
    
    # Completion
    display_completion_info
}

# Run main function
main "$@"
