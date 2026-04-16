# 【深度】Claude Code Quest Mode 实战：单 Agent 流水线的致命缺陷，以及我如何用四专家架构解决它

> 作者花了 3 个月用 Claude Code 做项目交付，从"对话式编程"一路踩坑到"结构化 Quest Mode"，发现一个反直觉的事实：AI 编程的瓶颈从来不是模型有多强，而是工程基础设施能不能兜住长链路任务。

**关键词**：Claude Code、Quest Mode、AI 编程、多 Agent 架构、Harness Engineering、Claude Dev

**适合读者**：已经用 Claude Code / Cursor 写过代码，想用它做完整项目交付的工程师

---

## 前言：我用 AI 做了 3 个月，发现哪里不对劲

2026 年初，我开始用 Claude Code 做完整的项目交付。最早的模式很简单：对话 → 写代码 → 对话 → 改 bug。听起来很自然，但做了几个项目之后，我发现一个越来越明显的问题：

**做到第三个功能模块的时候，我已经不太记得第一个模块的设计细节了。**

对话式编程的天然缺陷就是依赖上下文，而上下文会随着对话变长而衰减。我开始习惯性地在每次新对话里粘贴大段背景描述，Agent 也开始"遗忘"之前的决策。一个本该 2 小时完成的功能，最后花了一整天——大部分时间都在重新对齐上下文。

这让我开始思考一个问题：**AI 编程的瓶颈，真的在模型能力上吗？**

答案是：不是。Anthropic 和 OpenAI 的最新实践都指向了同一个方向——瓶颈在于 Harness，也就是围绕模型构建的工程基础设施。

这就是我写这篇文章的原因。

---

## 一、Claude Code Quest Mode 是什么

Claude Code 内置的 Quest Mode，本质上是一种**结构化任务执行模式**。它把完整项目交付拆解为明确阶段，每个阶段有清晰的输入、输出、验收标准。

区别于普通对话式编程：

| 维度 | 普通对话模式 | Quest Mode |
|------|------------|------------|
| 目标 | 回答问题 | 完成项目交付 |
| 上下文 | 依赖历史 | 每个阶段独立闭环 |
| 执行 | 自由探索 | 结构化流水线 |
| 验收 | 人工判断 | 明确标准检查 |
| 记忆 | 分散在对话里 | 集中管理 |

换句话说，Quest Mode 把 AI 编程从"聊天"变成了"流水线"。

---

## 二、我搭建的五阶段 Quest 流程

基于我的实战经验，Quest Mode 的标准流程分五个阶段：

### 阶段一：规划（Plan）

**做什么**：理解需求、拆解任务、设计技术方案。

**输入**：用户的一句话需求描述

**输出**：需求文档 + 技术方案 + 里程碑拆解

这个阶段的核心不是写得越多越好，而是**把范围界定清楚**。很多 AI 编程失败的根本原因是需求本身模糊，Agent 在模糊的需求下写了一堆不需要的功能，然后返工。

### 阶段二：执行（Execute）

**做什么**：按里程碑一个个实现，每个文件写完立即提交 git。

**输入**：技术方案

**输出**：文件变更 + git 提交记录

关键原则是**小步提交**。不要等整个功能写完再提交，每完成一个文件就提交。这样做有两个好处：出问题容易回滚，Agent 也不会在大量未提交的变更里迷失。

### 阶段三：编码（Code）

**做什么**：代码实现 + linter 检查 + 格式化。

**输入**：详细设计

**输出**：符合规范的源代码

这个阶段 Agent 容易"过度发挥"，写一些超出需求的实现。在五阶段模型里，编码阶段严格按 spec 执行，不允许自行扩展。

### 阶段四：测试（Test）

**做什么**：运行测试用例，生成覆盖率报告。

**输入**：代码变更

**输出**：测试报告 + 覆盖率数据

如果测试失败，记录失败原因，交给编码阶段修复。

### 阶段五：报告（Report）

**做什么**：汇总各阶段输出，生成结构化交付报告。

