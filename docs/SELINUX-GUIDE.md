# SELinux 优雅配置指南

## 概述

本文档介绍如何在 **不关闭 SELinux** 的情况下，优雅地配置 MediCare_AI 在 Fedora 43 上的 SELinux 策略。

## 核心原则

✅ **不关闭 SELinux** - 保持 `Enforcing` 模式  
✅ **遵循最小权限原则** - 仅授予必要的权限  
✅ **使用标准工具** - `semanage`, `restorecon`, `ausearch`  
✅ **持久化配置** - 使用 SELinux 策略文件，非临时修改

---

## 快速配置

### 一键配置脚本

```bash
sudo bash install-scripts/setup-selinux.sh /opt/medicare-ai
```

### 手动配置步骤

#### 1. 检查 SELinux 状态

```bash
# 查看当前模式
getenforce
# 输出: Enforcing

# 查看详细状态
sestatus
```

#### 2. 安装 container-selinux

```bash
sudo dnf install -y container-selinux
```

#### 3. 配置文件上下文规则

```bash
# 添加持久化规则
sudo semanage fcontext -a -t container_file_t '/opt/medicare-ai(/.*)?'

# 应用规则到现有文件
sudo restorecon -Rv /opt/medicare-ai/
```

#### 4. 验证配置

```bash
# 检查文件上下文
ls -laZ /opt/medicare-ai/

# 预期输出:
# drwxr-xr-x. 12 houge houge unconfined_u:object_r:container_file_t:s0  4096  2月 3日 11:03 .
```

---

## 配置详解

### 文件上下文类型

| 类型 | 用途 | 适用场景 |
|------|------|----------|
| `container_file_t` | 容器文件 | 被容器访问的宿主机文件 |
| `usr_t` | 用户文件 | 普通用户数据文件 |
| `default_t` | 默认类型 | 未分类文件 |

### 为什么选择 `container_file_t`

1. **专为容器设计** - Docker 容器可以读取和写入
2. **安全隔离** - 与其他系统文件隔离
3. **标准类型** - 被 container-selinux 包支持

### SELinux 规则持久化

```bash
# 查看已配置的规则
sudo semanage fcontext -l | grep medicare-ai

# 输出示例:
/opt/medicare-ai(/.*)?    all files    system_u:object_r:container_file_t:s0
```

---

## Docker 与 SELinux

### Docker 守护进程配置

Fedora 上的 Docker 默认启用 SELinux 支持，无需额外配置。

验证：
```bash
docker info | grep -i selinux
# 输出: Security Options: seccomp, selinux
```

### 卷挂载的 SELinux 标签

Docker 提供两种 SELinux 卷标签：

| 标签 | 含义 | 使用场景 |
|------|------|----------|
| `:z` | 共享标签 | 多个容器共享数据 |
| `:Z` | 私有标签 | 单容器独占数据 |

示例：
```bash
# 使用共享标签（推荐用于前端静态文件）
docker run -v /opt/medicare-ai/frontend:/usr/share/nginx/html:z nginx:alpine

# 使用私有标签（用于敏感数据）
docker run -v /opt/medicare-ai/data:/data:Z myapp
```

**注意**：使用 `:z` 或 `:Z` 时，Docker 会自动重新标记文件上下文。

---

## 故障排查

### 检查 SELinux 拒绝日志

```bash
# 查看最近的 SELinux 拒绝
sudo ausearch -m avc -ts recent

# 查看特定时间段的日志
sudo ausearch -m avc -ts today

# 查看详细日志
sudo cat /var/log/audit/audit.log | grep denied
```

### 生成允许规则（audit2allow）

如果发现有合理的 SELinux 拒绝：

```bash
# 生成允许模块
sudo ausearch -m avc -ts recent | audit2allow -M mypol

# 安装模块
sudo semodule -i mypol.pp
```

### 临时调试（仅用于诊断）

```bash
# 临时切换到宽容模式（不推荐长期使用）
sudo setenforce 0

# 测试应用
# ...

# 恢复强制模式
sudo setenforce 1
```

---

## 最佳实践

### 1. 目录权限管理

