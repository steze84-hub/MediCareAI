# Changelog | 更新日志

All notable changes to this project will be documented in this file.
本项目的所有重要变更都将记录在此文件中。

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/spec/v2.0.0.html)。

---

## [1.0.3] - 2026-02-04

### Added | 新增

#### Unified One-Click Installation Script | 统一一键安装脚本
- **Created unified installation script (`install.sh`) supporting 7 Linux distributions** / 创建支持 7 个 Linux 发行版的统一安装脚本
  - Multi-language support: Chinese (简体中文) and English / 多语言支持：中文和英文
  - Automatic distribution detection / 自动检测发行版
  - Interactive configuration (AI API, network, ports) / 交互式配置
  - User agreement and risk acknowledgment / 用户协议和风险确认
  - Automatic Docker & Docker Compose v2 installation / 自动安装 Docker 和 Docker Compose v2
  - SELinux and BuildKit compatibility handling / SELinux 和 BuildKit 兼容性处理
  - Health check after deployment / 部署后健康检查

- **Supported Distributions** / 支持的发行版
  - ✅ Ubuntu 24.04 LTS - Fully tested / 完整测试
  - ✅ Fedora 43 Server - Fully tested / 完整测试
  - ✅ openSUSE Leap 16.0 - Fully tested / 完整测试
  - ✅ openSUSE Tumbleweed - Fully tested (with BuildKit fix) / 完整测试
  - ✅ AOSC OS 13.0.7 - Fully tested / 完整测试
  - ✅ openEuler 24.03 LTS-SP3 - Fully tested / 完整测试
  - ✅ Deepin 25 - Fully tested / 完整测试

#### AI Language Support | AI 语言支持
- **Implemented language preference for AI diagnosis** / 实现 AI 诊断语言偏好
  - Backend API now accepts `language` parameter (`zh` or `en`) / 后端 API 接受 `language` 参数
  - Frontend automatically detects page language / 前端自动检测页面语言
  - Bilingual system prompts and diagnosis prompts / 双语系统提示词和诊断提示词
  - AI responds in user's preferred language / AI 使用用户首选语言回复

#### Symptom Duration Enhancement | 症状持续时间增强
- **Added "minutes" option for symptom duration** / 添加症状持续时间"分钟"选项

### Fixed | 修复

#### Bug Fixes | Bug 修复
- **Fixed diagnosis info display bug** / 修复诊断信息显示问题
  - Fixed "Model: N/A" issue by adding `model_used` field / 修复"模型: N/A"问题
  - Fixed "Token usage: 0" issue by adding estimated token count / 修复"Token用量: 0"问题
  - Fixed "Invalid Date" issue by proper ISO format datetime / 修复"Invalid Date"问题

- **Fixed Docker Compose compatibility** / 修复 Docker Compose 兼容性
  - Changed `DEBUG: true` to `DEBUG: "true"` in docker-compose.yml / 修改布尔值格式
  - Changed `DEBUG: false` to `DEBUG: "false"` in docker-compose.prod.yml

#### Documentation Fixes | 文档修复
- **Updated README.md** / 更新 README.md
  - Removed misleading "GLM-4.7-Flash integration" references / 移除误导性的"集成 GLM-4.7-Flash"描述
  - Updated AI model description to "OpenAI-compatible API support" / 更新为"支持 OpenAI 兼容 API"
  - Updated contact email to hougelangley1987@gmail.com / 更新联系邮箱

### Changed | 变更
- Improved architecture diagram to reflect API-based AI / 改进架构图以反映基于 API 的 AI
- Updated project documentation structure / 更新项目文档结构

---

## [Unreleased] - Future Plans

### Planned Features | 计划功能
- Additional Linux distribution support / 额外 Linux 发行版支持
- Web-based installation wizard / 基于 Web 的安装向导
- Mobile app companion / 移动应用伴侣
- Multi-language knowledge base / 多语言知识库

### Changed | 变更

#### Python Version Upgrade | Python 版本升级

### Changed | 变更

#### Python Version Upgrade | Python 版本升级
- **Upgraded from Python 3.11 to Python 3.12** / 从 Python 3.11 升级到 3.12
  - Updated base image: `python:3.11-slim` → `python:3.12-slim-bookworm` / 更新基础镜像
  - Improved Dockerfile with better layer caching and environment variables / 优化 Dockerfile
  - Added `libpq-dev` for better PostgreSQL compatibility / 添加 PostgreSQL 开发库