**输入**：各阶段产物

**输出**：变更清单 + 项目总结 + 文档更新

---

## 三、五阶段模型的五个致命缺陷

用了一段时间后，我发现了这个基础版本的问题。

### 缺陷一：单 Agent 执行，上下文在阶段切换时丢失

一个 Agent 负责所有五个阶段，听起来很简洁。但问题是：**第一阶段做的需求理解，到第四阶段已经记不全了。**

每个阶段都要重新告诉 Agent 项目背景，Agent 容易在编码时偏离最初的需求理解。这是缺少信息边界层的直接后果。

### 缺陷二：编码和测试是同一个 Agent，自己测自己

编码 Agent 写完代码，自己运行测试，自己判断通过没有。问题很明显：**Agent 很难真正否定自己的产出。**

Anthropic 的 GAN 架构早就证明了这一点：生成器和判别器必须分开，才能真正发现问题。OpenAI 在百万行代码项目里，也用了独立的 Review 机制。

### 缺陷三：工具全放开，阶段之间没有门控

在基础版本里，每个阶段都可以调用所有工具。结果是：**规划阶段 Agent 可能已经开始写代码了，测试阶段还在改需求。**

这说明没有执行编排层的设计，流水线根本守不住。

### 缺陷四：某阶段失败后，只能从头重试或放弃

测试挂了，Agent 在一堆未提交的变更里来回修改，越改越乱。最后的解决办法往往是"算了重来"。

根本原因是缺少状态管理和快照机制。

### 缺陷五：报告质量完全依赖 Agent 最后说了什么

没有结构化模板，报告内容就是 Agent 最后一次回复的内容。格式随机，容易漏项。没有变更清单，没有验收记录。

---

## 四、改进方案：四专家 Agent 架构

针对这五个缺陷，我基于 Harness Engineering 六层架构重新设计了 Quest Mode。核心改变是：**把单一 Agent 替换成四个专家 Agent，每个专家只做一件事。**

### 4.1 四专家流水线

```
Master Agent（主持全局，协调四专家分工）
     │
     ├── Plan Expert（专注文档：理解需求，拆解任务）
     ├── Code Expert（专注代码：实现功能，遵守规范）
     ├── Test Expert（专注验证：运行测试，检查覆盖率）
     └── Review Expert（专注质量：代码审查，安全审计）
```

每个专家有固定的系统提示词，角色切换零成本。专家之间通过结构化文档交接，不依赖 Agent 的记忆。

**关键设计**：Review Expert 和 Code Expert 完全分离。Review Expert 只有读权限，不能直接修改代码，必须通过 Master Agent 协调修复。这才是真正的"生成与验证分离"。

职责分工：

| 专家 | 核心职责 | 输入 | 输出 |
|-----|---------|------|------|
| Plan Expert | 需求理解、任务拆解 | 用户需求 | 需求文档、技术方案 |
| Code Expert | 代码实现、代码规范 | 技术方案 | 源代码、变更清单 |
| Test Expert | 测试用例、自动化验证 | 代码变更 | 测试报告、覆盖率报告 |
| Review Expert | 代码审查、安全审计 | 各阶段产物 | 质量报告、风险评估 |

### 4.2 六层架构支撑

```
L6: 约束与恢复层   阶段门控 | 失败策略 | 超时控制 | 自动回滚
L5: 评估与观测层   独立 Review | 测试报告 | 质量评分
L4: 记忆与状态层   状态机 | 快照 | 阶段产物持久化
L3: 执行编排层     阶段切换 | 门控规则 | 进度追踪
L2: 工具系统层     按专家分配工具集
L1: 信息边界层     阶段知识卡片 | 上下文摘要
```

六层各司其职，最底层（L1）定义每个专家"该知道什么"，最顶层（L6）负责"出了问题怎么兜底"。

---

## 五、核心组件详细设计

### 5.1 状态机与阶段门控

