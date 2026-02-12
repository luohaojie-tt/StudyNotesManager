# 🚀 部署指南

**项目**: Study Notes Manager - AI Learning Platform
**状态**: 开发完成，准备部署
**日期**: 2026-02-12

---

## 📋 部署前准备清单

### 1. 环境配置

### 后端环境变量

创建 `backend/.env` 文件：

```bash
# 应用配置
APP_NAME=StudyNotesManager
APP_VERSION=1.0.0
DEBUG=False  # 生产环境设为 False

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/studynotes
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=studynotes
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis 配置（可选，用于缓存）
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# JWT 配置
JWT_SECRET_KEY=生产环境使用强密钥
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS 配置
CORS_ORIGINS=["https://your-domain.com","https://www.your-domain.com"]

# 百度 OCR 配置
BAIDU_OCR_APP_ID=your_baidu_app_id
BAIDU_OCR_API_KEY=your_baidu_api_key
BAIDU_OCR_SECRET_KEY=your_baidu_secret_key

# 阿里云 OSS 配置
ALIYUN_OSS_ACCESS_KEY_ID=your_access_key_id
ALIYUN_OSS_ACCESS_KEY_SECRET=your_access_key_secret
ALIYUN_OSS_BUCKET_NAME=your_bucket_name
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com

# DeepSeek AI 配置
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1

# OpenAI（可选）
OPENAI_API_KEY=your_openai_api_key

# 文件上传配置
MAX_UPLOAD_SIZE=10485760  # 100MB
ALLOWED_EXTENSIONS=["jpg","jpeg","png","pdf"]

# 日志配置
LOG_LEVEL=INFO
```

### 前端环境变量

创建 `frontend/.env.local` 文件：

```bash
# API 配置
NEXT_PUBLIC_API_URL=https://your-api-domain.com/api

# 功能开关
NEXT_PUBLIC_ENABLE_MINDMAP=true
NEXT_PUBLIC_ENABLE_QUIZ=true
NEXT_PUBLIC_ENABLE_ANALYTICS=true

# 其他配置
NEXT_PUBLIC_MAX_UPLOAD_SIZE=104857600
```

---

### 2. 依赖安装

### 后端依赖
```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 或使用 poetry
poetry install
```

### 前端依赖
```bash
cd frontend

# 安装依赖
npm install
# 或使用 pnpm/yarn
pnpm install
```

---

### 3. 数据库初始化

### PostgreSQL 安装（Windows）

1. **下载 PostgreSQL**: https://www.postgresql.org/download/windows/
2. **安装**：使用安装向导
3. **创建数据库**:
   ```sql
   CREATE DATABASE studynotes;
   ```
4. **运行迁移**:
   ```bash
   cd backend
   alembic upgrade head
   ```

### Docker 方式（推荐）

使用 Docker 运行 PostgreSQL：

```bash
# 启动 PostgreSQL
docker run --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:15

# 或使用 docker-compose
docker-compose up -d postgres
```

---

### 4. 启动应用

### 开发模式

**后端**:
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端**:
```bash
cd frontend
npm run dev
# 访问 http://localhost:3000
```

### 生产模式

**后端** (使用 Gunicorn):
```bash
cd backend
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
--bind 0.0.0.0:8000
```

**前端** (先构建):
```bash
cd frontend
npm run build
npm start
# 或使用 PM2
pm2 start npm --name "study-notes-frontend"
```

---

## 🎯 部署步骤

### 阶段 1: 本地验证 ⏳

- [ ] 配置本地环境变量
- [ ] 启动 PostgreSQL 数据库
- [ ] 运行数据库迁移
- [ ] 启动后端服务
- [ ] 启动前端服务
- [ ] 本地测试所有功能

### 阶段 2: 容器化（可选）⏳

**Docker 化后端**:

创建 `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

创建 `backend/docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/studynotes
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: studynotes
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

**Docker 化前端**:

`frontend/` 已经有 Next.js 内置 Docker 支持。

### 阶段 3: 云平台部署 ⏳

#### 选项 A: Vercel（推荐用于 Next.js 前端）