#### Dependencies Update | 依赖更新
- Updated all Python packages to versions compatible with Python 3.12 / 更新所有包到 3.12 兼容版本
  - FastAPI: 0.104.1 → 0.109.2
  - Uvicorn: 0.24.0 → 0.27.1
  - SQLAlchemy: 2.0.23 → 2.0.27
  - Pydantic: 2.5.0 → 2.6.1
  - And other dependencies / 以及其他依赖

#### Code Refactoring | 代码重构
- Added `from __future__ import annotations` for improved type hints / 添加 future annotations
- Simplified and cleaned up code in core modules / 简化核心模块代码
  - `main.py`: Better organization and type hints / 更好的组织和类型提示
  - `config.py`: Improved validation and structure / 改进验证和结构
  - `ai_service.py`: Cleaner service layer / 更干净的服务层
  - `medical_case_service.py`: Better type annotations / 更好的类型注解
- Removed unnecessary comments while keeping essential documentation / 移除不必要注释
- Made code more Pythonic and elegant / 代码更 Pythonic 和优雅

### Technical Details | 技术细节

**Dockerfile Improvements:**
- Use `python:3.12-slim-bookworm` base image
- Set environment variables: `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`
- Add `PIP_NO_CACHE_DIR=1` and `PIP_DISABLE_PIP_VERSION_CHECK=1`
- Install `libpq-dev` for PostgreSQL compatibility
- Better cleanup with `apt-get clean` and `rm -rf`
- Multi-stage optimization / 多阶段优化

**Performance Benefits of Python 3.12:**
- 5-10% faster overall performance / 整体性能提升 5-10%
- Improved f-string parsing and error messages / 改进的 f-string 解析和错误信息
- Better memory efficiency / 更好的内存效率
- Enhanced type parameter syntax support / 增强的类型参数语法支持

---

## [1.0.2] - 2025-02-01

### Added | 新增

#### Streaming AI Diagnosis with Real-time Output | AI诊断流式输出
- **Implemented real-time streaming diagnosis** / 实现实时流式诊断
  - Added `/api/v1/ai/comprehensive-diagnosis-stream` endpoint / 添加流式诊断端点
  - StreamingResponse with Server-Sent Events (SSE) format / 使用 SSE 格式的 StreamingResponse
  - Character-by-character real-time AI response delivery / 逐字符实时传输 AI 响应
  - Enhanced user experience with immediate visual feedback / 即时视觉反馈改善用户体验

- **AI Service Streaming Support** / AI 服务流式支持
  - Added `chat_with_glm_stream()` method for streaming chat / 添加流式聊天方法
  - Added `comprehensive_diagnosis_stream()` for full workflow / 添加完整工作流流式方法
  - AsyncGenerator for efficient memory usage / 使用 AsyncGenerator 高效内存利用
  - Increased max_tokens to 8192 for comprehensive responses / 增加 max_tokens 至 8192 以支持完整回复

- **Frontend Markdown Rendering** / 前端 Markdown 渲染
  - Integrated marked.js for Markdown-to-HTML conversion / 集成 marked.js 进行 Markdown 到 HTML 转换
  - Real-time formatted display as AI generates content / AI 生成内容时实时格式化显示
  - Professional styling for tables, lists, code blocks / 表格、列表、代码块的专业样式
  - Support for headers, bold, italic, and complex formatting / 支持标题、粗体、斜体和复杂格式

#### Medical Records Enhancements | 诊疗记录增强
- **Fixed Status Bug** / 修复状态 Bug
  - Medical cases now correctly show "已完成" (completed) after AI diagnosis / 病历在 AI 诊断后正确显示"已完成"
  - Added `update_medical_case_status()` method in service layer / 在服务层添加 `update_medical_case_status()` 方法
  - Automatic status transition from 'active' to 'completed' / 自动状态从 'active' 转为 'completed'

- **PDF Export Functionality** / PDF 导出功能
  - Export diagnosis reports as PDF files / 将诊断报告导出为 PDF 文件
  - Using html2pdf.js library / 使用 html2pdf.js 库
  - Automatic button hiding during export / 导出时自动隐藏操作按钮
  - Filename format: `诊断报告_标题_日期.pdf` / 文件名格式

