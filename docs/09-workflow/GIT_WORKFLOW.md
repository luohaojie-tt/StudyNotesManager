# Git工作流规范

## 🌳 分支策略

### 主要分支

```
main (生产环境)
  ↑
  └─ merge (仅限稳定版本)

develop (开发环境)
  ↑
  ├─ backend-dev/* (后端功能分支)
  ├─ frontend-dev/* (前端功能分支)
  ├─ test/* (测试分支)
  └─ fix/* (bug修复分支)
```

### 分支命名规则

| 分支类型 | 命名格式 | 示例 |
|---------|---------|------|
| 后端功能 | `backend-dev/功能名` | `backend-dev/auth-api` |
| 前端功能 | `frontend-dev/功能名` | `frontend-dev/note-list` |
| 测试 | `test/测试类型` | `test/integration-auth` |
| Bug修复 | `fix/问题描述` | `fix/login-error` |
| 热修复 | `hotfix/问题描述` | `hotfix/security-patch` |

## 📋 teammates分支分配

| teammate | 分支前缀 | 示例 |
|----------|---------|------|
| backend-dev | `backend-dev/` | `backend-dev/auth-api`, `backend-dev/note-crud` |
| frontend-dev | `frontend-dev/` | `frontend-dev/dashboard`, `frontend-dev/mindmap` |
| test-specialist | `test/` | `test/auth-tests`, `test/e2e-flows` |
| code-reviewer | (直接在PR上审查) | - |

## 🔄 工作流程

### 1. 功能开发流程

```bash
# 1. 从develop创建功能分支
git checkout develop
git pull origin develop
git checkout -b backend-dev/auth-api

# 2. 开发功能
# ... 编写代码 ...

# 3. 提交代码
git add .
git commit -m "feat: 实现用户注册API

- POST /api/auth/register
- 邮箱格式验证
- 密码bcrypt加密
- 返回JWT token"

# 4. 推送到远程
git push -u origin backend-dev/auth-api

# 5. 创建Pull Request
# 从 backend-dev/auth-api -> develop

# 6. code-reviewer审查
# 7. 修改反馈
# 8. 合并到develop
# 9. 删除功能分支
```

### 2. Commit Message规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>

[optional body]

[optional footer]
```

**Type类型**:
- `feat`: 新功能
- `fix`: Bug修复
- `refactor`: 代码重构
- `docs`: 文档更新
- `test`: 测试相关
- `chore`: 构建/工具链
- `perf`: 性能优化
- `ci`: CI配置

**示例**:
```bash
feat: 添加笔记上传API支持图片和PDF

- 实现multipart/form-data处理
- 集成百度OCR识别文字
- 上传文件到阿里云OSS
- 添加文件类型和大小验证

Closes #123
```

### 3. Pull Request模板

```markdown
## 📝 变更说明
<!-- 简述本次PR的目的 -->

## 🔧 变更类型
- [ ] 新功能
- [ ] Bug修复
- [ ] 重构
- [ ] 文档
- [ ] 测试

## 📸 相关截图
<!-- 如果有UI变更，请截图 -->

## ✅ 测试清单
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试通过
- [ ] 代码覆盖率≥80%

## 🔗 相关Issue
Closes #(issue number)

## 📋 代码审查清单
- [ ] 安全审查通过（无SQL注入、XSS等）
- [ ] 性能审查通过（无N+1查询）
- [ ] 代码风格统一
- [ ] 注释完整
```

### 4. Code Review流程

1. **创建PR**后，自动通知code-reviewer
2. **code-reviewer**审查以下维度：
   - 安全问题（CRITICAL）
   - 代码质量（HIGH）
   - 性能问题（MEDIUM）
   - 测试覆盖（LOW）
3. **开发者**根据反馈修改
4. **审查通过**后合并到develop
5. **删除功能分支**

### 5. 合并策略

| 目标分支 | 合并策略 | 要求 |
|---------|---------|------|
| develop | Squash and Merge | 1个approval + CI通过 |
| main | Merge | 2个approvals + 全测试通过 |

## 🚨 注意事项

### 1. frontend子仓库问题
frontend是独立的git仓库，需要处理：
```bash
# 方案A: 删除frontend的.git，作为整体仓库
cd frontend
rm -rf .git
cd ..
git add frontend
git commit -m "chore: merge frontend into main repo"

# 方案B: 使用git submodule（推荐）
git rm --cached frontend
git submodule add <frontend-url> frontend
```

### 2. 避免直接提交到main/develop
所有开发工作必须在功能分支进行

### 3. 频繁同步develop
```bash
git checkout develop
git pull origin develop
git checkout backend-dev/feature
git rebase develop
```

### 4. 解决冲突
- 优先使用rebase而不是merge
- 与相关teammate沟通解决冲突
- 解决后确保测试通过

## 📊 分支状态追踪

当前活跃分支将在team-lead处统一追踪，每日站会同步进度。

---

**最后更新**: 2026-02-09
**维护者**: team-lead
