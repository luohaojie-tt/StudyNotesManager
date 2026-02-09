# Git Workflow Skill

> 🎯 **自动化的Git工作流** - 确保所有操作符合团队规范

## 📋 Skill描述

这个skill封装了StudyNotesManager项目的Git工作流，确保teammates的所有Git操作都符合团队规范，无需记忆复杂的规则。

## 🎯 适用场景

当teammates需要执行以下Git操作时：
- 创建功能分支
- 提交代码
- 创建Pull Request
- 推送代码
- 合并代码

## 📖 使用方法

### 方式1: 直接调用
```
请使用git-workflow skill创建一个backend认证功能的分支
```

### 方式2: 隐式触发
```
我要开始开发用户认证API
→ 自动使用git-workflow skill创建分支和提交
```

---

## 🔧 核心功能

### 1. 创建功能分支

**命令模板**：
```
git-workflow: create branch <分支类型> <功能名称>
```

**示例**：
```bash
# 后端功能
git-workflow: create branch backend-dev user-auth

# 前端功能
git-workflow: create branch frontend-dev note-list

# 测试功能
git-workflow: create branch test auth-integration
```

**自动执行**：
```bash
git checkout develop
git pull origin develop
git checkout -b <分支类型>/<功能名称>
```

**分支命名规范**：
- `backend-dev/*` - 后端开发
- `frontend-dev/*` - 前端开发
- `test/*` - 测试相关

---

### 2. 提交代码

**命令模板**：
```
git-workflow: commit <type> <description>
```

**Commit Type**：
- `feat` - 新功能
- `fix` - Bug修复
- `refactor` - 代码重构
- `docs` - 文档更新
- `test` - 测试相关
- `chore` - 构建/工具链

**示例**：
```bash
# 新功能
git-workflow: commit feat 添加用户注册API

# Bug修复
git-workflow: commit fix 修复登录验证错误

# 文档更新
git-workflow: commit docs 更新API文档
```

**自动执行**：
```bash
git add .
git commit -m "<type>: <description>"
# 自动检查格式（通过Git hook）
```

---

### 3. 推送代码

**命令模板**：
```
git-workflow: push
```

**自动执行**：
```bash
git push -u origin <当前分支名>
```

---

### 4. 创建Pull Request

**命令模板**：
```
git-workflow: pr <title>
```

**示例**：
```bash
git-workflow: pr 实现用户认证系统
```

**自动执行**：
```bash
# 使用gh命令创建PR
gh pr create --base develop --title "<title>"
# 自动填充PR模板
```

**PR模板内容**：
```markdown
## 📝 变更说明
<由AI自动生成>

## 🔧 变更类型
- [ ] 新功能
- [ ] Bug修复

## ✅ 测试清单
- [ ] 单元测试通过
- [ ] 代码覆盖率≥80%

## 🔗 相关任务
Closes #(issue number)
```

---

### 5. 每日工作流

**完整工作流**：
```
git-workflow: daily start
```

**自动执行**：
```bash
# 1. 拉取最新代码
git checkout develop
git pull origin develop

# 2. 创建今日功能分支（如果还没有）
git checkout -b <分支类型>/<功能名称>

# 3. 显示当前任务列表
# （从TaskList读取）

# 4. 询问今日计划
```

**每日结束**：
```
git-workflow: daily end
```

**自动执行**：
```bash
# 1. 提交今日所有更改
git add .
git commit -m "wip: 今日进度"

# 2. 推送到远程
git push

# 3. 生成今日工作报告
# （包含commits、修改的文件、测试结果）
```

---

## 🎨 高级功能

### 批量提交

当有多个小改动时：
```
git-workflow: squash feat 实现用户认证系统
```

自动将当前分支的所有commits压缩成一个规范的commit。

---

### 自动检测规范

**自动检查**：
- ✅ Commit message格式
- ✅ 分支命名规范
- ✅ 是否从develop创建
- ✅ 代码测试是否通过
- ✅ 是否有merge conflict

