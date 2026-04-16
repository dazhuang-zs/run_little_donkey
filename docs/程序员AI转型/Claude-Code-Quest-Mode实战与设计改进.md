# Claude Code Quest Mode 实战与设计改进

> 作者实战经验总结，基于 Harness Engineering 六层架构提出下一代设计方案

---

## 一、Claude Code Quest Mode 是什么

Claude Code 内置的 Quest Mode 是一种结构化任务执行模式，区别于普通的对话式编程，Quest Mode 将完整项目交付拆解为**明确阶段**，每个阶段有清晰的输入、输出、验收标准。

与普通模式的区别：

| 维度 | 普通对话模式 | Quest Mode |
|------|------------|------------|
| 目标 | 回答问题 | 完成项目交付 |
| 上下文 | 依赖历史 | 每个阶段独立闭环 |
| 执行 | 自由探索 | 结构化流水线 |
| 验收 | 人工判断 | 明确标准检查 |
| 记忆 | 分散 | 集中管理 |

---

## 二、当前 Quest Mode 标准流程

你搭建的 Quest Mode 标准流程：

```
┌─────────────────────────────────────────────┐
│  第一阶段：规划 (Plan)                        │
│  输入：用户需求描述                           │
│  输出：需求分析 + 技术方案 + 里程碑拆解        │
│  工具：claude code / claude dev             │
└─────────────────┬───────────────────────────┘
                  ▼
┌─────────────────────────────────────────────┐
│  第二阶段：执行 (Execute)                    │
│  输入：技术方案                              │
│  输出：文件变更 + 提交记录                     │
│  工具：文件读写 + exec 执行                   │
└─────────────────┬───────────────────────────┘
                  ▼
┌─────────────────────────────────────────────┐
│  第三阶段：编码 (Code)                       │
│  输入：详细设计                              │
│  输出：符合规范的代码                         │
│  工具：编辑器 + linter + formatter           │
└─────────────────┬───────────────────────────┘
                  ▼
┌─────────────────────────────────────────────┐
│  第四阶段：测试 (Test)                       │
│  输入：代码变更                              │
│  输出：测试报告 + 覆盖率                      │
│  工具：pytest / jest / 自动化测试             │
└─────────────────┬───────────────────────────┘
                  ▼
┌─────────────────────────────────────────────┐
│  第五阶段：报告 (Report)                     │
│  输入：各阶段输出                            │
│  输出：交付总结 + 变更记录 + 文档更新          │
│  工具：markdown 报告生成                     │
└─────────────────────────────────────────────┘
```

---

## 三、当前设计存在的问题

### 3.1 单 Agent 执行，信息边界模糊

**问题**：一个 Agent 负责所有阶段，角色切换时容易丢失上下文。

**现象**：
- 第一阶段做的需求理解，到第四阶段已经记不全
- 每个阶段都要重新"告诉"Agent 项目背景
- 编码阶段和测试阶段容易各自为战

**根本原因**：没有 L1 信息边界层 的设计，每个阶段没有明确的知识边界定义。

---

### 3.2 缺少独立的验证机制

**问题**：编码完成后，测试阶段由同一个 Agent 执行，缺少"自查"机制。

**现象**：
- Agent 写完代码，自己测自己，容易放过问题
- Anthropic 的 GAN 架构证明：生成和验证分开，才能发现问题

**根本原因**：没有 L5 评估与观测层 的独立验证设计。

---

### 3.3 工具调用全堆在一起

**问题**：每个阶段都能调用所有工具，没有按阶段筛选。

**现象**：
- 规划阶段 Agent 可能直接开始写代码
- 测试阶段还在修改需求
- 没有阶段锁定机制

**根本原因**：没有 L3 执行编排层 的状态机和阶段门控设计。

---

### 3.4 失败后没有恢复机制

**问题**：某阶段失败后，通常只能从头重试或者放弃。

**现象**：
- 测试挂了，Agent 改代码改乱了
- 执行中断后，不知道从哪恢复
- 没有中间产物持久化

