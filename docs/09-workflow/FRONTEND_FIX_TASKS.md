# Frontend Code Review Issues - 修复任务清单

> 📌 **重要提示**: 这些问题来自code-reviewer agents的审查结果

**分配给**: frontend-dev, frontend-dev-2, frontend-dev-3
**创建日期**: 2026-02-09
**优先级**: 🔴 CRITICAL > 🟠 HIGH > 🟡 MEDIUM

---

## 🔴 CRITICAL问题（必须立即修复）

### 1. Token存储在localStorage - XSS漏洞

**文件**: `frontend/src/contexts/AuthContext.tsx:31-32,60-61,80-81,100-101,112`
**问题**: JWT token存储在localStorage，XSS攻击可窃取
**修复**:
- ❌ 删除localStorage存储token的代码
- ✅ 后端设置httpOnly cookie
- ✅ 前端移除Authorization header处理
- ✅ Cookie自动发送，无需前端代码

### 2. 用户数据存储在localStorage

**文件**: `frontend/src/contexts/AuthContext.tsx:61,81,112`
**问题**: 敏感用户数据存储在localStorage
**修复**:
- 只在内存中存储必要session状态
- 页面刷新后从API重新获取

### 3. 硬编码API URL

**文件**: `frontend/src/lib/api-client.ts:4`
**问题**: localhost fallback可能在生产环境导致问题
**修复**:
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || (
  process.env.NODE_ENV === 'development'
    ? 'http://localhost:8000/api'
    : (() => { throw new Error('NEXT_PUBLIC_API_URL required') })()
)
```

### 4. 硬编码用户ID（placeholder）

**文件**: `frontend/src/app/quizzes/page.tsx:89`
**问题**: 使用`placeholder`绕过认证
**修复**: 从认证context获取真实user ID

### 5. ✅ 缺少CSRF保护 - 已完成

**文件**: 所有POST请求
**问题**: API请求缺少CSRF token
**修复**:
- ✅ 从cookie获取CSRF token
- ✅ 添加到所有mutation请求headers
- ✅ 实施日期: 2026-02-09
- ✅ 负责人: frontend-dev-3
- **详细报告**: `docs/09-workflow/CSRF_PROTECTION_IMPLEMENTATION.md`

### 6. dangerouslySetInnerHTML使用

**文件**: `frontend/src/components/ui/chart.tsx:83`
**问题**: 虽然当前内容安全，但这是危险模式
**修复**:
- 确保无用户输入
- 考虑使用CSS-in-JS替代

---

## 🟠 HIGH问题（应当修复）

### 1. 类型安全 - 大量使用`any`

**文件**: 多个文件
**问题**: TypeScript类型安全被破坏
**修复**:
- 移除所有`any`类型
- 定义明确的接口

### 2. 缺少Token过期处理

**文件**: `frontend/src/contexts/AuthContext.tsx`
**问题**: 过期token不处理
**修复**:
- 实现401响应拦截器
- 自动登出并重定向到登录页

### 3. 错误处理不完善

**文件**: `frontend/src/lib/api-client.ts:31-34`
**问题**: 错误消息直接显示给用户，可能泄露信息
**修复**:
- 记录详细错误到日志
- 显示用户友好的通用消息

### 4. URL参数未验证

**文件**: `frontend/src/app/notes/[id]/page.tsx:30-32`
**问题**: URL参数直接使用未验证
**修复**: 验证UUID格式

### 5. ✅ 答案比较逻辑错误 - 已完成

**文件**: `frontend/src/components/quiz/QuizTakingInterface.tsx:125-127`
**问题**: multiple-select类型答案比较逻辑不正确
**修复**:
```typescript
const getIsCorrect = (question: Question, answer: string): boolean => {
  if (question.type === 'multiple-select') {
    // For multiple-select, compare sorted arrays
    const userAnswers = answer.split(',').map(a => a.trim()).filter(a => a)
    const correctAnswers = question.correctAnswer.split(',').map(a => a.trim()).filter(a => a)
    if (userAnswers.length !== correctAnswers.length) return false
    const sortedUser = [...userAnswers].sort()
    const sortedCorrect = [...correctAnswers].sort()
    return sortedUser.every((val, idx) => val === sortedCorrect[idx])
  }
  // For other types, use case-insensitive string comparison
  return answer.trim().toLowerCase() === question.correctAnswer.trim().toLowerCase()
}
```
**实施日期**: 2026-02-09
**负责人**: frontend-dev-3

### 6. ✅ QuizTimer依赖问题 - 已完成

**文件**: `frontend/src/components/quiz/QuizTimer.tsx:23-46`
**问题**: 依赖数组包含`isWarning`和`onTimeUp`，可能导致无限循环
**修复**:
```typescript
// Store callback in ref to prevent infinite loops
const onTimeUpRef = useRef(onTimeUp)
const hasTriggeredRef = useRef(false)

