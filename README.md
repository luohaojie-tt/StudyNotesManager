# StudyNotesManager 学习笔记管理系统

> 🚀 智能学习笔记管理，AI驱动的学习效率提升工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/next.js-14-black.svg)](https://nextjs.org/)
[![PostgreSQL 15](https://img.shields.io/badge/postgresql-15-blue.svg)](https://www.postgresql.org/)

---

## 📖 项目简介

StudyNotesManager 是一个基于AI的学习笔记管理系统，帮助用户：
- 📝 **智能识别**：OCR识别图片和PDF笔记
- 🧠 **脑图生成**：AI自动生成思维导图
- ❓ **智能测验**：基于知识点自动生成题目
- 📚 **错题管理**：艾宾浩斯曲线智能复习
- 📊 **学习分析**：可视化学习数据和进度

---

## 🎯 核心功能

### 1. 笔记管理
- ✅ 上传图片/PDF笔记
- ✅ OCR文字识别（百度OCR）
- ✅ 笔记分类和标签
- ✅ 语义搜索（向量搜索）

### 2. AI脑图
- ✅ 自动生成思维导图（DeepSeek API）
- ✅ 可视化编辑节点
- ✅ 知识点关联

### 3. 智能测验
- ✅ 自动生成测验题
- ✅ 多种题型支持（选择、填空、问答）
- ✅ AI智能评分

### 4. 错题本
- ✅ 自动收集错题
- ✅ 艾宾浩斯复习提醒
- ✅ 知识点统计分析

### 5. 数据分析
- ✅ 学习时长统计
- ✅ 知识点掌握度
- ✅ 学习曲线可视化

---

## 🏗️ 技术栈

### 后端
- **框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 15 + pgvector
- **向量数据库**: ChromaDB
- **AI服务**: DeepSeek API
- **OCR**: 百度OCR API
- **存储**: 阿里云OSS

### 前端
- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript 5+
- **组件库**: shadcn/ui
- **状态管理**: Zustand
- **数据获取**: React Query

### 部署
- **容器**: Docker + Docker Compose
- **缓存**: Redis 7+
- **消息队列**: RabbitMQ 3.12+

---

## 📊 项目状态

| 模块 | 完成度 | 状态 |
|------|--------|------|
| 后端API | 70% | 🔄 开发中 |
| 前端UI | 20% | 🚧 开始阶段 |
| AI集成 | 90% | ✅ 基本完成 |
| 测试 | 80% | ✅ 覆盖良好 |
| 部署 | 0% | ⏸ 待开始 |

**整体进度**: 31% (MVP预计还需1-2周)

详细状态请查看：[docs/00-overview/项目状态.md](./docs/00-overview/项目状态.md)

---

## 🚀 快速开始

### 环境要求
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Docker & Docker Compose

### 后端启动
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 配置环境变量
uvicorn app.main:app --reload
```

### 前端启动
```bash
cd frontend
npm install
cp .env.example .env.local
# 配置环境变量
npm run dev
```

### Docker启动（推荐）
```bash
docker-compose up -d
```

---

## 📚 文档导航

📖 **完整文档请查看**: [docs/README.md](./docs/README.md)

### 核心文档
- 📋 [功能需求](./docs/01-requirements/功能需求.md) - 16项核心功能
- 🏗️ [系统架构设计](./docs/02-architecture/系统架构设计文档.md) - 技术方案
- 📝 [详细任务清单](./docs/03-tasks/详细任务清单.md) - 39个开发任务
- 🔧 [后端开发文档](./docs/04-backend/README.md)
- 🎨 [前端开发文档](./docs/05-frontend/README.md)
- 🧪 [测试文档](./docs/06-testing/测试规范.md)
- 📊 [项目进度报告](./docs/03-tasks/进度报告.md)

---

## 👥 团队协作

### Git工作流自动化 ⭐

**teammates使用git-workflow skill自动执行Git操作**：

```bash
# 创建分支
git-workflow: create branch backend-dev user-auth

# 提交代码
git-workflow: commit feat 添加用户注册API

# 创建PR
git-workflow: pr 实现用户认证系统
```

**文档参考**：
- 分支策略：[docs/09-workflow/GIT_WORKFLOW.md](./docs/09-workflow/GIT_WORKFLOW.md)
- 工作规范：[docs/09-workflow/TEAMMATES_GUIDELINES.md](./docs/09-workflow/TEAMMATES_GUIDELINES.md)
- Skill文档：[.claude/skills/git-workflow.md](./.claude/skills/git-workflow.md)

### 团队成员
- **team-lead**: 协调、决策、进度跟踪
- **backend-dev**: 后端API开发
- **frontend-dev**: 前端UI开发
- **code-reviewer**: 代码审查
- **test-specialist**: 测试保障

---

## 📝 开发规范

### Commit Message
```
feat: 添加用户注册API
fix: 修复登录验证错误
docs: 更新API文档
test: 添加认证模块测试
```

### Pull Request模板
请参考 [GIT_WORKFLOW.md](./GIT_WORKFLOW.md) 中的PR模板

---

## 🧪 测试

### 运行测试
```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm test

# E2E测试
npx playwright test
```

### 测试覆盖率
- 后端：>80% (pytest-cov)
- 前端：>80% (Vitest)

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

请先阅读 [docs/README.md](./docs/README.md) 了解项目结构。

---

**最后更新**: 2026-02-09
**维护者**: team-lead