**根本原因**：没有 L4 记忆与状态层 和 L6 约束校验层 的设计。

---

### 3.5 报告质量依赖最后一次对话

**问题**：报告内容取决于 Agent 最后说了什么，没有结构化模板。

**现象**：
- 每次输出的报告格式不一致
- 容易漏掉重要信息
- 没有清晰的变更清单

---

## 四、改进方案：多专家 Quest Mode 架构

基于 Harness Engineering 六层架构，提出改进后的 Quest Mode 设计：

### 4.1 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    L6: 约束与恢复层                  │
│  阶段门控 │ 失败策略 │ 超时控制 │ 自动回滚             │
├─────────────────────────────────────────────────────┤
│                    L5: 评估与观测层                  │
│  Code Review Agent │ 自动化测试 │ 报告生成器          │
├─────────────────────────────────────────────────────┤
│                    L4: 记忆与状态层                  │
│  Quest State.json │ 变更清单 │ 阶段产物 │ 版本快照     │
├─────────────────────────────────────────────────────┤
│                    L3: 执行编排层                    │
│  状态机 │ 阶段门控 │ 并行任务 │ 进度追踪             │
├─────────────────────────────────────────────────────┤
│                    L2: 工具系统层                    │
│  Plan Agent 工具集 │ Code Agent 工具集 │            │
│  Test Agent 工具集 │ Review Agent 工具集             │
├─────────────────────────────────────────────────────┤
│                    L1: 信息边界层                   │
│  需求文档 │ 上下文摘要 │ 各阶段知识卡片               │
└─────────────────────────────────────────────────────┘
```

### 4.2 四专家 Agent 流水线

用四个专门的 Agent，替代原来单一 Agent 的全流程执行：

```
┌────────────────────────────────────────────────────────┐
│                    Master Agent                        │
│            主持全局，协调四专家分工                     │
└──────────┬──────────┬──────────┬──────────┬─────────────┘
           ▼          ▼          ▼          ▼
    ┌──────────┐┌──────────┐┌──────────┐┌──────────┐
    │  Plan    ││  Code    ││  Test    ││  Review  │
    │  Expert  ││  Expert  ││  Expert  ││  Expert  │
    │          ││          ││          ││          │
    │ 专注文档 ││ 专注代码 ││ 专注验证 ││ 专注质量 │
    │ 理解需求 ││ 实现功能 ││ 运行测试 ││ 检查规范 │
    │ 拆解任务 ││ 代码规范 ││ 覆盖率   ││ 安全审计 │
    └──────────┘└──────────┘└──────────┘└──────────┘
```

**职责分工**：

| Agent | 核心职责 | 输入 | 输出 |
|-------|---------|------|------|
| Plan Expert | 需求理解、任务拆解 | 用户需求 | 需求文档、任务列表、技术方案 |
| Code Expert | 代码实现、代码规范 | 技术方案 | 源代码、代码变更清单 |
| Test Expert | 测试用例、自动化验证 | 代码变更 | 测试报告、覆盖率报告 |
| Review Expert | 代码审查、安全审计 | 各阶段输出 | 质量报告、风险评估 |

**为什么比单 Agent 强**：
- 每个专家有固定的系统提示词，角色切换零成本
- 专家之间通过结构化文档交接，不依赖记忆
- Review Expert 独立于 Code Expert，真正做到"生成和验证分离"

---

## 五、阶段门控设计（L3 执行编排层）

### 5.1 状态机定义

```python
class QuestState:
    INIT = "init"              # 初始状态
    PLANNING = "planning"      # 规划中
    PLAN_APPROVED = "plan_approved"    # 方案已确认
    CODING = "coding"          # 编码中
    CODE_APPROVED = "code_approved"    # 代码已审核
    TESTING = "testing"        # 测试中
    TEST_APPROVED = "test_approved"    # 测试已通过
    REPORTING = "reporting"    # 生成报告
    COMPLETED = "completed"    # 全部完成
    FAILED = "failed"          # 失败
    RECOVERING = "recovering"  # 恢复中
