# openSUSE Tumbleweed 在线部署测试报告

**日期**: 2026-02-04  
**目标**: openSUSE Tumbleweed (192.168.50.20)  
**状态**: ✅ 在线部署成功

---

## 部署结果

### 容器状态

| 容器 | 状态 | 端口 |
|------|------|------|
| medicare_nginx | ✅ Up | 80, 443 |
| medicare_backend | ✅ Up | 8000 |
| medicare_postgres | ✅ Healthy | 5432 |
| medicare_redis | ✅ Up | 6379 |
| medicare_frontend | ✅ Up | 3000 |

### 健康检查

```json
{
  "status": "healthy",
  "service": "MediCare_AI API",
  "version": "1.0.0",
  "python_version": "3.12.12",
  "environment": "production"
}
```

### 访问地址

- **Web UI**: http://192.168.50.20/
- **API Docs**: http://192.168.50.20:8000/docs
- **Health**: http://192.168.50.20:8000/health

---

## 关键发现

### 问题：Docker BuildKit 兼容性 ⚠️

**现象**:
```
ERROR: unable to fetch descriptor (sha256:...)
which reports content size of zero: invalid argument
```

**影响**: BuildKit 构建器在 Tumbleweed 上无法正常工作

**解决方案**:
```bash
# 禁用 BuildKit，使用旧版构建器
export DOCKER_BUILDKIT=0
docker compose up -d
```

**状态**: ✅ 已解决

---

## 部署步骤

### 完整在线部署流程

```bash
# 1. 进入项目目录
cd /opt/medicare-ai

# 2. 设置环境变量（禁用 BuildKit）
export DOCKER_BUILDKIT=0

# 3. 在线构建并启动
docker compose up --build -d

# 4. 验证部署
curl http://localhost:8000/health
docker ps
```

---

## 性能数据

| 指标 | 数值 |
|------|------|
| Docker Hub 拉取 | <5s |
| apt-get update | ~15s |
| pip install | ~40s |
| 总构建时间 | ~3分钟 |
| 容器启动时间 | <10s |

---

## 兼容性说明

### ✅ 已验证

- Docker 28.5.1-ce
- Docker Compose 5.0.2
- overlay2 存储驱动
- 旧版构建器（legacy builder）

### ⚠️ 注意事项

- **必须使用旧版构建器**: `DOCKER_BUILDKIT=0`
- **BuildKit 存在问题**: 无法解析镜像 metadata
- **Rolling Release**: 软件版本更新频繁，需定期测试

---

## 一键脚本适配建议

### 构建器自动检测

```bash
#!/bin/bash

# 检测是否需要禁用 BuildKit
detect_buildkit() {
    # 测试 BuildKit 是否可用
    if ! docker buildx version &>/dev/null; then
        echo "BuildKit 不可用，使用旧版构建器"
        export DOCKER_BUILDKIT=0
        return
    fi
    
    # 测试简单构建
    if ! echo 'FROM alpine:latest' | docker build -t test-buildkit - &>/dev/null 2>&1; then
        echo "BuildKit 测试失败，使用旧版构建器"
        export DOCKER_BUILDKIT=0
        docker rmi test-buildkit 2>/dev/null || true
        return
    fi
    
    docker rmi test-buildkit 2>/dev/null || true
    echo "BuildKit 正常工作"
}

# 主函数
main() {
    detect_buildkit
    docker compose up --build -d
}

main "$@"
```

---

## 加入支持列表

openSUSE Tumbleweed 已正式加入 MediCare_AI 一键脚本支持列表！

**特点**:
- ✅ 在线部署验证成功
- ✅ 支持 SELinux
- ✅ 软件版本最新
- ⚠️ 需要禁用 BuildKit

**适用场景**:
- 开发/测试环境
- 需要最新软件版本
- 技术预览

---

## 结论

**openSUSE Tumbleweed 支持在线部署！**

关键配置是使用旧版 Docker 构建器（`DOCKER_BUILDKIT=0`）， BuildKit 在 Tumbleweed 上存在兼容性问题。

一键脚本需要适配：
1. 自动检测 BuildKit 兼容性
2. 必要时自动切换旧版构建器
3. 为用户提供清晰的错误提示

---

**测试人员**: Sisyphus AI  
**测试时间**: 2026-02-04  
**状态**: ✅ 验证通过，已加入支持列表
