# Claude Code 高级用法与人性化协作指南

**——让 AI 成为真正懂你的编程伙伴**

---

> *"工欲善其事，必先利其器。但真正的利器不是工具本身，而是你与工具之间的默契。"*
>
> —— 来自 10 个月深度使用 Claude Code 的开发者

---

## 📋 目录

- [前言：为什么要学高级用法？](#前言为什么要学高级用法)
- [第一章：CLAUDE.md —— 给 AI 注入项目"灵魂"](#第一章claudemd-给-ai-注入项目灵魂)
- [第二章：Hooks —— 让 Claude 自动遵守你的规则](#第二章hooks-让-claude-自动遵守你的规则)
- [第三章：Skills —— 打造你的专属 AI 技能库](#第三章skills-打造你的专属-ai-技能库)
- [第四章：MCP —— 连接外部世界的桥梁](#第四章mcp-连接外部世界的桥梁)
- [第五章：上下文管理 —— 让 Claude 记住重要的事](#第五章上下文管理-让-claude-记住重要的事)
- [第六章：高级命令与工作流](#第六章高级命令与工作流)
- [第七章：大佬实战经验分享](#第七章大佬实战经验分享)
- [第八章：常见问题与避坑指南](#第八章常见问题与避坑指南)

---

## 前言：为什么要学高级用法？

Claude Code 不只是一个代码补全工具，它是一个**系统级 AI Agent**。如果你只用它来写代码片段，就像买了辆跑车只用来买菜。

### 这篇文档能帮你做到什么

| 使用层次 | 效率提升 | 工作流对齐度 | 说明 |
|---------|---------|-------------|------|
| **基础对话模式** | +15% | 30% | 问什么答什么，需要频繁纠正 |
| **增强协作模式** | +24% | 76% | 配置 CLAUDE.md + 基础 Hooks |
| **自动化模式** | -17% ⚠️ | 40% | 全交给 AI 反而效率下降 |
| **精通协作模式** | +50%+ | 90%+ | Hooks + Skills + MCP 完整配置 |

> 💡 **核心洞察**：Claude Code 的真正威力不在于"完全自动化"，而在于**人机协作的无缝衔接**。你需要教会它理解你的工作方式，而不是期望它自动完美。

---

## 第一章：CLAUDE.md —— 给 AI 注入项目"灵魂"

### 1.1 什么是 CLAUDE.md？

`CLAUDE.md` 是 Claude Code 自动读取的记忆文件，类似 Cursor 的 `rules`，但更强大。它为 Claude 提供项目相关的上下文信息，让它**真正理解**你的项目。

### 1.2 CLAUDE.md 的三层架构

| 层级 | 路径 | 作用 | 示例内容 |
|-----|------|------|---------|
| **项目记忆（共享）** | `./CLAUDE.md` | 团队共享的指令 | 项目架构、编码规范、常用工作流程 |
| **用户记忆（全局）** | `~/.claude/CLAUDE.md` | 所有项目的个人偏好 | 代码风格偏好、个人工具快捷方式 |
| **目录记忆（嵌套）** | 各目录的 `CLAUDE.md` | 特定模块的上下文 | 模块说明、依赖关系 |

Claude Code 会**递归读取**这些文件：从当前工作目录开始，向上递归到根目录。

### 1.3 一个好的 CLAUDE.md 长什么样？

```markdown
# 项目名称 - AI 协作上下文

## 项目概述
- **技术栈**: Python 3.11 + FastAPI + PostgreSQL + Redis
- **架构风格**: 微服务，事件驱动
- **当前阶段**: MVP 开发阶段

## 核心架构
```
src/
├── api/          # API 路由层
├── services/     # 业务逻辑层
├── models/       # 数据模型
├── utils/        # 工具函数
└── tests/        # 测试（与源码镜像）
```

## 编码规范
- 使用 **类型注解**（Python 3.11+）
- 函数必须有 docstring（Google 风格）
- 测试框架：pytest，目标覆盖率 80%
- 提交格式：`feat|fix|refactor: 简洁描述`

## 常用命令
- `make dev` - 启动开发服务器
- `make test` - 运行测试
- `make lint` - 代码检查

## 禁止事项
- ❌ 不要在生产代码中使用 `print()`，使用 `logging`
- ❌ 不要修改 `migrations/` 中的历史迁移文件
- ❌ 不要在测试中使用真实数据库连接

## 当前工作重点
- [ ] 用户认证模块重构
- [ ] 性能优化（关注 N+1 查询）
- [ ] API 文档补充
```

### 1.4 CLAUDE.md 最佳实践

#### ✅ 要做的：
1. **保持精简**：控制在 300 行以内，太长反而降低效果
2. **持续更新**：把它当作活文档，随项目演进
3. **模块化结构**：复杂项目可以拆分多个文件
4. **明确优先级**：把最重要的规则放在前面

#### ❌ 不要做的：
1. **堆砌技术细节**：代码本身就是细节，CLAUDE.md 应该是"元信息"
2. **写太泛的规则**："写高质量代码" —— 这种话 Claude 不需要
3. **忽略更新**：过期的信息比没有信息更糟糕

### 1.5 Boris Pro Tip：CLAUDE.md 的灵魂

> **Boris Cherny（Claude Code 之父）在 X 上分享**：
> 
> "我的 CLAUDE.md 开头永远是一句话：**这个项目的核心目标是什么**。这样当 Claude 面临选择时，它能做出和我一致的判断。"
> 
> 例如：`这是一个追求极致性能的实时系统，性能优先于代码可读性。`

---

## 第二章：Hooks —— 让 Claude 自动遵守你的规则

### 2.1 Hooks 是什么？

Hooks 是 Claude Code 的**自动化规则引擎**。它可以在特定事件发生时自动执行脚本，确保代码始终符合你的标准。

### 2.2 四种 Hook 类型

| Hook 类型 | 触发时机 | 典型用途 |
|----------|---------|---------|
| `PreToolUse` | Claude 使用工具之前 | 权限检查、参数验证 |
| `PostToolUse` | Claude 使用工具之后 | 自动格式化、lint 检查 |
| `Notification` | Claude 需要你注意时 | 桌面通知、Slack 通知 |
| `Stop` | Claude 完成任务时 | 清理工作、状态记录 |

### 2.3 实战案例：自动代码格式化

**场景**：每次 Claude 修改 TypeScript 文件后，自动运行 Prettier。

**配置 `.claude/settings.json`**：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": {
          "toolName": "Edit|Write",
          "filePath": ".*\\.(ts|tsx)$"
        },
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write"
          }
        ]
      }
    ]
  }
}
```

### 2.4 实战案例：保护关键文件

**场景**：防止 Claude 意外修改生产配置文件。

**创建脚本 `.claude/hooks/protect-files.sh`**：

```bash
#!/bin/bash
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# 保护列表
PROTECTED_FILES=(
  ".env.production"
  "config/database.yml"
  "terraform/main.tf"
)

for protected in "${PROTECTED_FILES[@]}"; do
  if [[ "$FILE_PATH" == *"$protected"* ]]; then
    echo "❌ 受保护文件，需要人工确认：$FILE_PATH"
    exit 2  # 阻止操作
  fi
done

exit 0
```

**并在 settings.json 中注册**：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": { "toolName": "Edit|Write" },
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh"
          }
        ]
      }
    ]
  }
}
```

### 2.5 实战案例：桌面通知

**macOS 配置**：

```json
{
  "hooks": {
    "Notification": [
      {
        "type": "command",
        "command": "osascript -e 'display notification \"Claude Code needs your attention\" with title \"Claude Code\"'"
      }
    ]
  }
}
```

**Linux 配置**：

```json
{
  "hooks": {
    "Notification": [
      {
        "type": "command",
        "command": "notify-send \"Claude Code\" \"需要你的确认\""
      }
    ]
  }
}
```

---

## 第三章：Skills —— 打造你的专属 AI 技能库

### 3.1 什么是 Skills？

Skills 是 Claude Code 的**能力扩展包**。你可以把它理解为"给 Claude 安装新技能"。一个 Skill 包含：

- **SKILL.md**：技能描述和使用说明
- **scripts/**：自动执行的脚本
- **references/**：参考资料和模板

### 3.2 官方 Skills 推荐

| Skill | 用途 | 安装命令 |
|-------|-----|---------|
| `frontend-design` | 前端设计和组件开发 | `npx skills-installer install @anthropics/claude-code/frontend-design` |
| `doc-coauthoring` | 文档协作写作 | `npx skills-installer install @anthropics/claude-code/doc-coauthoring` |
| `commit` | 智能提交信息生成 | `npx skills-installer install @anthropics/claude-code/commit` |
| `test-writer` | 自动生成测试 | `npx skills-installer install @anthropics/claude-code/test-writer` |
| `pdf` | PDF 文档处理 | `npx skills-installer install @anthropics/claude-code/pdf` |

### 3.3 创建自定义 Skill

**场景**：创建一个代码审查 Skill。

**目录结构**：

```
.claude/skills/code-review/
├── SKILL.md
├── scripts/
│   └── analyze.sh
└── references/
    └── review-checklist.md
```

**SKILL.md 内容**：

```markdown
---
name: code-review
description: 代码审查技能，自动检查代码质量、安全性和最佳实践
---

# Code Review Skill

## 使用场景
- 提交 PR 前自动审查
- 定期代码质量检查
- 新成员代码指导

## 触发方式
在对话中提到 "代码审查"、"review" 或使用 `/code-review` 命令。

## 审查维度
1. **代码质量**：命名、结构、复杂度
2. **安全性**：SQL 注入、XSS、敏感信息泄露
3. **性能**：N+1 查询、内存泄漏、不必要的循环
4. **可维护性**：注释、文档、测试覆盖

## 输出格式
参见 references/review-checklist.md
```

---

## 第四章：MCP —— 连接外部世界的桥梁

### 4.1 什么是 MCP？

MCP（Model Context Protocol）是 Claude Code 连接外部服务的桥梁。通过 MCP，Claude 可以：

- 直接操作数据库
- 调用 API
- 读取外部文档
- 执行远程命令

### 4.2 推荐的 MCP 服务器

| MCP Server | 功能 | 适用场景 |
|-----------|------|---------|
| `context7` | 访问最新文档 | 解决知识过时问题 |
| `postgres` | PostgreSQL 数据库操作 | 直接查询和修改数据 |
| `github` | GitHub API 集成 | 自动处理 Issues/PRs |
| `puppeteer` | 浏览器自动化 | 测试、截图、爬虫 |
| `filesystem` | 增强的文件系统操作 | 复杂文件处理 |

### 4.3 MCP 配置示例

**在 `.claude/settings.json` 中配置**：

```json
{
  "mcpServers": {
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"]
    },
    "postgres": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@postgres/mcp-server"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/mydb"
      }
    }
  }
}
```

### 4.4 测试 MCP 连接

```bash
# 测试 MCP 服务器是否正常
claude mcp test postgres
claude mcp test context7
```

---

## 第五章：上下文管理 —— 让 Claude 记住重要的事

### 5.1 上下文窗口的困境

Claude Code 有个限制：**上下文窗口是有限的**。当对话越来越长，早期的信息会被"遗忘"。

### 5.2 Claude Code 团队推荐的上下文策略

| 策略 | 效果 | 实施难度 |
|-----|------|---------|
| **定期压缩** | ⭐⭐⭐⭐ | 简单 |
| **新建会话** | ⭐⭐⭐ | 简单 |
| **Git Worktrees** | ⭐⭐⭐⭐⭐ | 中等 |
| **Fork 对话** | ⭐⭐⭐⭐ | 中等 |

### 5.3 使用 /compact 智能压缩

```bash
# 手动压缩，保留关键信息
/compact

# 压缩时指定保留重点
/compact focus on the API changes and the list of modified files
```

**在 CLAUDE.md 中添加压缩指令**：

```markdown
## 上下文压缩规则
当执行 /compact 时，请始终保留：
1. 完整的修改文件列表
2. 当前测试状态
3. 未解决的 bug 或问题
4. 待办事项清单
```

### 5.4 使用 Git Worktrees 并行开发

**场景**：同时在多个分支上工作，每个分支一个独立的 Claude 会话。

```bash
# 创建 worktree
git worktree add ../project-feature-a feature-a
git worktree add ../project-feature-b feature-b

# 在不同目录启动 Claude Code
cd ../project-feature-a && claude
cd ../project-feature-b && claude
```

**优势**：
- 每个会话有独立的上下文
- 避免任务混淆
- 可以真正并行开发

### 5.5 使用 .claudeignore 排除无关文件

**示例 `.claudeignore`**：

```
# 依赖目录
node_modules/
vendor/
__pycache__/

# 构建产物
dist/
build/
*.min.js
*.pyc

# 日志和缓存
*.log
.cache/
.pytest_cache/

# 大型二进制文件
*.bin
*.sqlite
*.db
```

---

## 第六章：高级命令与工作流

### 6.1 启动模式

```bash
# 交互模式（默认）
claude

# 带初始提示启动
claude "帮我分析这个项目的性能瓶颈"

# 非交互模式（管道友好）
echo "分析代码结构" | claude

# 指定权限模式
claude --permission-mode plan  # 计划模式，只输出不执行
claude --permission-mode auto  # 自动模式，危险操作除外
claude --permission-mode acceptAll  # 全自动（谨慎使用）
```

### 6.2 常用斜杠命令

| 命令 | 功能 | 适用场景 |
|-----|------|---------|
| `/help` | 帮助信息 | 忘记命令时 |
| `/model` | 切换模型 | Opus/Sonnet 切换 |
| `/compact` | 压缩上下文 | 会话过长时 |
| `/clear` | 清除上下文 | 开始新任务 |
| `/init` | 生成 CLAUDE.md | 新项目初始化 |
| `/resume` | 恢复历史会话 | 继续之前的工作 |
| `/insights` | 使用分析报告 | 复盘、优化习惯 |
| `/permissions` | 权限设置 | 调整安全级别 |
| `/cost` | 查看消耗 | 成本控制 |
| `/bug` | 报告问题 | 反馈 bug |
| `/think` | 深度思考模式 | 复杂任务 |

### 6.3 远程控制模式

**Boris 推荐**：使用 `claude remote-control` 进行协同调试。

```bash
# 启动远程控制会话
claude remote-control

# 然后在 claude.ai/code 或手机 App 上连接
# 可以问："为什么选择这个方案？"
# Claude 会在 overlay 中回答，不影响主上下文
```

### 6.4 自定义命令

**创建自定义命令 `.claude/commands/optimize.md`**：

```markdown
分析这个项目的性能，并提出三个具体的优化建议。
重点关注：
1. 数据库查询效率
2. 缓存策略
3. 并发处理能力
```

**使用**：在 Claude Code 中输入 `/project:optimize`

### 6.5 深度思考模式

让 Claude 在复杂问题上进行更深层的分析：

```markdown
请深度思考（extended thinking）这个架构方案：
- 有哪些潜在的瓶颈？
- 在什么情况下会失败？
- 有没有更好的替代方案？
```

---

## 第七章：大佬实战经验分享

### 7.1 YK（ykdojo）的 40+ 条经验

YK 是 Claude Code 的早期用户，在 GitHub 上维护了 [claude-code-tips](https://github.com/ykdojo/claude-code-tips) 项目。

#### 核心经验：

1. **自定义状态栏**：显示模型、分支、token 使用量
   ```bash
   # 配置 ~/.claude/statusline.sh
   # 显示：model | branch | uncommitted | token %
   ```

2. **Half-clone 技术**：克隆对话但只保留后半部分
   ```bash
   # 用于上下文过半但不想要完全新会话时
   ./scripts/half-clone.sh
   ```

3. **System Prompt Patching**：修改系统提示词
   > "通过修补系统提示词，我把 Claude 变成了真正的结对编程伙伴。"

4. **Check-context 脚本**：每次响应后检查上下文使用
   ```bash
   # 当上下文超过 70% 时自动提醒
   ./scripts/check-context.sh
   ```

### 7.2 Builder.io 团队的 50 条最佳实践

#### 精华摘录：

1. **远程控制是神器**
   > "我的每个会话都从 `claude remote-control` 开始。在手机上问 为什么，回答在 overlay 里，主上下文保持精简。"

2. **压缩时告诉 Claude 保留什么**
   ```
   /compact focus on the API changes and the list of modified files
   ```

3. **用 @ 引用文件，而不是复制粘贴**
   ```
   @src/auth/middleware.ts has the session handling.
   ```

4. **PostToolUse Hook + Prettier = 永远格式化好的代码**
   ```json
   {
     "hooks": {
       "PostToolUse": [{
         "matcher": { "toolName": "Edit|Write" },
         "hooks": [{
           "type": "command",
           "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write"
         }]
       }]
     }
   }
   ```

### 7.3 一位 11 个月深度用户的 Top 10

来自 Reddit r/ClaudeAI 社区：

1. **CLAUDE.md 是最重要的投资**
   > "我花在前 10 小时优化 CLAUDE.md 的时间，在接下来的 1000 小时里得到百倍回报。"

2. **相信 Claude 的 /init**
   > "在新项目中，先运行 `/init`，让它自己分析并生成 CLAUDE.md。通常比我手写的还好。"

3. **权限模式要选对**
   - `plan`：新项目探索，不确定 Claude 会做什么
   - `auto`：熟悉的项目，日常开发
   - `acceptAll`：仅在完全信任的环境

4. **AI 是队友不是工具**
   > "当我改变心态，从 使用工具 变成 与队友协作，效率翻倍。"

5. **定期 review `/insights`**
   > "每周看一次使用报告，发现我 60% 的时间在修同一个类型的 bug。这是流程问题，不是 Claude 的问题。"

---

## 第八章：常见问题与避坑指南

### 8.1 上下文过长怎么办？

**问题**：会话越来越长，Claude 开始"健忘"。

**解决方案**：
1. 主动使用 `/compact`，并告知保留重点
2. 适时开启新会话（不是所有事都要在一个会话完成）
3. 使用 Git Worktrees 实现真正的并行开发
4. 配置好 `.claudeignore`

### 8.2 Claude 老是问权限怎么办？

**问题**：每操作一下就问"是否允许"。

**解决方案**：
```bash
# 在当前会话设置权限
/permissions

# 或者启动时指定
claude --permission-mode auto
```

### 8.3 如何让 Claude 记住我的偏好？

**问题**：每次都要重新说"我喜欢用 TypeScript"、"我的测试框架是 Jest"。

**解决方案**：写入 `~/.claude/CLAUDE.md`（全局）或项目根目录的 `CLAUDE.md`（项目级）。

```markdown
## 用户偏好
- 类型严格模式
- 测试框架：Jest + @testing-library
- 注释语言：中文
- 变量命名：camelCase
```

### 8.4 Claude Code 在国内使用？

**问题**：API 访问不稳定或无法访问。

**解决方案**：
1. 配置 API 代理（见项目文档）
2. 使用国内 API 代理服务
3. 参考 [Claude Code 中文社区指南](https://github.com/claude-code-chinese/claude-code-guide)

### 8.5 陷阱警示

| 陷阱 | 表现 | 解决方案 |
|-----|------|---------|
| **过长的 CLAUDE.md** | Claude 读取时间变长，效果下降 | 控制在 300 行以内 |
| **过度自动化** | 配了一堆 hooks 反而变慢 | 只自动化真正重复的事 |
| **忽略 /insights** | 不知道自己的使用模式 | 每周 review 一次 |
| **滥用 acceptAll** | 出了问题不知道是谁干的 | 熟悉的项目才用 |

---

## 附录 A：快速配置模板

### A.1 最小可用配置

**`.claude/settings.json`**：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": { "toolName": "Edit|Write" },
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs -I {} sh -c 'if [ -f \"{}\" ]; then npx prettier --write \"{}\" 2>/dev/null || true; fi'"
          }
        ]
      }
    ]
  }
}
```

### A.2 完整推荐配置

参见 GitHub 示例仓库：[everything-claude-code](https://github.com/affaan-m/everything-claude-code)

---

## 附录 B：参考资源

### 官方文档
- [Claude Code 官方文档](https://code.claude.com/docs)
- [Hooks 指南](https://code.claude.com/docs/zh-CN/hooks-guide)
- [Best Practices](https://code.claude.com/docs/en/best-practices)

### 社区资源
- [ykdojo/claude-code-tips](https://github.com/ykdojo/claude-code-tips) - 40+ 条实战经验
- [Claude Code 中文指南](https://github.com/claude-code-chinese/claude-code-guide)
- [Reddit r/ClaudeAI](https://www.reddit.com/r/ClaudeAI/) - 活跃社区

### 进阶阅读
- [Builder.io: 50 Claude Code Tips and Best Practices](https://www.builder.io/blog/claude-code-tips-best-practices)
- [Claude Code 最佳实践指南（知乎）](https://zhuanlan.zhihu.com/p/2009744974980331332)

---

## 结语

掌握 Claude Code 的高级用法，不是要你成为"配置大师"，而是要建立**你与 AI 之间的默契**。

就像真正的队友一样：
- 它知道你的习惯（CLAUDE.md）
- 它遵守你的规则（Hooks）
- 它有你的工具箱（Skills + MCP）
- 它记得重要的事（上下文管理）

当你发现自己在想"这个任务让 Claude 来做，它应该知道怎么做"时，你就成功了。

---

*最后更新：2026-04-16*
*参考来源：Claude Code 官方文档、社区经验分享、10+ 个月深度使用总结*