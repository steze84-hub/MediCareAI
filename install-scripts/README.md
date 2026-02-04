# Install Scripts | 安装脚本

This directory contains auxiliary installation scripts for MediCare_AI.

本目录包含 MediCare_AI 的辅助安装脚本。

## 🚀 Main Installation Script | 主安装脚本

**For most users, use the main installation script in the project root:**

**大多数用户请使用项目根目录的主安装脚本：**

```bash
cd /path/to/MediCare_AI
sudo ./install.sh
```

The main `install.sh` script supports:
- **Multi-Language**: Chinese (简体中文) and English
- **7 Linux Distributions**: Ubuntu, Fedora, openSUSE, AOSC OS, openEuler, Deepin
- **Interactive Configuration**: AI API setup, network configuration, custom ports
- **Auto-Configuration**: Docker, Docker Compose, SELinux, BuildKit handling

主安装脚本 `install.sh` 支持：
- **多语言**: 中文和英文
- **7个Linux发行版**: Ubuntu、Fedora、openSUSE、AOSC OS、openEuler、Deepin
- **交互式配置**: AI API设置、网络配置、自定义端口
- **自动配置**: Docker、Docker Compose、SELinux、BuildKit处理

## 📁 Auxiliary Scripts | 辅助脚本

| Script | Purpose | Usage |
|--------|---------|-------|
| `generate-test-key.sh` | Generate test JWT secret | `./generate-test-key.sh` |
| `setup-selinux.sh` | Configure SELinux for Docker | `sudo ./setup-selinux.sh` |
| `enable-password-auth.sh` | Enable SSH password auth | `sudo ./enable-password-auth.sh` |

## 📖 Full Documentation | 完整文档

See the main project documentation:
- [README.md](../README.md) - Project overview and quick start
- [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md) - Detailed deployment guide
- [CHANGELOG.md](../CHANGELOG.md) - Version history

查看主项目文档：
- [README.md](../README.md) - 项目概览和快速开始
- [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md) - 详细部署指南
- [CHANGELOG.md](../CHANGELOG.md) - 版本历史
