# Fedora 43 在线部署成功经验总结

**日期**: 2026-02-04  
**目标**: Fedora 43 Server (192.168.50.145)  
**状态**: ✅ 在线部署成功

---

## 关键成功因素

### 1. 全局科学上网配置 ⭐⭐⭐⭐⭐

**问题**: Docker 容器内部无法直接访问宿主机代理  
**解决**: 配置 v2raya 为 **全局模式**

**配置步骤**:
```bash
# 1. 安装并启动 v2raya
sudo systemctl enable --now v2raya

# 2. 访问 v2raya Web UI (http://localhost:2017)
# 3. 导入节点配置
# 4. 设置为【全局模式】（不是绕过大陆或规则模式）
# 5. 确认代理端口: 127.0.0.1:20171 (HTTP)
```

### 2. Docker 代理配置

创建 Docker 代理配置：
```bash
sudo mkdir -p /etc/systemd/system/docker.service.d

sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf << 'EOF'
[Service]
Environment="HTTP_PROXY=http://127.0.0.1:20171/"
Environment="HTTPS_PROXY=http://127.0.0.1:20171/"
Environment="NO_PROXY=localhost,127.0.0.1,192.168.50.0/24"
EOF

# 重启 Docker
sudo systemctl daemon-reload
sudo systemctl restart docker
```

### 3. 验证网络

测试命令：
```bash
# 测试外部网络
curl -s https://www.google.com -o /dev/null -w '%{http_code}'
# 预期输出: 200

# 测试 Docker Hub
docker pull hello-world:latest
# 预期: 成功拉取

# 查看出口 IP
curl -s https://ipinfo.io/ip
# 预期: 代理服务器 IP
```

---

## 部署步骤

### 完整在线部署流程

```bash
# 1. 进入项目目录
cd /opt/medicare-ai

# 2. 更新环境配置
cat > .env << 'EOF'
POSTGRES_PASSWORD=medicare123456
REDIS_PASSWORD=medicare123456
JWT_SECRET_KEY=fedora43-online-deploy-key-32chars
AI_API_KEY=zhanxiaopi
AI_API_URL=http://192.168.50.253:8033/v1/
MINERU_TOKEN=your-mineru-token
DEBUG=false
USE_CN_MIRROR=false
EOF

# 3. 在线构建并启动
docker compose up --build -d

# 4. 验证部署
curl http://localhost:8000/health
docker ps
```

---

## 验证结果

| 检查项 | 状态 | 说明 |
|--------|------|------|
| Google 访问 | ✅ | HTTP 200 |
| Docker Hub | ✅ | 拉取成功 |
| 构建速度 | ✅ | apt-get update < 10s |
| 容器启动 | ✅ | 5/5 运行 |
| 健康检查 | ✅ | {"status":"healthy"} |
| API 文档 | ✅ | http://192.168.50.145:8000/docs |

---

## 经验总结

### ✅ 必要条件

1. **全局代理模式**: v2raya 必须设置为全局，不能只代理特定域名
2. **Docker 代理**: 必须通过 systemd 配置 Docker 代理
3. **网络连通性**: 部署前验证 Google 和 Docker Hub 均可访问

### ❌ 常见陷阱

1. **绕过大陆模式**: 只代理国外域名，但 Docker 容器内部解析可能失败
2. **规则模式**: 某些必要域名可能未在规则中
3. **仅配置 registry-mirrors**: 只能加速镜像拉取，无法加速构建过程中的 apt-get

### 🚀 性能对比

| 指标 | 无代理 | HTTP 代理 (之前) | 全局代理 (现在) |
|------|--------|------------------|-----------------|
| apt-get update | 超时 | >10 分钟 | <10 秒 ✅ |
| 镜像拉取 | 失败 | 成功 | 成功 |
| 构建时间 | 不可用 | 极慢 | 3-5 分钟 ✅ |

---

## 配置模板

### v2raya 配置要点

```json
// /etc/v2raya/config.json 中的关键部分
{
  "inbounds": [
    {
      "port": 20171,          // HTTP 代理端口
      "protocol": "http",
      "listen": "127.0.0.1",
      "tag": "http_ipv4"
    }
  ],
  "routing": {
    "rules": [
      // 全局模式下，所有流量都走代理
      {
        "type": "field",
        "outboundTag": "proxy",
        "port": "0-65535"
      }
    ]
  }
}
```

### Docker 代理配置模板

```ini
# /etc/systemd/system/docker.service.d/http-proxy.conf
[Service]
Environment="HTTP_PROXY=http://127.0.0.1:20171/"
Environment="HTTPS_PROXY=http://127.0.0.1:20171/"
Environment="NO_PROXY=localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8"
```

---

## 访问地址

部署完成后访问：
- **Web UI**: http://192.168.50.145/
- **API Docs**: http://192.168.50.145:8000/docs
- **Health**: http://192.168.50.145:8000/health

---

## 结论

**Fedora 43 支持在线部署！**

关键成功因素是配置 **全局科学上网**，而不仅仅是镜像加速器或 Docker 代理。只有全局代理才能确保构建过程中的所有网络请求都能正常访问。

---

**记录人**: Sisyphus AI  
**部署时间**: 2026-02-04  
**状态**: ✅ 在线部署验证成功