- **Share Functionality with QR Code** / 分享功能（带二维码）
  - Generate shareable links with configurable content / 生成可配置内容的分享链接
  - QR code generation for mobile scanning / 二维码生成供手机扫描
  - Privacy options: include/exclude diagnosis, symptoms, personal info / 隐私选项
  - One-click link copying / 一键复制链接

- **Print Optimization** / 打印优化
  - Dedicated print styles for clean output / 专用打印样式实现干净输出
  - Hide navigation, buttons, and UI elements when printing / 打印时隐藏导航、按钮和 UI 元素
  - Optimized page breaks and formatting / 优化的分页和格式

- **Medical Case Comparison** / 病历对比功能
  - Side-by-side comparison of two medical cases / 两份病历并排对比
  - Compare dates, severity, symptoms, and AI diagnoses / 对比日期、严重程度、症状和 AI 诊断
  - Dropdown selectors for case selection / 下拉选择器选择病历
  - Real-time comparison view updates / 实时对比视图更新

- **Doctor Annotations System** / 医生批注系统
  - Add annotations to medical cases / 为病历添加批注
  - LocalStorage-based persistence / 基于 LocalStorage 的持久化
  - Display annotation author, timestamp, and content / 显示批注作者、时间戳和内容
  - Styled annotation cards with yellow accent / 带黄色强调的样式化批注卡片

### Changed | 变更

#### Generic LLM References | 通用大模型引用
- **Removed specific LLM brand names from UI** / 从 UI 中移除特定大模型品牌名称
  - Updated login.html: "GLM-4.7" → "AI 大语言模型" / 更新 login.html
  - Updated index.html: "GLM-4.7" → "先进的大语言模型" / 更新 index.html
  - Updated test.html: "GLM-4.7" → "大语言模型" / 更新 test.html
  - Kept MinerU references as it's actually used for document extraction / 保留 MinerU 引用

### Technical Details | 技术细节

**Backend Changes:**
- `backend/app/api/api_v1/endpoints/ai.py`: Added streaming endpoint with status update
- `backend/app/services/ai_service.py`: Added streaming methods, increased max_tokens to 8192
- `backend/app/services/medical_case_service.py`: Added `update_medical_case_status()` method

**Frontend Changes:**
- `frontend/symptom-submit.html`: Updated for streaming with Markdown rendering
- `frontend/medical-records.html`: Added modal with PDF export, share, print, compare, annotations
- `frontend/login.html`, `frontend/index.html`, `frontend/test.html`: Removed GLM references

**New Dependencies:**
- marked.js (Markdown rendering)
- html2pdf.js (PDF export)
- qrcode.js (QR code generation)

---

## [1.0.1] - 2025-02-01

### Fixed | 修复

#### Critical Bug Fixes | 关键错误修复
- **Fixed SQLAlchemy relationship comment parameter error** / 修复 SQLAlchemy relationship comment 参数错误
  - Removed unsupported `comment` parameter from all `relationship()` definitions / 从所有 `relationship()` 定义中移除不支持的 `comment` 参数
  - Fixed backend container crash on startup / 修复后端容器启动时崩溃问题
  - Affected 11 relationship definitions across models / 影响模型中的 11 处关系定义
  - Error: `TypeError: RelationshipProperty.__init__() got an unexpected keyword argument 'comment'` / 错误：`TypeError: RelationshipProperty.__init__() got an unexpected keyword argument 'comment'`

#### Documentation Updates | 文档更新
- **Updated GLM_FLASH_SUCCESS_REPORT.md** / 更新 GLM_FLASH_SUCCESS_REPORT.md
  - Converted to comprehensive local deployment guide / 转换为全面的本地部署指南
  - Added deployment instructions for Ollama, llama.cpp, vLLM, SGLang, TGI / 添加 Ollama、llama.cpp、vLLM、SGLang、TGI 的部署说明
  - Added local MinerU deployment guide / 添加本地 MinerU 部署指南
  - Removed all sensitive information (IPs, API keys, tokens) / 移除所有敏感信息（IP、API 密钥、令牌）

- **Added comprehensive bilingual documentation** / 添加全面的双语文档
  - README.md with Chinese-English content / 包含中英文内容的 README.md
  - DEPLOYMENT.md with detailed deployment instructions / 包含详细部署说明的 DEPLOYMENT.md
  - ARCHITECTURE.md with system design documentation / 包含系统设计文档的 ARCHITECTURE.md
  - API.md with complete API reference / 包含完整 API 参考的 API.md
  - Comprehensive code comments in key files / 关键文件中的全面代码注释

