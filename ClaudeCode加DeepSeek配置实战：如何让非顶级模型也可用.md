# Claude Code 加 DeepSeek 配置实战：如何让非顶级模型也可用

> 用不起 Claude Opus？配置到位，效果不差。

## 前提

本文目标读者：**用不了 Claude Opus API，只能用 DeepSeek 的程序员**

核心问题：DeepSeek 输出不够稳定，怎么通过配置让 Claude Code 达到可用状态？

---

## 核心认知

Claude Code 官方文档里有一句话容易被忽略：

> CLAUDE.md content is delivered as a user message, not as part of the system prompt. Claude reads it and tries to follow it.

这意味着：**模型不是全部，配置能补偿。**

官方文档把 Claude Code 的记忆机制分两种：

| 机制 | 谁写 | 什么时候加载 |
|------|------|-------------|
| CLAUDE.md | 你写 | 每次会话开始 |
| Auto Memory | Claude 自己写 | 每次会话开始（只读前200行） |

**关键点**：你写的东西会直接影响模型行为。配置越具体，模型越靠谱。

---

## 配置一：CLAUDE.md 怎么写才有用

官方文档明确说了：

> Specific, concise, well-structured instructions work best.

### 1.1 写什么

把"每次都要解释"的东西写进去：

```markdown
# 项目配置

## 项目结构
- src/api/ - API 路由
- src/core/ - 核心逻辑
- tests/ - 测试

## 构建命令
- `npm run dev` - 启动开发服务器
- `npm run test` - 运行测试
- `npm run lint` - 代码检查

## 代码规范
- 使用 2 空格缩进
- 必须加类型提示
- 函数必须有 docstring
- 提交前运行 lint
```

### 1.2 别写什么

- **模糊的规则**："代码写得好一点" —— 没用
- **矛盾的规则**："用 2 空格" + "用 4 空格" —— 模型随便选
- **太长**："目标 < 200 行" —— 越长 adherence 越低

### 1.3 进阶：按文件类型加载规则

官方文档说可以用 `.claude/rules/` 目录，让规则只在相关文件被打开时才加载：

```
.claude/
├── CLAUDE.md
└── rules/
    ├── api.md        # 只在打开 API 文件时加载
    ├── testing.md    # 只在打开测试文件时加载
    └── security.md   # 安全相关规则
```

`api.md` 内容示例：

```markdown
---
paths:
  - "src/api/**/*.ts"
---

# API 开发规则

- 所有端点必须有输入验证
- 使用标准错误响应格式
- 包含 OpenAPI 注释
```

### 1.4 路径规则怎么写

官方文档支持的 glob 模式：

| 模式 | 匹配 |
|------|------|
| `*.ts` | 根目录所有 TS 文件 |
| `src/**/*.js` | src 下所有 JS 文件 |
| `tests/*.{ts,tsx}` | tests 下 TS 和 TSX |

---

## 配置二：settings.json 怎么配

官方文档说 settings.json 有四个作用域：

| 作用域 | 位置 | 谁能用 |
|--------|------|--------|
| User | ~/.claude/settings.json | 自己所有项目 |
| Project | .claude/settings.json | 团队（提交 git） |
| Local | .claude/settings.local.json | 自己当前项目 |
| Managed | IT 部署 | 整个组织 |

### 2.1 最实用：permissions 权限控制

这是官方文档的核心例子：

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run test *)",
      "Bash(npm run lint *)",
      "Bash(git *)",
      "Read",
      "Edit",
      "Write"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(curl *)",
      "Read(./.env*)",
      "Read(./secrets/**)"
    ]
  }
}
```

**为什么有用**：限制危险操作，让模型更谨慎。DeepSeek 模型能力弱，更需要安全边界。

### 2.2 环境变量

```json
{
  "env": {
    "NODE_ENV": "development",
    "LOG_LEVEL": "debug"
  }
}
```

---

## 配置三：Skills 自定义命令

官方文档说：当你"每次都复制同样的流程"时，用 Skill。

### 3.1 创建一个代码审查 Skill

```bash
mkdir -p ~/.claude/skills/code-review
```

`~/.claude/skills/code-review/SKILL.md`：

```yaml
---
name: code-review
description: 按团队规范审查代码
disable-model-invocation: true
allowed-tools: Bash(git *) Bash(ruff *) Read
---