```

### 5.2 阶段门控规则

```python
GATE_TRANSITIONS = {
    "init": {
        "trigger": "用户提交需求",
        "action": "启动 Plan Expert",
        "exit_condition": "Plan Expert 输出需求文档",
        "approver": "用户 / Master Agent",
    },
    "planning": {
        "trigger": "用户确认方案",
        "action": "启动 Code Expert",
        "exit_condition": "所有代码变更已提交",
        "approver": "Review Expert",
    },
    "coding": {
        "trigger": "Review Expert 通过",
        "action": "启动 Test Expert",
        "exit_condition": "测试通过率达到 80%",
        "approver": "Test Expert",
    },
    "testing": {
        "trigger": "测试通过",
        "action": "启动 Review Expert + 报告生成",
        "exit_condition": "质量报告分数 >= 85",
        "approver": "Review Expert",
    },
    "reporting": {
        "trigger": "报告生成完成",
        "action": "输出交付物",
        "exit_condition": "用户确认",
        "approver": "用户",
    },
}
```

### 5.3 失败策略（L6 约束与恢复层）

```python
FAILURE_STRATEGIES = {
    "planning": {
        "max_retries": 3,
        "on_max_retry": "请求用户澄清需求",
        "snapshot": "保存当前方案草稿",
        "recovery": "从草稿恢复，不从头开始",
    },
    "coding": {
        "max_retries": 5,
        "on_max_retry": "回滚到上一稳定版本",
        "snapshot": "每完成一个文件立即提交",
        "recovery": "git checkout 到上一 commit",
    },
    "testing": {
        "max_retries": 3,
        "on_max_retry": "Code Expert 修复，Test Expert 重测",
        "snapshot": "测试结果快照",
        "recovery": "只重跑失败的测试用例",
    },
}
```

---

## 六、记忆与状态管理（L4）

### 6.1 Quest State 文件结构

```
.quest/
├── state.json          # 当前状态机状态
├── context.md          # 全局上下文摘要（每次阶段切换更新）
├── plan/
│   ├── requirements.md # 原始需求
│   ├── spec.md         # 技术方案
│   └── tasks.md        # 任务清单
├── code/
│   ├── changes.md      # 代码变更清单
│   └── files.md        # 已修改文件列表
├── test/
│   ├── results.md      # 测试结果
│   └── coverage.md     # 覆盖率报告
├── review/
│   ├── report.md       # 质量审查报告
│   └── risks.md       # 风险清单
└── reports/
    └── delivery.md    # 最终交付报告
```

### 6.2 上下文压缩策略

每个阶段开始时，Master Agent 自动生成上下文摘要：

```markdown
# Quest 上下文摘要

## 项目背景
[一句话描述项目在做什么]

## 当前阶段
[X] 已完成 / [ ] 进行中 / [ ] 待开始

## 已完成的工作
- 需求文档已完成 ✓
- 技术方案已确认 ✓
- 核心模块已完成 ✓
- 测试覆盖率 72%

## 当前瓶颈
测试在 XXX 功能上失败，原因是YYY

## 接下来
1. 修复 XXX 功能
2. 重跑测试
3. 生成最终报告
```

---

## 七、工具集分层设计（L2）

每个专家 Agent 只获得它需要的工具：

| Agent | 允许的工具 |
|-------|----------|
| Plan Expert | read, glob, grep, web_search, write, memory_search |
| Code Expert | read, write, exec, git, linter, formatter |
| Test Expert | exec, read, glob, write (测试文件) |
| Review Expert | read, glob, exec (安全扫描), linter |

**关键设计**：不把 bash/exec 工具给 Review Expert，防止它绕过验证直接修代码。

---

## 八、与 Claude Code 原生功能的结合

### 8.1 使用 /plan 命令启动规划阶段

```bash
# 在 Claude Code 中
/plan
# 输入：我想做一个小红书评论分析工具，支持小红书、大众点评、抖音三个平台
# Claude Code 输出：需求分析 + 技术方案 + 任务拆解
```

### 8.2 使用 /memory 管理上下文（L4）

```bash
# 每个阶段结束时保存状态
/memory save "当前状态：规划完成，技术方案已确认，3个任务待完成"
# 下次继续时加载
/memory load
```

### 8.3 使用 MCP 工具增强 L2

推荐的 MCP 工具组合：

| MCP 工具 | 作用 | 适用阶段 |
|---------|------|---------|
| Browser Relay | Web 自动化测试 | Test |
| GitHub | PR 管理 | Review |
| File System | 结构化文件操作 | Plan / Code |
| Search | 文档检索 | Plan |

---

## 九、改进后的完整流程图

```
用户提交需求
     │
     ▼