**如果检测到违规**：
```
❌ 检测到以下问题：
- Commit message格式错误
- 分支命名不符合规范

请修正后再继续。
```

---

## 📊 示例对话

### 场景1: backend-dev开始新功能

**User**:
```
我要开发用户注册API
```

**Git Workflow Skill**:
```
🔄 执行以下操作：

1. 切换到develop分支
   git checkout develop
   git pull origin develop

2. 创建功能分支
   git checkout -b backend-dev/user-registration

✅ 分支创建成功，现在可以开始开发了！

💡 提示：
- 使用 TDD 方式开发
- 测试覆盖率需 >80%
- 完成后使用 "git-workflow: commit feat 实现用户注册API" 提交
```

---

### 场景2: frontend-dev提交代码

**User**:
```
我完成了笔记列表页面，提交代码
```

**Git Workflow Skill**:
```
🔄 准备提交代码：

检测到修改：
- src/app/notes/page.tsx
- src/components/notes/NotesList.tsx
- src/hooks/useNotes.ts

建议的commit message：
feat: 实现笔记列表页面

- 添加笔记列表组件
- 实现分页和筛选功能
- 集成后端API

是否使用这个commit message？[Y/n]
```

---

### 场景3: 创建PR

**User**:
```
认证功能开发完成，创建PR
```

**Git Workflow Skill**:
```
🔄 创建Pull Request：

分支: backend-dev/auth-api → develop

标题: feat: 实现用户认证系统

描述：
## 📝 变更说明
实现完整的用户认证系统，包括注册、登录、Token管理

## ✅ 完成的功能
- [x] POST /api/auth/register
- [x] POST /api/auth/login
- [x] POST /api/auth/refresh
- [x] JWT token生成和验证
- [x] 单元测试 (覆盖率85%)

## 📊 测试结果
- 单元测试: 32/32 通过 ✅
- 集成测试: 8/8 通过 ✅
- 代码覆盖率: 85% ✅

🔗 创建PR中...
✅ PR创建成功: https://github.com/xxx/pull/123

💡 下一步：
- 等待code-reviewer审查
- 根据反馈修改
- 审查通过后使用Squash and Merge合并
```

---

## 🚨 错误处理

### 错误1: 分支命名不符合规范

**场景**:
```
git checkout -b auth-api
```

**Git Workflow Skill**:
```
❌ 分支命名错误！

正确格式: <type>/<feature-name>

后端开发: backend-dev/*
前端开发: frontend-dev/*
测试: test/*

示例：
  backend-dev/auth-api  ✅
  frontend-dev/note-list ✅
  test/integration-auth ✅

请重新创建分支。
```

---

### 错误2: Commit message格式错误

**场景**:
```
git commit -m "add feature"
```

**Git Hook**:
```
[ERROR] Commit Message format is invalid!
Please follow: <type>: <description>

正确的格式：
  feat: 添加用户注册API
  fix: 修复登录验证错误
  docs: 更新API文档

❌ Commit已拒绝
```

---

## 📚 相关文档

- [Git Workflow详细说明](../../docs/09-workflow/GIT_WORKFLOW.md)
- [Team规范](../../docs/09-workflow/TEAMMATES_GUIDELINES.md)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

## 🔄 更新日志

- **2026-02-09**: 创建skill，包含完整的Git工作流
- 支持自动分支创建、提交、PR管理
- 集成Git hook自动检查

---

## 💡 最佳实践

1. **开始新功能前**
   ```
   git-workflow: daily start
   ```

2. **开发过程中**
   - 频繁提交（使用规范的commit message）
   - 每个功能点一个commit
   - 不要在功能分支上进行merge

3. **完成功能后**
   ```
   git-workflow: commit feat 完成功能
   git-workflow: push
   git-workflow: pr 功能说明
   ```

4. **每日结束**
   ```
   git-workflow: daily end
   ```

---

**Skill维护者**: team-lead
**最后更新**: 2026-02-09
