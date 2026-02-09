# Teammates工作规范

> 📌 **所有teammates必须遵守的工作规范**

## 🔴 强制要求

### 0. ⏱️ 时间控制规则（CRITICAL - 所有teammates必须遵守）

#### 📌 基本规则

**适用对象**：所有teammates（包括team-lead）

**核心规则**：
```
单个任务最长时间：30分钟
```

#### 🔄 30分钟后的强制流程

**第一步：立即停止当前工作**
- 停止所有编码工作
- 无论任务是否完成
- 不要"再写一点"

**第二步：向team-lead报告进度**

格式示例：
```
📊 任务进度报告
✅ 已完成：用户注册API的endpoint定义
🔄 进行中：密码验证逻辑（完成50%）
📋 遗留：邮箱验证功能待开发
⏱️ 用时：30分钟
🚧 阻塞：无
```

**第三步：Git管理未完成代码**

```bash
# 1. 保存所有更改
git add .

# 2. 提交进度（带详细说明）
git commit -m "wip: 用户认证模块开发进度

已完成：
- POST /api/auth/register endpoint
- 基本表单验证

进行中：
- 密码哈希处理（50%完成）
- 已实现bcrypt集成
- 待添加salt rounds配置

待完成：
- 邮箱验证功能
- JWT token生成
- 单元测试编写

下一步计划：
1. 完成密码哈希逻辑
2. 实现邮箱验证endpoint
3. 编写单元测试（目标覆盖率>80%）
"

# 3. 推送到远程保存工作
git push -u origin backend-dev/user-auth
```

**第四步：更新TaskList状态**

- 将未完成任务标记为 `in_progress`
- 在描述中添加详细进度说明
- 记录下一步计划

#### 🛑 team-lead停止命令

**停止命令含义**：
```
team-lead: "今日停止" 或 "停止工作"
↓
这意味着：下班了
```

**收到停止命令后必须执行**：

1. **立即停止**所有开发工作
   - 不允许"再写一点"
   - 不允许"再完成这个函数"

2. **向team-lead报告任务完成情况**
   ```
   今日完成清单：
   ✅ 用户注册API（已完成）
   ✅ 登录验证逻辑（已完成）

   未完成任务及进度：
   🔄 笔记列表API - 60%完成
      - 已实现：基础查询、数据库连接
      - 待完成：分页逻辑、过滤条件

   🔄 OCR集成 - 30%完成
      - 已完成：百度OCR SDK配置
      - 待完成：图片上传处理、结果解析

   遇到的问题：
   ⚠️ 百度OCR API响应较慢，需优化
   ```

3. **Git管理所有工作**
   ```bash
   git add .
   git commit -m "wip: 2026-02-09 工作进度

   今日完成：
   ✅ 用户注册API（已完成）
      - endpoint: POST /api/auth/register
      - 验证逻辑完整
      - 单元测试通过

   ✅ 登录验证逻辑（已完成）
      - JWT生成正确
      - 密码哈希验证通过

   未完成进度：
   🔄 笔记列表API - 60%完成
      - 已实现：基础查询、数据库连接
      - 待完成：分页逻辑、过滤条件、排序

   🔄 OCR集成 - 30%完成
      - 已完成：百度OCR SDK配置、API密钥设置
      - 待完成：图片上传endpoint、结果解析

   下次开发计划：
   1. 完成笔记列表分页逻辑
   2. 实现图片上传endpoint
   3. OCR结果解析和存储
   4. 编写单元测试（当前覆盖率：65%）
   "

   git push
   ```

4. **更新TaskList**
   - 标记已完成任务状态为 `completed`
   - 记录未任务的详细进度
   - 明确下次继续的起点

#### ▶️ 继续开发流程

**只有收到team-lead的继续指令后才能恢复开发**：

```bash
# team-lead评估进度后下发继续指令
# teammate从git记录恢复：

git pull origin develop
git checkout backend-dev/user-auth
git pull

# 查看上次commit message了解进度
git log -1 --pretty=format:"%B"

# 继续未完成的工作
```

#### ⚠️ 违规后果

**不遵守30分钟规则**：
```
第1次：⚠️ 警告
第2次：🔄 任务重新分配
第3次：❌ 从团队移除
```

**不遵守停止命令**：
```
立即：
- ❌ 停止所有开发权限
- ❌ 代码不被合并
- ❌ 从团队移除
```

#### 📋 示例完整流程

**场景：backend-dev正在开发用户认证API**

```
00:00 - 开始任务：实现用户注册API
00:25 - 进行中：密码哈希处理
00:30 - ⏰ 30分钟到！

✅ 执行30分钟流程：
1. 停止编码
2. 向team-lead报告进度
3. git add . && git commit -m "wip: 详细进度..."
4. git push
5. 更新TaskList

team-lead评估后："可以继续"
backend-dev继续开发...

00:55 - 再次30分钟
再次报告进度...

01:20 - team-lead: "今日停止"
✅ 立即执行停止流程
✅ 报告今日完成情况
✅ Git管理所有工作
✅ 下班
```

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