┌──────────────────┐
│  Plan Expert     │  ← L1 信息边界：只读需求文档
│  理解需求        │  ← L2 工具集：read + web_search + write
│  拆解任务        │  ← L4 输出：requirements.md + tasks.md
└──────┬───────────┘
       ▼ 用户确认方案
┌──────────────────┐
│  Code Expert     │  ← L1 信息边界：只读 spec.md
│  写代码          │  ← L2 工具集：read + write + exec + git
│  提交代码        │  ← L4 输出：changes.md + 文件变更
└──────┬───────────┘
       ▼ Review Expert 通过
┌──────────────────┐
│  Test Expert     │  ← L1 信息边界：只读 changes.md
│  写测试          │  ← L2 工具集：exec + read + write
│  运行测试        │  ← L4 输出：test-results.md + coverage
└──────┬───────────┘
       ▼ 测试通过
┌──────────────────┐
│  Review Expert   │  ← L1 信息边界：读所有阶段产物
│  代码审查        │  ← L2 工具集：read + linter（无 exec 写权限）
│  安全审计        │  ← L4 输出：review-report.md
└──────┬───────────┘
       ▼ 质量达标
┌──────────────────┐
│  报告生成器      │  ← L4 读取所有阶段产物
│  结构化输出      │  ← L5 输出：delivery-report.md
└──────┬───────────┘
       ▼ 用户确认
       ✅ 交付完成
```

---

## 十、落地行动计划

### 第一周：搭建基础框架

1. 创建 `.quest/` 目录结构
2. 编写四个专家 Agent 的系统提示词模板
3. 实现简单的状态机（state.json）
4. 配置阶段门控规则

### 第二周：引入独立验证

1. 将 Test Expert 和 Code Expert 完全分离
2. 添加 Review Expert 的代码审查功能
3. 实现测试覆盖率自动检查

### 第三周：增强恢复能力

1. 实现每个阶段的快照机制
2. 添加失败后的自动回滚
3. 实现上下文压缩脚本

### 第四周：与 Claude Code 集成

1. 封装成可复用的 Claude Code 项目模板
2. 编写 `/quest start` 命令的快捷方式
3. 整理最佳实践文档

---

## 十一、总结：为什么这个设计更强

| 维度 | 原设计 | 改进后 |
|------|--------|--------|
| Agent 架构 | 单 Agent 全流程 | 四专家流水线 |
| 上下文管理 | 依赖记忆 | 结构化文档交接 |
| 验证机制 | Agent 自测自 | 独立 Review Expert |
| 失败恢复 | 手动重试 | 自动快照 + 回滚 |
| 工具权限 | 全放开 | 按阶段精确授权 |
| 报告质量 | 依赖最后对话 | 结构化模板生成 |

**核心洞察**：AI 编程的瓶颈不在于模型有多强，而在于工程基础设施（也就是 Harness）能不能支撑长链路、可靠执行的任务。

---

## 附录：快速启动命令

```bash
# 初始化 Quest 项目
mkdir my-project && cd my-project
mkdir -p .quest/plan .quest/code .quest/test .quest/review .quest/reports

# 创建初始状态
echo '{"state": "init", "started_at": ""}' > .quest/state.json

# 在 Claude Code 中启动
/claude
# 输入: 帮我用 Quest Mode 完成这个项目...
```