#### Security Improvements | 安全改进
- **Sanitized all configuration files** / 清理所有配置文件
  - Removed real API keys and tokens from .env.example / 从 .env.example 中移除真实 API 密钥和令牌
  - Replaced with placeholder values / 替换为占位符值
  - Removed sensitive files containing internal IPs and credentials / 移除包含内部 IP 和凭据的敏感文件

#### Technical Memo | 技术备忘录
- **Added TECHNICAL_MEMO_ISSUE_ANALYSIS.md** / 添加 TECHNICAL_MEMO_ISSUE_ANALYSIS.md
  - Detailed incident report / 详细的事件报告
  - Root cause analysis / 根本原因分析
  - Solution and lessons learned / 解决方案和经验教训
  - Preventive measures / 预防措施

---

## [1.0.0] - 2025-02-01

### Added | 新增

#### Core Features | 核心功能
- **User Authentication System** - 用户认证系统
  - JWT-based authentication with refresh tokens / 基于 JWT 的认证，支持刷新令牌
  - User registration and login / 用户注册和登录
  - Password hashing with bcrypt / 使用 bcrypt 进行密码哈希
  - Session management / 会话管理

- **Patient Management** - 患者管理
  - Comprehensive patient profiles / 全面的患者档案
  - Personal information management / 个人信息管理
  - Emergency contact details / 紧急联系人详情
  - Medical record number assignment / 病历号分配

- **AI-Powered Diagnosis** - AI 智能诊断
  - Integration with GLM-4.7-Flash AI model / 集成 GLM-4.7-Flash AI 模型
  - Comprehensive diagnosis workflow / 综合诊断流程
  - Real-time symptom analysis / 实时症状分析
  - Follow-up plan generation / 随访计划生成
  - Confidence scoring / 置信度评分

- **Document Processing** - 文档处理
  - MinerU API integration / MinerU API 集成
  - PDF and image text extraction / PDF 和图片文本提取
  - Structured data extraction / 结构化数据提取
  - Document upload and management / 文档上传和管理

- **Medical Records** - 医疗记录
  - Case-based record management / 基于病例的记录管理
  - Document attachment support / 文档附件支持
  - AI feedback tracking / AI 反馈追踪
  - Medical history tracking / 病史追踪

- **Knowledge Base** - 知识库
  - Modular medical guidelines system / 模块化医疗指南系统
  - Multi-disease support / 多疾病支持
  - Evidence-based recommendations / 循证建议
  - Guidelines integration with AI diagnosis / 指南与 AI 诊断集成

#### Technical Implementation | 技术实现
- **Backend** - 后端
  - FastAPI framework with Python 3.11 / FastAPI 框架，Python 3.11
  - Async SQLAlchemy ORM with PostgreSQL / 异步 SQLAlchemy ORM，PostgreSQL
  - Pydantic data validation / Pydantic 数据验证
  - Dependency injection pattern / 依赖注入模式
  - Service layer architecture / 服务层架构

- **Frontend** - 前端
  - Vanilla HTML/CSS/JavaScript / 原生 HTML/CSS/JavaScript
  - Responsive design / 响应式设计
  - JWT token management / JWT 令牌管理
  - Form validation / 表单验证

- **Infrastructure** - 基础设施
  - Docker containerization / Docker 容器化
  - Docker Compose orchestration / Docker Compose 编排
  - Nginx reverse proxy / Nginx 反向代理
  - Redis caching / Redis 缓存
  - PostgreSQL 17 database / PostgreSQL 17 数据库

#### Documentation | 文档
- Comprehensive bilingual documentation (Chinese-English) / 全面的双语文档（中英文）
- README.md with quick start guide / 包含快速开始指南的 README.md
- DEPLOYMENT.md with detailed deployment instructions / 包含详细部署说明的 DEPLOYMENT.md
- ARCHITECTURE.md with system design / 包含系统设计的 ARCHITECTURE.md
- API.md with complete API reference / 包含完整 API 参考的 API.md
- AGENTS.md for AI assistant context / 用于 AI 助手上下文的 AGENTS.md
- CONTRIBUTING.md with development guidelines / 包含开发指南的 CONTRIBUTING.md
- CODE_OF_CONDUCT.md for community standards / 社区标准的 CODE_OFDUCT.md