```python
class QuestState:
    INIT = "init"           # 初始状态
    PLANNING = "planning"   # 规划中
    PLAN_APPROVED = "plan_approved"  # 方案已确认
    CODING = "coding"       # 编码中
    CODE_APPROVED = "code_approved"  # 代码已审核
    TESTING = "testing"     # 测试中
    COMPLETED = "completed"  # 全部完成
    FAILED = "failed"       # 失败
    RECOVERING = "recovering"  # 恢复中
```

每个状态之间有明确的门控规则，不是想跳就能跳：

| 当前状态 | 触发条件 | 启动专家 | 退出条件 | 审批人 |
|---------|---------|---------|---------|-------|
| init | 用户提交需求 | Plan Expert | 需求文档输出 | 用户确认 |
| planning | 方案已确认 | Code Expert | 所有代码变更提交 | Review Expert |
| coding | Review 通过 | Test Expert | 测试覆盖率 >= 80% | Test Expert |
| testing | 测试通过 | Review Expert | 质量分数 >= 85 | Review Expert |

### 5.2 失败策略（让 AI 编程可恢复）

```python
FAILURE_STRATEGIES = {
    "planning": {
        "max_retries": 3,
        "on_max_retry": "请求用户澄清需求",
        "snapshot": "保存方案草稿到 .quest/plan/draft.md",
        "recovery": "从草稿恢复，不从头开始",
    },
    "coding": {
        "max_retries": 5,
        "on_max_retry": "git 回滚到上一稳定 commit",
        "snapshot": "每完成一个文件立即 git add + commit",
        "recovery": "git checkout 到上一 commit",
    },
    "testing": {
        "max_retries": 3,
        "on_max_retry": "Code Expert 修复后重测",
        "snapshot": "保存测试结果快照",
        "recovery": "只重跑失败的测试用例",
    },
}
```

### 5.3 记忆管理：.quest/ 目录结构

```
.quest/
├── state.json              # 当前状态（状态机状态）
├── context.md              # 全局上下文摘要（阶段切换时更新）
├── plan/
│   ├── requirements.md     # 原始需求
│   ├── spec.md              # 技术方案
│   └── tasks.md             # 任务清单
├── code/
│   ├── changes.md           # 代码变更清单
│   └── files.md             # 已修改文件列表
├── test/
│   ├── results.md           # 测试结果
│   └── coverage.md          # 覆盖率报告
├── review/
│   ├── report.md            # 质量审查报告
│   └── risks.md             # 风险清单
└── reports/
    └── delivery.md          # 最终交付报告
```

上下文摘要模板（每个阶段开始时由 Master Agent 生成）：

```markdown
# Quest 上下文摘要

## 项目背景
一句话描述项目在做什么

## 当前阶段：进行中
[ ] Plan [✓] Code [ ] Test [ ] Review [ ] Report

## 已完成
- 需求文档已完成
- 技术方案已确认
- 核心模块已完成

## 当前瓶颈
测试在认证模块失败，原因：Token 过期未处理

## 接下来
1. 修复 Token 刷新逻辑
2. 重跑认证相关测试
3. 生成最终交付报告
```

### 5.4 工具集按专家分层授权

这是很多人忽略但非常关键的一点：不是每个专家都需要 bash 权限。

| 专家 | 允许的工具 |
|-----|----------|
| Plan Expert | read, glob, grep, web_search, write |
| Code Expert | read, write, exec, git, linter, formatter |
| Test Expert | exec, read, glob, write（测试文件） |
| Review Expert | read, glob, exec（安全扫描）, linter（仅读） |

**Review Expert 没有 exec 的写权限**，它只能运行只读的安全扫描，不能修改代码。这是强制分离的核心机制。

---

## 六、完整流程图

