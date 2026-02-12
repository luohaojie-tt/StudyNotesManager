# Frontend Team快速参考卡

> 📌 打印此卡片并放在显眼位置

---

## 🚨 今日CRITICAL任务（必须完成！）

### 🔵 frontend-dev
```
任务: Token存储迁移到httpOnly cookie
文件: frontend/src/contexts/AuthContext.tsx
时间: 2-3小时
关键: 删除所有localStorage token操作
```

### 🟣 frontend-dev-2
```
任务: 移除硬编码用户ID和API URL
文件: frontend/src/app/quizzes/page.tsx
时间: 1小时
关键: 使用真实用户ID，验证API URL
```

### 🩷 frontend-dev-3
```
任务: 添加CSRF保护
文件: frontend/src/lib/api-client.ts
时间: 1.5小时
关键: 读取XSRF-TOKEN cookie，添加header
```

---

## ⏰ 报告时间
每30分钟: `10:00, 10:30, 11:00, 11:30, 14:00, 14:30, 15:00...`

报告格式:
```
[任务ID] 进度: XX%
✅ 完成: ...
🔄 进行中: ...
⚠️ 阻塞: ...
📅 完成: XX:XX
```

---

## 🆘 紧急联系
- 阻塞问题 → 立即联系team-lead
- Backend问题 → 联系backend-dev
- API规范 → 查看文档

---

## ✅ 完成检查
- [ ] 无localStorage存储敏感数据
- [ ] 使用httpOnly cookie
- [ ] 无硬编码值
- [ ] CSRF token正确发送
- [ ] 功能测试通过
- [ ] Code reviewer验证通过

---

## 📚 详细文档
- 任务说明: `docs/09-workflow/FRONTEND_TEAM_ASSIGNMENT.md`
- 问题清单: `docs/09-workflow/FRONTEND_FIX_TASKS.md`

---

*今天必须完成所有CRITICAL任务！💪*
