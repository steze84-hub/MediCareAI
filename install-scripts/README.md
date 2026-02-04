# MediCare_AI Installation Scripts

## 🎉 重要更新: 统一一键部署脚本

我们很高兴地宣布，**统一一键部署脚本 `../install.sh`** 现已可用！

这个新脚本支持 **7 个 Linux 发行版**，提供完全交互式的部署体验，**支持中英文双语**！

### 支持的发行版

- Ubuntu 24.04 LTS
- Fedora 43 Server
- openSUSE Leap 16.0
- openSUSE Tumbleweed
- AOSC OS 13.0.7
- openEuler 24.03 LTS-SP3
- Deepin 25

### 多语言支持

脚本启动时会显示语言选择菜单：

```
[LANGUAGE / 语言] Please select language / 请选择语言

  1. 中文 (Chinese)
  2. English
  3. Auto-detect / 自动检测
```

- **中文**: 完整的简体中文界面
- **English**: Full English interface
- **Auto-detect**: 自动检测系统语言

### 快速开始

```bash
# 克隆项目
git clone https://github.com/HougeLangley/MediCareAI.git
cd MediCareAI

# 运行一键部署脚本
sudo ./install.sh
```

### 脚本特性

- ✅ **多语言支持**: 中文 / English
- ✅ **发行版自动检测**: 支持 7 个 Linux 发行版
- ✅ **交互式配置**: API 配置、网络设置、端口自定义
- ✅ **用户协议**: 开源协议和风险提示确认
- ✅ **智能安装**: 自动安装 Docker 和 Docker Compose v2
- ✅ **兼容性处理**: 自动处理 SELinux、BuildKit 等
- ✅ **配置生成**: 自动生成 .env 和 docker-compose 配置
- ✅ **健康检查**: 部署完成后自动验证服务状态

详细文档请参阅 [./install.sh](../install.sh)

---

This directory contains installation scripts and documentation for deploying MediCare_AI on various Linux distributions.

## Available Scripts

### 统一部署脚本 (推荐)
- **Script**: `../install.sh` (项目根目录)
- **Status**: ✅ 支持 7 个发行版
- **Features**:
  - 自动检测发行版
  - 交互式配置（API、网络、端口）
  - 用户协议确认
  - 自动处理 SELinux/BuildKit
  - 自动生成配置文件
  - 健康检查

### 单独发行版脚本

#### Ubuntu 24.04 LTS
- **Script**: `install-ubuntu-2404.sh`
- **Guide**: `UBUNTU-2404-INSTALL-GUIDE.md`
- **Status**: ✅ 已测试

#### Fedora 43
- **Script**: `install-fedora-43.sh`
- **Report**: `FEDORA-43-TEST-REPORT.md`
- **Status**: ✅ 已测试

### 测试报告

| 发行版 | 测试报告 | 状态 |
|--------|----------|------|
| Ubuntu 24.04 LTS | `UBUNTU-2404-TEST-RESULTS.md` | ✅ 通过 |
| Fedora 43 | `FEDORA-43-TEST-REPORT.md` | ✅ 通过 |
| openSUSE Leap 16.0 | `OPENSUSE-16-DEPLOYMENT-COMPLETE.md` | ✅ 通过 |
| openSUSE Tumbleweed | `TUMBLEWEED-ONLINE-DEPLOYMENT-SUCCESS.md` | ✅ 通过 |
| AOSC OS 13.0.7 | `AOSC-OS-DEPLOYMENT-SUCCESS.md` | ✅ 通过 |
| openEuler 24.03 LTS-SP3 | `openeuler-online-deployment-success.md` | ✅ 通过 |
| Deepin 25 | `deepin-25-online-deployment-success.md` | ✅ 通过 |

## System Requirements

### Minimum Requirements
- CPU: 2 cores
- RAM: 4 GB
- Storage: 20 GB
- Network: Internet connection

### Recommended Requirements
- CPU: 4+ cores
- RAM: 8+ GB
- Storage: 50+ GB SSD

## Testing Matrix

| Distribution | Version | Status | IP | Notes |
|-------------|---------|--------|-----|-------|
| Ubuntu | 24.04 LTS | ✅ Tested | 192.168.50.195 | 最简单 |
| Fedora | 43 Server | ✅ Tested | 192.168.50.145 | SELinux |
| openSUSE Leap | 16.0 | ✅ Tested | 192.168.50.221 | SELinux |
| openSUSE Tumbleweed | Rolling | ✅ Tested | 192.168.50.20 | BuildKit |
| AOSC OS | 13.0.7 | ✅ Tested | 192.168.50.219 | Docker 手动安装 |
| openEuler | 24.03 LTS-SP3 | ✅ Tested | 192.168.50.92 | docker-compose 升级 |
| Deepin | 25 | ✅ Tested | 192.168.50.220 | Docker Compose v2 |

## Common Issues

### Docker Permission Denied
After installation, you may need to log out and log back in for Docker group membership to take effect.

```bash
# Or use this command to apply changes without logout
newgrp docker
```

### Port Conflicts
If ports 80, 443, 8000, or 3000 are already in use, the install script allows you to customize ports interactively.

### Docker Compose Compatibility
Some distributions ship with Docker Compose v1 which has compatibility issues. The unified `install.sh` script automatically upgrades to v2.

## Contributing

To add support for a new distribution:

1. Test deployment manually
2. Create `<DISTRO>-<VERSION>-DEPLOYMENT-SUCCESS.md` test report
3. Update `../docs/SUPPORTED-DISTROS.md`
4. Test with unified `install.sh` script
5. Submit PR

## License

Same as MediCare_AI project (MIT License)

## Support

For issues or questions:
- Review the test reports in this directory
- Check the distribution-specific guide
- Open an issue on GitHub

---

**Note**: Use the unified `../install.sh` script for new deployments. The individual scripts in this directory are kept for reference and advanced customization.