### Security | 安全性
- JWT authentication with configurable expiration / 可配置过期时间的 JWT 认证
- Password hashing using bcrypt / 使用 bcrypt 进行密码哈希
- CORS configuration / CORS 配置
- Input validation with Pydantic / 使用 Pydantic 进行输入验证
- SQL injection prevention via parameterized queries / 通过参数化查询防止 SQL 注入
- HTTPS support via Nginx SSL / 通过 Nginx SSL 支持 HTTPS

### Changed | 变更
- Updated Docker images to latest versions / 将 Docker 镜像更新到最新版本
  - PostgreSQL: 15 → 17 / PostgreSQL: 15 → 17
  - Redis: 7 → 7.4 / Redis: 7 → 7.4
  - Node.js: 18 → 22 / Node.js: 18 → 22

### Fixed | 修复
- Emergency contact field split into name and phone / 紧急联系人字段拆分为姓名和电话
- Patient data binding during registration / 注册期间的患者数据绑定
- User profile data display consistency / 用户档案数据显示一致性

---

## Release History | 发布历史

### Version 1.0.0 (2025-02-01)
**Initial Production Release** | 初始生产版本

This is the first stable release of MediCare_AI, featuring a complete AI-powered disease management system.

这是 MediCare_AI 的第一个稳定版本，包含完整的 AI 智能疾病管理系统。

**Key Highlights:**
- Complete user authentication and patient management
- AI diagnosis with GLM-4.7-Flash integration
- Document processing with MinerU
- Comprehensive medical records system
- Modular knowledge base architecture
- Full Docker containerization
- Bilingual documentation

---

## Upcoming Features | 即将推出的功能

### Planned for v1.1.0
- [ ] Multi-language support (i18n) / 多语言支持
- [ ] Advanced analytics dashboard / 高级分析仪表盘
- [ ] Email notification system / 邮件通知系统
- [ ] Mobile app (React Native) / 移动应用
- [ ] Enhanced AI model fine-tuning / 增强的 AI 模型微调

### Planned for v1.2.0
- [ ] Multi-tenancy support / 多租户支持
- [ ] Advanced role-based access control / 高级基于角色的访问控制
- [ ] Integration with external EHR systems / 与外部 EHR 系统集成
- [ ] Real-time collaboration features / 实时协作功能
- [ ] Advanced reporting and statistics / 高级报告和统计

---

## Migration Guides | 迁移指南

### Upgrading from v0.x to v1.0.0

**Database Migration:**
```bash
# Backup your data first / 首先备份数据
docker-compose exec postgres pg_dump -U medicare_user medicare_ai > backup.sql

# Pull latest changes / 拉取最新更改
git pull origin main

# Rebuild containers / 重建容器
docker-compose down
docker-compose up -d --build

# Initialize database / 初始化数据库
docker-compose exec backend python -c "
import asyncio
from app.db.init_db import init_db
asyncio.run(init_db())
"
```

**Configuration Changes:**
- Update `.env` file with new variables / 使用新变量更新 `.env` 文件
- Review updated Docker Compose configuration / 检查更新的 Docker Compose 配置
- Update Nginx configuration if customized / 如果自定义则更新 Nginx 配置

---

## Contributors | 贡献者

A big thank you to all contributors who helped make this release possible!

非常感谢所有帮助实现此版本的贡献者！

### Core Team | 核心团队
- Architecture & Backend Development / 架构和后端开发
- Frontend Development / 前端开发
- AI Integration / AI 集成
- Documentation / 文档

### Special Thanks | 特别感谢
- GLM-4.7-Flash Team for the AI model / GLM-4.7-Flash 团队提供 AI 模型
- MinerU Team for document processing / MinerU 团队提供文档处理
- FastAPI Community for the excellent framework / FastAPI 社区提供优秀的框架

---

## Feedback | 反馈

We welcome your feedback! Please report issues or suggest features:

我们欢迎您的反馈！请报告问题或建议功能：

- **Issues**: [GitHub Issues](https://github.com/yourusername/MediCare_AI/issues)
- **Email**: support@medicare-ai.example.com
- **Documentation**: [Full Docs](docs/)

---

**Last Updated | 最后更新:** 2025-02-01  
**Current Version | 当前版本:** 1.0.2  
**Maintained by | 维护者:** MediCare_AI Team