// Update ref when callback changes
useEffect(() => {
  onTimeUpRef.current = onTimeUp
}, [onTimeUp])

// Remove onTimeUp and isWarning from dependency array
useEffect(() => {
  if (isPaused || timeLeft <= 0 || hasTriggeredRef.current) return
  // ... timer logic
}, [timeLeft, isPaused, isWarning])
```
**实施日期**: 2026-02-09
**负责人**: frontend-dev-3

---

## 🟡 MEDIUM问题（建议改进）

### 1. console.log语句残留

**文件**: 20+处
**修复**: 创建logger工具，生产环境禁用

### 2. 缺少Content Security Policy

**文件**: `frontend/src/app/layout.tsx`
**修复**: 在next.config.js添加CSP headers

### 3. 缺少Error Boundary

**文件**: 整个应用
**修复**:
- 创建ErrorBoundary组件
- 包裹主要路由

### 4. 搜索输入无debounce

**文件**: `frontend/src/components/notes/NotesFilter.tsx:31-34`
**修复**: 添加500ms debounce

### 5. 缺少加载状态

**文件**: `frontend/src/app/quizzes/page.tsx:54-78`
**修复**: 添加loading状态和disabled按钮

### 6. 使用window.location.href

**文件**: `frontend/src/app/quizzes/page.tsx:169`
**修复**: 使用Next.js router

---

## 📊 组件复杂度问题

### QuizTakingInterface过于复杂

**文件**: `frontend/src/components/quiz/QuizTakingInterface.tsx` (352行)
**建议**: 拆分为多个组件和hooks

**修复方案**:
```
hooks/useQuizState.ts - 管理quiz状态
hooks/useQuizTimer.ts - 管理计时器
hooks/useQuizNavigation.ts - 管理导航
components/quiz/QuizQuestionCard.tsx - 问题卡片
components/quiz/QuizNavigation.tsx - 导航控制
```

---

## 📝 修复优先级

### 阶段1: 安全关键（今天）
1. ✅ **Token存储迁移到httpOnly cookie**（最高优先级）
2. ✅ 移除硬编码用户ID
3. ✅ 添加CSRF保护
4. ✅ 修复硬编码API URL

### 阶段2: 稳定性（本周）
1. 修复所有HIGH问题（6个）
2. 添加Token过期处理
3. 修复类型安全问题
4. 修复QuizTimer依赖问题

### 阶段3: 用户体验（下周）
1. 修复MEDIUM问题
2. 添加Error Boundary
3. 添加CSP headers
4. 改进组件设计

---

## ✅ 验证标准

修复后的代码必须：
- [ ] 无localStorage存储敏感数据
- [ ] 使用httpOnly cookie存储token
- [ ] 所有`any`类型已替换
- [ ] 无console.log在production代码
- [ ] 通过TypeScript strict检查
- [ ] 无CRITICAL安全问题残留

---

## 🎯 具体修复示例

### Token存储迁移

**当前代码（不安全）**:
```typescript
// AuthContext.tsx
localStorage.setItem('token', userToken)
const token = localStorage.getItem('token')
```

**修复后（安全）**:
```typescript
// 删除localStorage代码
// 后端设置cookie:
// Set-Cookie: token=<jwt>; HttpOnly; Secure; SameSite=Strict; Path=/
// 前端无需任何代码，cookie自动发送
```

### 类型安全修复

**当前代码**:
```typescript
const data: any = response.data
```

**修复后**:
```typescript
interface ApiResponse<T> {
  data: T
  error?: string
}

const response: ApiResponse<Quiz> = await apiClient.get('/quizzes')
const data = response.data
```

---

## 📚 参考资料

- Frontend Security Best Practices
- OWASP Top 10 for Frontend
- Next.js Security Guidelines
- React TypeScript Patterns

---

**任务分配人**: team-lead
**执行人**: frontend-dev, frontend-dev-2, frontend-dev-3
**状态**: 🔴 待开始
