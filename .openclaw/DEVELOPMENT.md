# 开发准则

## Git 提交规范

### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| Type | 说明 |
|------|------|
| feat | 新功能 |
| fix | Bug 修复 |
| docs | 文档更新 |
| style | 代码格式（不影响逻辑） |
| refactor | 重构 |
| perf | 性能优化 |
| test | 测试相关 |
| chore | 构建/工具相关 |
| sync | git-sync 同步操作 |

### 示例

```bash
feat(auth): 添加用户登录功能

- 实现 JWT 认证
- 添加登录页面
- 集成第三方登录

Closes #123
```

---

## 分支命名规范

| 分支类型 | 命名格式 | 示例 |
|----------|----------|------|
| 主分支 | main / master | main |
| 开发分支 | develop | develop |
| 功能分支 | feature/<name> | feature/user-auth |
| 修复分支 | fix/<name> | fix/login-bug |
| 发布分支 | release/<version> | release/v1.0.0 |
| 热修复 | hotfix/<name> | hotfix/critical-bug |

---

## Memory 写作规范

### MEMORY.md（长期记忆）

记录**重要且持久**的信息：

- 项目架构设计
- 重要技术决策及原因
- 关键接口/API 说明
- 长期待办事项
- 踩坑记录和解决方案

**格式：**

```markdown
# MEMORY.md

## 项目概述
<!-- 项目简介、技术栈、目标 -->

## 架构设计
<!-- 核心架构、模块划分 -->

## 重要决策
<!-- 决策内容、原因、时间 -->

## 技术债务
<!-- 已知问题、待优化项 -->

## 工作状态
<!-- 当前工作状态，用于跨环境恢复 -->
```

### memory/YYYY-MM-DD.md（每日日志）

记录**当天**的工作：

- 今日完成的任务
- 遇到的问题和解决方案
- 明日计划

**格式：**

```markdown
# 2026-04-06 工作日志

## 今日任务
- [ ] 任务1
- [x] 任务2（已完成）

## 完成事项
- 完成了 XX 功能

## 遇到的问题
- 问题：XXX
- 解决：XXX

## 明日计划
- 继续开发 XX
```

### memory/tasks.md（待办事项）

记录**待处理**的任务：

```markdown
# 待办事项

## 进行中
- 当前正在做的任务

## 待处理
- 优先级高的任务
- 优先级低的任务

## 已完成
- 已完成的任务（可定期清理）
```

### memory/context.md（当前上下文）

记录**当前工作**的上下文，用于恢复状态：

```markdown
# 当前工作上下文

## 当前任务
<!-- 正在做什么 -->

## 相关文件
<!-- 涉及哪些文件 -->

## 注意事项
<!-- 需要特别注意的内容 -->

## 下一步
<!-- 接下来要做什么 -->
```

---

## 协同工作流约定

### 开始工作前

```bash
# 1. 同步最新代码
./.openclaw/skills/git-sync/scripts/git-sync.sh sync

# 2. 查看状态
./.openclaw/skills/git-sync/scripts/git-sync.sh status
```

### 工作中

```bash
# 定期创建检查点（每完成一个阶段性任务）
./.openclaw/skills/git-sync/scripts/git-sync.sh checkpoint "完成了 XX 模块"
```

### 结束工作时

```bash
# 1. 更新 Memory
# 2. 同步所有修改
./.openclaw/skills/git-sync/scripts/git-sync.sh sync
```

### 切换环境时

```bash
# 在新环境恢复工作状态
./.openclaw/skills/git-sync/scripts/git-sync.sh resume
```

---

## 禁止事项

1. ❌ 不要在 Memory 文件中写入敏感信息（密码、密钥等）
2. ❌ 不要直接在 main 分支开发，使用 feature 分支
3. ❌ 不要提交未测试的代码
4. ❌ 不要覆盖他人的 Memory 更新（冲突时先沟通）

---

## 最佳实践

1. ✅ 每次开始工作前先 sync
2. ✅ 完成阶段性任务后创建 checkpoint
3. ✅ 结束工作时确保所有修改已推送
4. ✅ 定期清理已完成的 tasks
5. ✅ 保持 Memory 文件简洁，只记录重要信息