```
用户提交需求
     │
     ▼
┌──────────────────┐
│  Plan Expert     │  L1: 只读需求文档
│  理解 + 拆解     │  L2: read + web_search + write
│                  │  L4: 输出 requirements.md + tasks.md
└──────┬───────────┘
       ▼ 用户确认方案
┌──────────────────┐
│  Code Expert     │  L1: 只读 spec.md
│  写代码 + 提交   │  L2: read + write + exec + git
│                  │  L4: 每文件完成立即 commit
└──────┬───────────┘
       ▼ Review Expert 通过
┌──────────────────┐
│  Test Expert     │  L1: 只读 changes.md
│  写测试 + 运行    │  L2: exec + read + write
│                  │  L4: 输出 coverage.md
└──────┬───────────┘
       ▼ 测试通过
┌──────────────────┐
│  Review Expert   │  L1: 读所有阶段产物
│  代码审查 + 审计  │  L2: read + linter（无写权限）
│                  │  L4: 输出 quality-report.md
└──────┬───────────┘
       ▼ 质量达标
┌──────────────────┐
│  报告生成器       │  L4: 读取所有阶段产物
│  结构化输出       │  L5: 输出 delivery-report.md
└──────┬───────────┘
       ▼ 用户确认
       ✅ 交付完成
```

---

## 七、四周落地计划

### 第一周：搭架子

- 创建 `.quest/` 目录结构
- 编写四个专家的提示词模板
- 实现状态机（state.json）
- 配置基础门控规则

### 第二周：引入独立验证

- Test Expert 和 Code Expert 完全分离
- Review Expert 的代码审查功能
- 测试覆盖率自动检查脚本

### 第三周：增强恢复能力

- 每个阶段快照机制
- 失败后自动回滚脚本
- 上下文压缩生成器

### 第四周：集成到 Claude Code

- 封装成项目模板（clone 即用）
- 编写启动快捷命令
- 整理最佳实践文档

---

## 八、和 Claude Code 原生功能的结合

Quest Mode 不是推倒重来，而是叠加在 Claude Code 原生能力之上：

**用 /plan 启动规划阶段**。Claude Code 内置的 /plan 命令天然适合作为 Plan Expert 的入口。

**用 /memory 管理上下文**。每个阶段结束时把状态保存到 memory，下次继续时加载。

**用 MCP 工具增强各专家**。Browser Relay 用于 Test Expert 的 Web 自动化测试，GitHub MCP 用于 Review Expert 的 PR 管理。

---

## 总结：为什么这个架构更强

| 维度 | 原设计 | 改进后 |
|------|--------|--------|
| Agent 架构 | 单 Agent 全流程 | 四专家流水线 |
| 上下文管理 | 依赖对话记忆 | 结构化文档交接 |
| 验证机制 | Agent 自己测自己 | 独立 Review Expert |
| 失败恢复 | 手动重试或放弃 | 快照 + 自动回滚 |
| 工具权限 | 全放开 | 按专家精确授权 |
| 报告质量 | 依赖最后对话 | 结构化模板生成 |

核心洞察只有一句话：**AI 编程的瓶颈不在于模型有多强，而在于 Harness 能不能支撑长链路、可靠执行的任务。**

OpenAI 三个工程师五个月写出一百万行代码，Anthropic 十六个并行 Agent 跑出十万行 Rust，Stripe 每周合并一千三百个无人值守 PR——这些数字的背后，靠的都不是更强的模型，而是更精密的工程基础设施。

---

## 快速启动

```bash
# 初始化项目
mkdir my-project && cd my-project
mkdir -p .quest/plan .quest/code .quest/test .quest/review .quest/reports

# 创建初始状态
echo '{"state": "init", "started_at": ""}' > .quest/state.json

# 在 Claude Code 中启动
/claude
# 输入: 帮我用 Quest Mode 完成这个项目...
```

完整代码模板和专家提示词已开源到 GitHub：[run_little_donkey](https://github.com/dazhuang-zs/run_little_donkey)

---

**相关阅读**：
- [Harness Engineering 完全指南：AI Agent 时代的核心工程方法论](https://blog.csdn.net/weixin_43726381/article/details/XXXXX)
- [AI 时代程序员生存指南：职业方向全景地图](https://blog.csdn.net/weixin_43726381/article/details/XXXXX)
