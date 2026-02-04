# MediCare_AI One-Click Deployment Script | 一键部署脚本

## 🌍 Multi-Language Support | 多语言支持

This script supports **Chinese (简体中文)** and **English**!

脚本支持 **中文** 和 **英文**！

When you run the script, you will see a language selection menu:

运行脚本时，会显示语言选择菜单：

```
[LANGUAGE / 语言] Please select language / 请选择语言

  1. 中文 (Chinese)
  2. English
  3. Auto-detect / 自动检测

>>> Enter choice / 输入选项 [1-3]:
```

---

## 🚀 Quick Start | 快速开始

### For English Users

```bash
# Clone the repository
git clone https://github.com/HougeLangley/MediCareAI.git
cd MediCareAI

# Run the installation script
sudo ./install.sh

# Select "2. English" when prompted for language
```

### 中文用户

```bash
# 克隆项目
git clone https://github.com/HougeLangley/MediCareAI.git
cd MediCareAI

# 运行安装脚本
sudo ./install.sh

# 在语言选择时输入 "1" 选择中文
```

---

## ✨ Features | 功能特性

### English
- **Multi-Language**: Full English and Chinese (简体中文) support
- **7 Linux Distributions**: Ubuntu, Fedora, openSUSE, AOSC OS, openEuler, Deepin
- **Interactive Configuration**: AI API setup, network configuration, custom ports
- **User Agreement**: Open source license and risk acknowledgment
- **Smart Installation**: Auto-install Docker and Docker Compose v2
- **Compatibility**: Auto-handle SELinux, BuildKit, and version compatibility
- **Auto-Configuration**: Generate .env and docker-compose configurations
- **Health Check**: Verify services after deployment

### 中文
- **多语言支持**: 完整的英文和简体中文界面
- **7个Linux发行版**: Ubuntu、Fedora、openSUSE、AOSC OS、openEuler、Deepin
- **交互式配置**: AI API 设置、网络配置、自定义端口
- **用户协议**: 开源协议和风险确认
- **智能安装**: 自动安装 Docker 和 Docker Compose v2
- **兼容性处理**: 自动处理 SELinux、BuildKit 和版本兼容性
- **自动生成配置**: 生成 .env 和 docker-compose 配置
- **健康检查**: 部署后自动验证服务状态

---

## 📋 Deployment Process | 部署流程

### 1. Language Selection | 语言选择
```
[LANGUAGE / 语言] Please select language / 请选择语言
  1. 中文 (Chinese)
  2. English
  3. Auto-detect / 自动检测
```

### 2. System Detection | 系统检测
- Detect Linux distribution | 检测 Linux 发行版
- Check administrator privileges | 检查管理员权限
- Verify system requirements | 验证系统要求

### 3. User Agreement | 用户协议
- MIT License | MIT 开源协议
- Risk acknowledgment | 风险提示
- Agreement confirmation | 协议确认

### 4. Interactive Configuration | 交互式配置

#### AI Service Configuration | AI 服务配置
- AI API URL (optional) | AI API 地址（可选）
- AI API Key (optional) | AI API 密钥（可选）
- AI Model ID (default: GLM-4.7-Flash) | AI 模型 ID
- MinerU Token (optional) | MinerU 令牌（可选）

#### Network Configuration | 网络配置
- **Domain deployment** | 域名部署
- **LAN IP deployment** | 局域网 IP 部署
- **Local test mode** | 本地测试模式

#### Port Configuration | 端口配置
- HTTP Port (default: 80) | HTTP 端口
- HTTPS Port (default: 443) | HTTPS 端口
- API Port (default: 8000) | API 端口
- Frontend Port (default: 3000) | 前端端口

#### Data Persistence | 数据持久化
- Enable/disable data persistence | 启用/禁用数据持久化
- Docker volume configuration | Docker 卷配置

### 5. Environment Preparation | 环境准备
- Install Docker | 安装 Docker
- Install/Upgrade Docker Compose v2 | 安装/升级 Docker Compose v2
- Configure SELinux (Fedora/openSUSE) | 配置 SELinux
- Handle BuildKit (Tumbleweed) | 处理 BuildKit

### 6. Deployment | 部署
- Pull base images | 拉取基础镜像
- Build application images | 构建应用镜像
- Start all services | 启动所有服务
- Health check | 健康检查

### 7. Completion | 完成
- Display access URLs | 显示访问地址
- Show management commands | 显示管理命令
- Configuration file locations | 配置文件位置

---

## 🐧 Supported Distributions | 支持的发行版

| Distribution | Version | Package Manager | Special Notes |
|-------------|---------|----------------|---------------|
| Ubuntu | 24.04 LTS | apt | Easiest deployment |
| Fedora | 43 Server | dnf | SELinux auto-config |
| openSUSE Leap | 16.0 | zypper | SELinux auto-config |
| openSUSE Tumbleweed | Rolling | zypper | BuildKit auto-disable |
| AOSC OS | 13.0.7 | apt (oma) | Docker manual install |
| openEuler | 24.03 LTS-SP3 | dnf | Docker Compose v2 upgrade |
| Deepin | 25 | apt | Docker Compose v2 upgrade |

---

## ⚙️ Configuration Files | 配置文件

### Generated .env file | 生成的 .env 文件
```bash
# Database | 数据库
POSTGRES_PASSWORD=<random>
DATABASE_URL=postgresql+asyncpg://...

# Redis
REDIS_PASSWORD=<random>
REDIS_URL=redis://...

# JWT Secret | JWT 密钥
JWT_SECRET_KEY=<random>

# AI Service | AI 服务
AI_API_KEY=your_api_key
AI_API_URL=your_api_url
AI_MODEL_ID=unsloth/GLM-4.7-Flash-GGUF:BF16

# MinerU
MINERU_TOKEN=your_token
```

---

## 🛠️ Management Commands | 管理命令

```bash
# View logs | 查看日志
sudo docker-compose logs -f

# Stop services | 停止服务
sudo docker-compose down

# Restart services | 重启服务
sudo docker-compose restart

# Check status | 查看状态
sudo docker-compose ps

# Access backend shell | 进入后端容器
sudo docker-compose exec backend bash

# Access database | 进入数据库
sudo docker-compose exec postgres psql -U medicare_user -d medicare_ai
```

---

## 🔧 Troubleshooting | 故障排除

### Docker Compose Version Issues | Docker Compose 版本问题

Some distributions ship with Docker Compose v1 which is incompatible with newer Docker versions. The script automatically upgrades to v2.

某些发行版自带的 Docker Compose v1 与新版本 Docker 不兼容。脚本会自动升级到 v2。

### SELinux Issues (Fedora/openSUSE) | SELinux 问题

The script automatically sets SELinux to permissive mode. For production, consider configuring proper Docker SELinux policies.

脚本会自动将 SELinux 设置为 permissive 模式。生产环境建议配置正确的 Docker SELinux 策略。

### BuildKit Issues (Tumbleweed) | BuildKit 问题

openSUSE Tumbleweed has BuildKit compatibility issues. The script automatically disables BuildKit.

openSUSE Tumbleweed 有 BuildKit 兼容性问题。脚本会自动禁用 BuildKit。

---

## 📄 License | 许可证

MIT License

---

**Version | 版本**: 1.0.3  
**Date | 日期**: 2026-02-04  
**Languages | 语言**: English / 简体中文
