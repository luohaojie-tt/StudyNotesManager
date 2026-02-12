# Frontend Team任务分配

> **日期**: 2026-02-09
> **目标**: 修复4个CRITICAL + 6个HIGH安全问题
> **期限**: CRITICAL今天完成，HIGH本周完成

---

## Team成员

### frontend-dev (蓝色)
**专长**: 认证系统、API集成、安全机制

**分配任务**:
1. ✅ **#40**: Token存储迁移到httpOnly cookie (3h) - CRITICAL
2. ✅ **#43**: 修复Token过期处理 (1h) - HIGH

### frontend-dev-2 (紫色)
**专长**: 组件开发、用户体验、表单处理

**分配任务**:
1. ✅ **#39**: 移除硬编码用户ID和API URL (1h) - CRITICAL
2. ✅ **#42**: 修复类型安全问题 (2h) - HIGH

### frontend-dev-3 (粉色)
**专长**: Quiz功能、状态管理、逻辑处理

**分配任务**:
1. ✅ **#44**: 添加CSRF保护 (1.5h) - CRITICAL
2. ✅ **#41**: 修复Quiz答案比较逻辑 (1h) - HIGH

---

## 工作流程

### 1. 报告周期
- **频率**: 每30分钟报告一次进度
- **格式**:
  ```
  [任务ID] 任务名称: XX%
  - 完成项: ✅ ...
  - 进行中: 🔄 ...
  - 阻塞问题: ⚠️ ...
  - 预计完成时间: ...
  ```

### 2. 协作规则
- ✅ 独立任务可并行执行
- ✅ 有依赖的任务等待依赖完成
- ✅ 遇到问题立即沟通
- ✅ 代码完成后使用code-reviewer验证

### 3. 优先级
1. 🔴 **CRITICAL** (今天必须完成)
   - Token存储迁移
   - 硬编码移除
   - CSRF保护
2. 🟠 **HIGH** (本周完成)
   - Token过期处理
   - 类型安全
   - Quiz逻辑修复

---

## 任务详细说明

### #40: Token存储迁移 (最高优先级)

**为什么CRITICAL**:
- localStorage可被XSS攻击读取
- JWT token一旦泄露，攻击者可完全控制用户账户
- httpOnly cookie无法被JavaScript访问，安全得多

**Backend已完成**:
- ✅ 设置Set-Cookie header with httpOnly flag
- ✅ Secure, SameSite=Strict attributes

**Frontend需要做**:
1. ❌ 删除所有localStorage token操作
2. ❌ 移除Authorization header
3. ❌ 删除用户数据localStorage存储
4. ❌ 只在内存中存储session

**文件位置**:
- `frontend/src/contexts/AuthContext.tsx`
- `frontend/src/lib/api-client.ts`

**验证方法**:
```bash
# 测试登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' \
  -c cookies.txt -v

# 检查cookie是否设置
grep "token" cookies.txt

# 测试API调用
curl http://localhost:8000/api/auth/me \
  -b cookies.txt -v
```

---

### #39: 移除硬编码值

**风险**:
- "placeholder"用户ID绕过认证
- localhost fallback可能连接错误服务器
- 生产环境可能暴露开发配置

**修复方案**:
```typescript
// ❌ 当前 (不安全)
const userId = "placeholder"

// ✅ 修复后
const { user } = useAuth()
if (!user?.id) {
  throw new Error("User not authenticated")
}
const userId = user.id
```

**API URL修复**:
```typescript
// ❌ 当前
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

// ✅ 修复后
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || (
  process.env.NODE_ENV === 'development'
    ? 'http://localhost:8000/api'
    : (() => { throw new Error('NEXT_PUBLIC_API_URL required in production') })()
)
```

---

### #44: CSRF保护

**为什么需要**:
- 虽然有httpOnly cookie，但仍然可能受CSRF攻击
- 攻击者可以构造恶意网站发送跨域请求

