# Changelog | 更新日志

All notable changes to this project will be documented in this file.
本项目的所有重要变更都将记录在此文件中。

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/spec/v2.0.0.html)。

---

## [1.0.3] - 2026-02-04

### 主要更新 Highlights

#### 🚀 一键部署脚本（中英双语）| One-Click Installation Script
- **统一安装脚本** `install.sh` 支持 7 大 Linux 发行版
  - ✅ Ubuntu 24.04 LTS
  - ✅ Fedora 43 Server  
  - ✅ openSUSE Leap 16.0
  - ✅ openSUSE Tumbleweed
  - ✅ AOSC OS 13.0.7
  - ✅ openEuler 24.03 LTS-SP3
  - ✅ Deepin 25
- **多语言支持**: 中文/English 双语界面
- **智能检测**: 自动识别发行版并处理兼容性问题
- **交互配置**: AI API、网络设置、端口自定义
- **自动处理**: SELinux、BuildKit 等兼容性问题

#### 🌍 AI 诊断语言自适应 | AI Language Support
- **新增 `language` 参数** 支持 `zh` (中文) 和 `en` (英文)
- **前端自动检测** 页面语言并传递参数
- **双语 Prompt**: 系统提示词和诊断提示词均支持双语
- **智能回复**: AI 根据界面语言自动切换回复语言

### 新增功能 Added

#### 症状提交增强 | Symptom Submission Enhancement
- **新增"分钟"单位** 到症状持续时间选项

### 修复 Fixed

#### Bug 修复 | Bug Fixes
- **修复诊断信息显示问题**
  - 修复 "模型: N/A" → 正确显示配置的模型ID
  - 修复 "Token用量: 0" → 显示估算的Token用量
  - 修复 "诊断时间: Invalid Date" → 正确格式化日期
- **修复 Docker Compose 兼容性**
  - `DEBUG: true` → `DEBUG: "true"` (字符串格式)
  - 解决 docker-compose v1.x 的类型验证错误

### 变更 Changed

#### 文档更新 | Documentation Updates
- **README.md 修正**
  - 移除 "集成 GLM-4.7-Flash" 描述，改为 "支持 OpenAI 兼容 API"
  - 更新联系邮箱为 hougelangley1987@gmail.com
  - 添加作者信息：苏业钦 (Su Yeqin)
- **LICENSE 更新**
  - 版权声明：Copyright (c) 2025 苏业钦 (Su Yeqin) and Contributors
  - 协议类型：MIT License

#### 界面优化 | UI Improvements
- **登录页面** 添加作者署名和 License 信息
- **首页页脚** 添加作者署名

### 技术细节 Technical Details

#### 后端变更 | Backend Changes
- `ai.py`: 新增 `language` 参数，更新流式响应数据结构
- `ai_service.py`: 双语 prompt 构建，系统提示词语言切换
- `docker-compose.yml`: 修复布尔值格式

#### 前端变更 | Frontend Changes
- `symptom-submit.html`: 语言检测逻辑，诊断信息存储
- `login.html`: 添加作者信息
- `index.html`: 页脚添加作者信息

---

## [1.0.2] - 2025-02-01

### 主要特性

#### 🤖 AI 流式诊断 | Streaming AI Diagnosis
- **实时流式输出** `/api/v1/ai/comprehensive-diagnosis-stream`
- **SSE 格式** Server-Sent Events 实现
- **逐字符显示** AI 回复实时展示
- **完整工作流**: 个人信息 + MinerU文档提取 + 知识库 → AI诊断

#### 📄 文档智能处理 | Document Processing
- **MinerU 集成** PDF/图片/文档文本提取
- **支持格式**: PDF, Word, PPT, 图片
- **自动提取** 检查报告内容结构化

#### 🏥 知识库系统 | Knowledge Base
- **模块化设计** 支持多种疾病
- **当前支持**: 呼吸系统疾病 (respiratory)
- **循证医学** 整合诊疗指南

### 核心功能

- **用户认证**: JWT + Refresh Token
- **患者管理**: 档案、病历号、随访
- **医疗记录**: 病例、附件、AI反馈
- **多科室支持**: 内科、外科、儿科、妇科

### 技术栈

- **后端**: FastAPI 0.109.2, Python 3.12, SQLAlchemy 2.0
- **数据库**: PostgreSQL 17, Redis 7.4
- **前端**: HTML5/CSS3/ES6
- **AI**: OpenAI 兼容 API
- **部署**: Docker + Docker Compose

---

## 版本历史 Version History

| 版本 | 日期 | 主要更新 |
|------|------|----------|
| 1.0.3 | 2026-02-04 | 一键部署脚本、AI语言支持、Bug修复 |
| 1.0.2 | 2025-02-01 | 流式AI诊断、文档处理、知识库 |

---

**作者 Author**: 苏业钦 (Su Yeqin)  
**协议 License**: MIT License  
**仓库 Repository**: MediCare_AI