## 审查流程

1. 运行 `git diff --stat` 看改了多少
2. 运行 `ruff check .` 检查代码
3. 读改动文件，找问题
4. 输出报告

## 报告格式

## 问题
- [file:line] 问题描述

## 总结
- 严重问题数
- 建议
```

### 3.2 调用方式

```bash
# 直接调用
/code-review

# 带参数
/code-review src/api/user.py
```

---

## 配置四：MCP 扩展工具

官方文档：MCP (Model Context Protocol) 让 Claude 连接外部工具。

### 4.1 什么时候用

官方文档说：

> Connect a server when you find yourself copying data into chat from another tool

比如：
- 想让 Claude 查数据库？→ 接 PostgreSQL MCP
- 想让 Claude 查 GitHub？→ 接 GitHub MCP

### 4.2 怎么配

项目级 MCP 在 `.mcp.json`：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/project"]
    },
    "github": {
      "command": "uvx",
      "args": ["mcp-server-github"]
    }
  }
}
```

---

## 实战：一步步配好 DeepSeek

### Step 1：创建 CLAUDE.md

```bash
# 项目根目录
touch CLAUDE.md
```

内容：

```markdown
# 项目配置

## 项目
Python FastAPI 项目。

## 命令
- pytest - 运行测试
- ruff check . - 代码检查
- ruff format . - 格式化

## 规范
- 4 空格缩进
- 类型提示必须有
- docstring 用 Google 风格
```

### Step 2：配置 permissions

```bash
mkdir -p .claude
touch .claude/settings.json
```

```json
{
  "permissions": {
    "allow": [
      "Bash(pytest *)",
      "Bash(ruff *)",
      "Bash(git *)",
      "Read",
      "Edit",
      "Write"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(curl *)",
      "Read(./.env*)",
      "Read(./secrets/**)"
    ]
  }
}
```

### Step 3：创建代码审查 Skill

```bash
mkdir -p .claude/skills/review
touch .claude/skills/review/SKILL.md
```

```yaml
---
name: review
description: 审查代码质量
disable-model-invocation: true
allowed-tools: Bash(git *) Bash(ruff *) Read
---

请审查当前改动：

1. 运行 `git diff --stat` 看改了多少
2. 运行 `ruff check .` 检查代码
3. 输出审查报告

格式：
## 问题
- [file:line] 问题

## 总结
```

### Step 4：使用

```bash
# 启动 Claude Code，指定 DeepSeek
claude --model deepseek

# 或者在对话中用
/review
```

---

## 效果怎么样

官方文档说：

> The more specific and concise your instructions, the more consistently Claude follows them.

配置到位后：
- **输出更稳定**：规则明确，模型不用猜
- **错误更少**：权限限制防止危险操作
- **效率更高**：Skill 自动化重复流程

---

## 还有啥可以配

官方文档里还有这些我没展开：

- **Auto Memory**：让 Claude 自己记住调试心得
- **Subagents**：创建专门的子 Agent
- **Hooks**：自动化工具调用前后的事件

官方文档值得一读：https://docs.anthropic.com/en/docs/claude-code/

---

## 总结

| 配置 | 作用 | 难度 |
|------|------|------|
| CLAUDE.md | 项目规范 | ⭐ |
| settings.json | 权限控制 | ⭐⭐ |
| Skills | 自动化流程 | ⭐⭐ |
| MCP | 外部工具 | ⭐⭐⭐ |

**记住**：模型不够，配置来凑。配置越具体，输出越靠谱。