```bash
# 项目根目录
sudo chown -R houge:houge /opt/medicare-ai
sudo chmod 755 /opt/medicare-ai

# uploads 目录（容器写入）
sudo chmod 755 /opt/medicare-ai/backend/uploads
sudo chown houge:houge /opt/medicare-ai/backend/uploads

# 应用 SELinux 上下文
sudo restorecon -Rv /opt/medicare-ai/
```

### 2. 监控 SELinux 日志

创建日志监控脚本：

```bash
#!/bin/bash
# monitor-selinux.sh

while true; do
    if sudo ausearch -m avc -ts recent 2>/dev/null | grep -q "denied"; then
        echo "$(date): 发现 SELinux 拒绝"
        sudo ausearch -m avc -ts recent | tail -5
    fi
    sleep 60
done
```

### 3. 定期验证

```bash
#!/bin/bash
# verify-selinux.sh

echo "=== SELinux 验证 ==="
echo ""
echo "1. SELinux 模式: $(getenforce)"
echo ""
echo "2. Docker SELinux 支持:"
docker info 2>/dev/null | grep -i selinux
echo ""
echo "3. 文件上下文检查:"
ls -laZ /opt/medicare-ai/ | head -3
echo ""
echo "4. 最近的 SELinux 拒绝:"
sudo ausearch -m avc -ts recent 2>/dev/null | wc -l | xargs echo "拒绝次数:"
```

---

## Fedora 43 特定说明

### 默认 SELinux 策略

Fedora 43 默认启用 `targeted` 策略：

```bash
$ sestatus
SELinux status:                 enabled
SELinuxfs mount:                /sys/fs/selinux
SELinux root directory:         /etc/selinux
Loaded policy name:             targeted
Current mode:                   enforcing
Mode from config file:          enforcing
Policy MLS status:              enabled
Policy deny_unknown status:     allowed
Memory protection checking:     actual (secure)
Max kernel policy version:      33
```

### 与 Ubuntu 的区别

| 特性 | Fedora 43 | Ubuntu 24.04 |
|------|-----------|--------------|
| 默认 SELinux | Enforcing | 无（AppArmor） |
| 策略类型 | targeted | 无 |
| container-selinux | 预装或需安装 | 需安装 |

---

## 验证清单

部署后验证 SELinux 配置：

- [ ] SELinux 模式为 `Enforcing`
- [ ] 文件上下文为 `container_file_t`
- [ ] 容器可以读取前端文件
- [ ] 容器可以写入 uploads 目录
- [ ] 无 SELinux 拒绝日志
- [ ] 所有服务正常运行

---

## 命令速查表

```bash
# 查看 SELinux 状态
getenforce
sestatus

# 查看文件上下文
ls -laZ /path/to/file

# 修改文件上下文
sudo chcon -t container_file_t /path/to/file

# 添加持久化规则
sudo semanage fcontext -a -t container_file_t '/path(/.*)?'

# 应用上下文规则
sudo restorecon -Rv /path

# 查看 SELinux 日志
sudo ausearch -m avc -ts recent
sudo cat /var/log/audit/audit.log | grep denied

# 查看 SELinux 布尔值
getsebool -a | grep docker

# 设置 SELinux 布尔值
sudo setsebool -P docker_connect_any on
```

---

## 参考资源

- [SELinux Project Wiki](https://selinuxproject.org)
- [Fedora SELinux Guide](https://docs.fedoraproject.org/en-US/fedora/latest/system-administrators-guide/selinux/)
- [Docker SELinux Security](https://docs.docker.com/engine/security/selinux/)
- [container-selinux GitHub](https://github.com/containers/container-selinux)

---

## 总结

通过正确配置 SELinux 文件上下文规则，我们实现了：

1. ✅ **零妥协安全** - 保持 SELinux Enforcing 模式
2. ✅ **容器兼容** - Docker 容器正常访问文件
3. ✅ **持久化配置** - 规则保存在 SELinux 策略中
4. ✅ **优雅管理** - 使用标准工具，无临时绕过

**关键命令**：
```bash
sudo semanage fcontext -a -t container_file_t '/opt/medicare-ai(/.*)?'
sudo restorecon -Rv /opt/medicare-ai/
```

这样配置后，MediCare_AI 在 Fedora 43 上既安全又功能完整。
