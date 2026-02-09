# Teammates工作规范

> 📌 **所有teammates必须遵守的工作规范**

## 🔴 强制要求

### 1. Git工作流（CRITICAL）

**必须严格遵守 [GIT_WORKFLOW.md](./GIT_WORKFLOW.md)**

#### 分支管理
```
✅ 必须从develop创建功能分支
✅ 分支命名必须符合规范:
   - backend-dev: backend-dev/功能名
   - frontend-dev: frontend-dev/功能名
   - test: test/测试类型

❌ 禁止直接在develop上提交
❌ 禁止直接在main上操作
```

#### Commit Message规范（自动检查）
```
必须格式: <type>: <description>

类型:
  feat     - 新功能
  fix      - Bug修复
  refactor - 代码重构
  docs     - 文档更新
  test     - 测试相关
  chore    - 构建/工具链
  perf     - 性能优化
  ci       - CI配置

示例:
  ✅ feat: 实现用户注册API
  ✅ fix: 修复登录验证错误
  ✅ docs: 更新README文档
  ❌ "add feature" (无类型)
  ❌ "update" (描述太简单)
```

**重要**: Git hook会自动检查commit格式，不符合将拒绝提交！

#### 合并策略
```
✅ 必须使用 "Squash and Merge"
✅ 必须创建Pull Request
✅ 必须通过code-reviewer审查
✅ 必须确保CI测试通过
```

### 2. 代码质量

#### 后端开发
```python
# ✅ 好的代码
def create_note(user_id: UUID, title: str, content: str) -> Note:
    """
    创建笔记

    Args:
        user_id: 用户ID
        title: 笔记标题
        content: 笔记内容

    Returns:
        创建的笔记对象

    Raises:
        ValueError: 参数验证失败
    """
    if not title or len(title) > 255:
        raise ValueError("标题长度必须在1-255之间")

    note = Note(user_id=user_id, title=title, content=content)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

# ❌ 坏的代码
def createNote(u, t, c):
    note = Note(u, t, c)
    db.add(note)
    db.commit()
    return note
```

**要求**:
- ✅ 使用类型注解
- ✅ 编写docstring
- ✅ 错误处理
- ✅ 遵循PEP 8规范

#### 前端开发
```typescript
// ✅ 好的代码
interface CreateNoteParams {
  userId: string;
  title: string;
  content: string;
}

/**
 * 创建笔记
 * @param params - 笔记参数
 * @returns 创建的笔记对象
 */
async function createNote(params: CreateNoteParams): Promise<Note> {
  if (!params.title || params.title.length > 255) {
    throw new Error('标题长度必须在1-255之间');
  }

  const response = await apiClient.post('/api/notes', params);
  return response.data;
}

// ❌ 坏的代码
function createNote(u: any, t: any, c: any) {
  return api.post('/notes', {u, t, c});
}
```

**要求**:
- ✅ 使用TypeScript类型
- ✅ 编写JSDoc注释
- ✅ 错误处理
- ✅ 遵循ESLint规则

### 3. 测试要求

```bash
# 后端测试
pytest --cov=app --cov-report=term-missing
要求: 覆盖率 > 80%

# 前端测试
npm test -- --coverage
要求: 覆盖率 > 80%
```

**TDD工作流**（test-specialist强制执行）:
1. ✅ 先写测试（RED）
2. ✅ 实现功能（GREEN）
3. ✅ 重构代码（REFACTOR）
4. ✅ 确保测试通过

### 4. Code Review流程

```
1. 创建Pull Request
   ↓
2. 填写PR模板（必须完整填写）
   ↓
3. code-reviewer自动审查
   ↓
4. 标记问题（CRITICAL/HIGH/MEDIUM/LOW）
   ↓
5. 开发者修复问题
   ↓
6. 审查通过后合并
```

**必须修复的问题**:
- 🔴 CRITICAL: 安全漏洞（SQL注入、XSS等）
- 🟠 HIGH: 重大bug、性能问题
- 🟡 MEDIUM: 代码质量问题
- 🟢 LOW: 代码风格、注释

---

## 📋 工作流程

### 每日工作流程

```
1. 早上:
   - 拉取最新代码: git pull origin develop
   - 查看任务列表
   - 向team-lead汇报今日计划

2. 开发中:
   - 创建功能分支
   - 遵循TDD写代码
   - 频繁提交（使用规范的commit message）

3. 完成:
   - 推送到远程: git push -u origin branch-name
   - 创建Pull Request
   - 通知code-reviewer审查

4. 晚间:
   - 向team-lead汇报进度
   - 更新任务状态
```

### 任务完成后

```
✅ 代码已合并到develop
✅ 功能分支已删除
✅ 相关文档已更新
✅ 测试全部通过
✅ 向team-lead确认任务完成
```

---

## ⚠️ 常见错误

### ❌ 错误示例

```bash
# 错误1: 直接在develop上工作
git checkout develop
git commit -m "add feature"  # ❌

# 正确做法
git checkout develop
git pull origin develop
git checkout -b backend-dev/auth-api
git commit -m "feat: 添加认证API"  # ✅

# 错误2: 不规范的commit message
git commit -m "update"  # ❌
git commit -m "fix bug"  # ❌

# 正确做法
git commit -m "feat: 添加用户注册接口"  # ✅
git commit -m "fix: 修复登录验证逻辑错误"  # ✅

# 错误3: 不写测试
def create_note():
    pass  # ❌ 直接写功能

# 正确做法（TDD）
# 1. 先写测试
def test_create_note():
    note = create_note(user_id=1, title="Test", content="Content")
    assert note.id is not None

# 2. 再实现功能
def create_note(user_id, title, content):
    # 实现...
    pass  # ✅
```

---

## 🔧 工具配置

### Git别名（推荐配置）

```bash
# 添加到 ~/.gitconfig
[alias]
  st = status
  co = checkout
  br = branch
  ci = commit
  unstage = reset HEAD --
  last = log -1 HEAD
  amend = commit --amend --no-edit
```

### VSCode配置

```json
{
  "git.enableCommitSigning": true,
  "git.postCommitCommand": "none",
  "editor.formatOnSave": true
}
```

---

## 📊 进度报告

### 每日必须报告

向team-lead汇报：

1. **今日完成**
   - 完成的任务
   - 提交的commits
   - 创建的PRs

2. **遇到的问题**
   - 技术难点
   - 依赖阻塞
   - 需要协助

3. **明日计划**
   - 计划任务
   - 预计完成时间

---

## ✅ 检查清单

在提交代码前，必须确认：

- [ ] Git分支符合命名规范
- [ ] Commit Message符合格式
- [ ] 代码通过所有测试
- [ ] 测试覆盖率 > 80%
- [ ] 代码有适当的注释
- [ ] 已更新相关文档
- [ ] 已创建Pull Request
- [ ] PR描述完整填写

---

**最后更新**: 2026-02-09
**强制执行**: team-lead
**违反后果**: 代码将被拒绝合并，任务重新分配
