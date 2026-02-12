# 🚀 快速启动指南 - Docker 容器化部署

**创建时间**: 2026-02-12
**配置方式**: Docker Compose + 环境变量

---

## ✅ 环境配置完成！

已创建 `backend/.env` 文件，包含所有必需的配置。

---

## 🎯 启动步骤

### 1️⃣ 生成 JWT 密钥

**Windows 用户**:
```bash
openssl rand -hex 32
```

**Linux/Mac 用户**:
```bash
openssl rand -hex 32
```

将生成的密钥更新到 `.env` 文件的 `JWT_SECRET_KEY` 字段。

---

### 2️⃣ 启动 Docker 服务

#### **选项 A: 使用交互式脚本**（推荐）

```bash
cd D:\work\StudyNotesManager
bash start-docker.sh
```

脚本会：
- ✅ 检查 Docker 安装
- ✅ 检查端口占用
- ✅ 让您选择启动方式
- ✅ 自动启动所有服务

#### **选项 B: 手动启动**

```bash
# 完整启动（推荐）
docker-compose up -d postgres redis backend frontend

# 仅启动数据库
docker-compose up -d postgres redis

# 仅启动后端
docker-compose up -d backend

# 仅启动前端
docker-compose up -d frontend
```

---

## 📋 服务地址

启动后可以访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| **后端 API** | http://localhost:8000 | FastAPI 后端 |
| **前端** | http://localhost:3000 | Next.js 前端 |
| **数据库** | localhost:5432 | PostgreSQL |
| **Redis** | localhost:6379 | 缓存（可选） |

---

## 🔍 健康检查

### 后端健康检查
```bash
curl http://localhost:8000/api/health
```

### 查看容器状态
```bash
docker-compose ps
```

### 查看后端日志
```bash
docker-compose logs -f backend
```

---

## 🛑 常用操作

### 停止服务
```bash
docker-compose down
```

### 重启服务
```bash
docker-compose restart backend
```

### 查看实时日志
```bash
docker-compose logs -f
```

---

## 📝 环境变量说明

### 百度 OCR（如需要）

1. 前往百度智能云创建应用
2. 获取 API Key 和 Secret Key
3. 更新 `.env` 文件：
   ```
     BAIDU_OCR_APP_ID=你的AppID
     BAIDU_OCR_API_KEY=你的APIKey
     BAIDU_OCR_SECRET_KEY=你的SecretKey
     ```

### DeepSeek AI（如需要）

1. 注册 DeepSeek 账号
2. 获取 API Key
3. 更新 `.env` 文件：
   ```DEEPSEEK_API_KEY=your-api-key-here
   ```

### 阿里云 OSS（如需要文件存储）

1. 创建 Bucket
2. 配置 CORS
3. 更新 `.env` 文件

---

## ⚠️ 注意事项

1. **首次启动**：需要先初始化数据库
   ```bash
   docker-compose exec postgres psql -U studynotes -c "CREATE DATABASE studynotes;"
   ```

2. **密钥安全**：生产环境必须使用强密钥
   - JWT_SECRET_KEY 应为 32 字符随机字符串
   - 不要在代码中硬编码密钥
   - 不要将 `.env` 提交到 Git

3. **端口占用**：确保端口 5432、6379、8000、3000 未被占用

4. **Docker 清理**：定期清理未使用的镜像和容器
   ```bash
   docker system prune -a
   ```

---

## 🎯 现在可以启动了！

**准备好告诉我**：
1. ✅ 环境配置文件已创建
2. ✅ JWT 密钥已生成（或使用上面命令生成）
3. ✅ 启动脚本已准备好
4. ✅ Docker Compose 配置已就绪

**选择启动方式**：
- 方式 1：运行 `bash start-docker.sh`（推荐，交互式）
- 方式 2：运行 `docker-compose up -d`（快速）

**告诉我您选择的方式，我会协助启动服务！** 🚀