**实现方案**:
1. Backend设置XSRF-TOKEN cookie (non-httpOnly)
2. Frontend读取该cookie
3. 添加X-CSRF-Token header到所有mutation请求

**代码示例**:
```typescript
// 读取CSRF token
const getCsrfToken = (): string | null => {
  const match = document.cookie.match(/XSRF-TOKEN=([^;]+)/)
  return match ? match[1] : null
}

// 添加到请求
apiClient.interceptors.request.use((config) => {
  if (['post', 'put', 'delete', 'patch'].includes(config.method ?? '')) {
    const csrfToken = getCsrfToken()
    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken
    }
  }
  return config
})
```

---

### #43: Token过期处理

**用户体验问题**:
- Token过期后API调用失败，但用户不知道
- 继续操作会连续失败

**解决方案**:
```typescript
apiClient.interceptors.response.use(
  response => response,
  async (error) => {
    if (error.response?.status === 401) {
      // 清除认证状态
      await authContext.logout()
      // 重定向到登录页
      router.push('/login?reason=session_expired')
      // 显示提示
      toast.info('Session已过期，请重新登录')
    }
    return Promise.reject(error)
  }
)
```

---

### #42: 类型安全

**为什么重要**:
- `any`类型破坏TypeScript类型检查
- 运行时错误难以发现
- IDE无法提供准确的自动完成

**主要问题**:
- API响应类型不明确
- 组件props使用any
- 事件处理器参数类型

**修复方法**:
```typescript
// ❌ 当前
const data: any = response.data

// ✅ 修复后
interface ApiResponse<T> {
  success: boolean
  data: T
  error?: string
}

interface Quiz {
  id: string
  title: string
  questions: Question[]
}

const response: ApiResponse<Quiz> = await apiClient.get('/quizzes')
const data = response.data
```

---

### #41: Quiz答案比较逻辑

**Bug描述**:
- multiple-select类型答案比较不正确
- 当前使用简单字符串比较，不考虑顺序

**修复方案**:
```typescript
const getIsCorrect = (question: Question, answer: string): boolean => {
  if (question.type === 'multiple-select') {
    // 分割、排序、比较
    const userAnswers = answer.split(',')
      .map(a => a.trim())
      .sort()
    const correctAnswers = question.correctAnswer.split(',')
      .map(a => a.trim())
      .sort()
    return JSON.stringify(userAnswers) === JSON.stringify(correctAnswers)
  }
  return answer.trim().toLowerCase() === question.correctAnswer.trim().toLowerCase()
}
```

---

## 验证清单

每个任务完成后必须验证：

### 安全验证
- [ ] 无localStorage存储敏感数据
- [ ] Token使用httpOnly cookie
- [ ] CSRF token正确发送
- [ ] 无硬编码认证信息

### 功能验证
- [ ] 登录流程正常
- [ ] 登出流程正常
- [ ] Token过期自动登出
- [ ] 页面刷新session保持
- [ ] Quiz答案判断正确

### 代码质量验证
- [ ] TypeScript编译无错误
- [ ] 无`any`类型残留
- [ ] 无console.log
- [ ] 代码符合规范

---

## 时间表

### 今天 (2026-02-09)
- ✅ 9:00-12:00: CRITICAL任务修复
- ✅ 13:00-15:00: CRITICAL任务测试
- ✅ 15:00-17:00: code-reviewer验证
- ✅ 17:00-18:00: 修复review发现的问题

### 本周
- 周二-周三: HIGH问题修复
- 周四: 集成测试
- 周五: code-reviewer最终验证

### 下周
- MEDIUM问题修复
- 性能优化
- 文档更新

---

## 紧急联系

如遇到阻塞问题，立即联系team-lead：
- Backend问题 → 联系backend-dev
- API规范问题 → 查看API文档
- 测试问题 → 联系test-specialist

---

**文档创建**: team-lead
**最后更新**: 2026-02-09
**状态**: 🔴 活跃执行中