**前端部署到 Vercel**:
```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
```

**后端部署到 Railway/Render**:
1. 推送代码到 GitHub
2. 在 Railway 创建新项目
3. 连接 GitHub 仓库
4. 配置环境变量
5. 部署

#### 选项 B: 自建服务器

**服务器要求**:
- Ubuntu 20.04+ 或 CentOS 7+
- 2GB+ RAM
- 20GB+ 磁盘空间

**部署步骤**:
```bash
# 1. 克隆代码
git clone https://github.com/luohaojie-tt/StudyNotesManager.git

# 2. 配置环境
cd StudyNotesManager/backend
cp .env.example .env
# 编辑 .env 文件，填入真实配置

# 3. 安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. 数据库迁移
alembic upgrade head

# 5. 使用 Supervisor 管理进程
sudo apt install supervisor
sudo vi /etc/supervisor/conf.d/studynotes.conf

# 6. 启动服务
sudo supervisord -c /etc/supervisor/supervisord.conf
sudo supervisorctl start studynotes
```

**Nginx 配置**:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # WebSocket 支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 🧪 部署后验证

### 1. 健康检查

```bash
# 后端健康检查
curl https://your-api-domain.com/api/health

# 前端检查
curl https://your-domain.com
```

### 2. 功能测试清单

- [ ] 用户注册和登录
- [ ] 笔记上传（图片、PDF）
- [ ] OCR 文字识别
- [ ] 思维导图生成
- [ ] 测验生成和答题
- [ ] 错题记录
- [ ] 错题复习
- [ ] 数据统计展示

### 3. 性能验证

- [ ] API 响应时间 < 500ms
- [ ] 页面加载时间 < 2s
- [ ] 数据库查询优化
- [ ] 缓存命中率 > 80%

---

## 📊 监控配置

### 日志监控

```bash
# 后端日志
tail -f backend/logs/app.log

# Nginx 访问日志
tail -f /var/log/nginx/access.log
```

### 性能监控

使用 **Sentry** 或类似工具：
```python
# 安装 Sentry
pip install sentry-sdk[fastapi]

# 在代码中初始化
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
)
```

---

## 🔒 安全配置

### 生产环境安全检查

- [ ] DEBUG=False
- [ ] 使用强密码（数据库、JWT）
- [ ] 配置防火墙（仅开放 80、443）
- [ ] 启用 HTTPS（Let's Encrypt）
- [ ] 配置 CORS 白名单
- [ ] 启用速率限制
- [ ] 定期更新依赖

---

## 📝 故障排查

### 常见问题

**1. 数据库连接失败**
```bash
# 检查 PostgreSQL 状态
sudo systemctl status postgresql

# 检查端口
netstat -an | grep 5432
```

**2. API CORS 错误**
```bash
# 检查 .env 中的 CORS_ORIGINS
# 确保前端域名在列表中
```

**3. 文件上传失败**
```bash
# 检查 OSS 配置
# 检查 bucket 权限
# 检查文件大小限制
```

**4. AI API 调用失败**
```bash
# 检查 API Key 有效性
# 检查 API 额度
# 查看错误日志
```

---

## 🎯 快速部署（最简单方式）

### 使用现有平台

**Render** (推荐):
1. 连接 GitHub: https://render.com
2. New Web Service
3. 选择 PostgreSQL + Python
4. 连接仓库
5. 配置环境变量
6. Deploy

**Railway**:
1. Connect GitHub
2. New Project + Database
3. Deploy

---

## 📞 支持和文档

**项目文档**: `docs/09-workflow/`
**GitHub Issues**: https://github.com/luohaojie-tt/StudyNotesManager/issues
**Wiki**: (可创建 GitHub Wiki)

---

**部署前请确保**:
1. ✅ 所有环境变量已配置
2. ✅ 数据库已创建和迁移
3. ✅ 依赖已安装
4. ✅ 安全配置已检查
5. ✅ 监控已配置

**祝部署顺利！** 🚀

---

**文档版本**: 1.0
**最后更新**: 2026-02-12
