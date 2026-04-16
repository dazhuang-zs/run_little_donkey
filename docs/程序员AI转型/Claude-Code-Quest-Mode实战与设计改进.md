# Claude Code Quest Mode 实战与设计改进

> 作者实战经验总结，基于 Harness Engineering 六层架构提出下一代设计方案

---

## 一、Claude Code Quest Mode 是什么

Claude Code 内置的 Quest Mode 是一种结构化任务执行模式，区别于普通的对话式编程，Quest Mode 将完整项目交付拆解为明确阶段，每个阶段有清晰的输入、输出、验收标准。

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

核心流程：规划 -> 执行 -> 编码 -> 测试 -> 输出报告

```
第一阶段：规划 (Plan)
  输入：用户需求描述
  输出：需求分析 + 技术方案 + 里程碑拆解
  工具：claude code / claude dev

第二阶段：执行 (Execute)
  输入：技术方案
  输出：文件变更 + 提交记录
  工具：文件读写 + exec 执行

第三阶段：编码 (Code)
  输入：详细设计
  输出：符合规范的代码
  工具：编辑器 + linter + formatter

第四阶段：测试 (Test)
  输入：代码变更
  输出：测试报告 + 覆盖率
  工具：pytest / jest / 自动化测试

第五阶段：报告 (Report)
  输入：各阶段输出
  输出：交付总结 + 变更记录 + 文档更新
```

---

## 三、当前设计存在的问题

### 3.1 单 Agent 执行，信息边界模糊

一个 Agent 负责所有阶段，角色切换时容易丢失上下文。

现象：
- 第一阶段做的需求理解，到第四阶段已经记不全
- 每个阶段都要重新告诉 Agent 项目背景
- 编码阶段和测试阶段容易各自为战

根本原因：没有 L1 信息边界层 的设计，每个阶段没有明确的知识边界定义。

### 3.2 缺少独立的验证机制

编码完成后，测试阶段由同一个 Agent 执行，缺少自查机制。

现象：
- Agent 写完代码，自己测自己，容易放过问题
- Anthropic 的 GAN 架构证明：生成和验证分开，才能发现问题

根本原因：没有 L5 评估与观测层 的独立验证设计。

### 3.3 工具调用全堆在一起

每个阶段都能调用所有工具，没有按阶段筛选。

现象：
- 规划阶段 Agent 可能直接开始写代码
- 测试阶段还在修改需求
- 没有阶段锁定机制

### 3.4 失败后没有恢复机制

某阶段失败后，通常只能从头重试或者放弃。

现象：
- 测试挂了，Agent 改代码改乱了
- 执行中断后，不知道从哪恢复
- 没有中间产物持久化

### 3.5 报告质量依赖最后一次对话

每次输出的报告格式不一致，容易漏掉重要信息，没有结构化模板。

---

## 四、改进方案：多专家 Quest Mode 架构

基于 Harness Engineering 六层架构，提出改进后的 Quest Mode 设计。

### 4.1 六层架构

```
L6: 约束与恢复层   阶段门控 | 失败策略 | 超时控制 | 自动回滚
L5: 评估与观测层   Code Review Agent | 自动化测试 | 报告生成器
L4: 记忆与状态层   Quest State.json | 变更清单 | 阶段产物 | 版本快照
L3: 执行编排层     状态机 | 阶段门控 | 并行任务 | 进度追踪
L2: 工具系统层     Plan工具集 | Code工具集 | Test工具集 | Review工具集
L1: 信息边界层      需求文档 | 上下文摘要 | 各阶段知识卡片
```

### 4.2 四专家 Agent 流水线

用四个专门的 Agent，替代原来单一 Agent 的全流程执行：

```
Master Agent（主持全局，协调四专家分工）
     │
     ├── Plan Expert（专注文档，理解需求，拆解任务）
     ├── Code Expert（专注代码，实现功能，代码规范）
     ├── Test Expert（专注验证，运行测试，覆盖率检查）
     └── Review Expert（专注质量，代码审查，安全审计）
```

| Agent | 核心职责 | 输入 | 输出 |
|-------|---------|------|------|
| Plan Expert | 需求理解、任务拆解 | 用户需求 | 需求文档、任务列表、技术方案 |
| Code Expert | 代码实现、代码规范 | 技术方案 | 源代码、代码变更清单 |
| Test Expert | 测试用例、自动化验证 | 代码变更 | 测试报告、覆盖率报告 |
| Review Expert | 代码审查、安全审计 | 各阶段输出 | 质量报告、风险评估 |

为什么比单 Agent 强：
- 每个专家有固定的系统提示词，角色切换零成本
- 专家之间通过结构化文档交接，不依赖记忆
- Review Expert 独立于 Code Expert，真正做到生成和验证分离

---

## 五、阶段门控设计

### 5.1 状态机

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

### 5.2 阶段门控规则

| 当前状态 | 触发 | 行动 | 退出条件 | 审批 |
|---------|------|------|---------|------|
| init | 用户提交需求 | 启动 Plan Expert | Plan Expert 输出需求文档 | 用户确认 |
| planning | 用户确认方案 | 启动 Code Expert | 所有代码变更已提交 | Review Expert |
| coding | Review 通过 | 启动 Test Expert | 测试通过率达到 80% | Test Expert |
| testing | 测试通过 | Review Expert + 报告 | 质量报告分数 >= 85 | Review Expert |

### 5.3 失败策略

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

## 六、记忆与状态管理

### 6.1 Quest State 文件结构

```
.quest/
├── state.json          # 当前状态机状态
├── context.md          # 全局上下文摘要
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
│   └── risks.md        # 风险清单
└── reports/
    └── delivery.md     # 最终交付报告
```

### 6.2 上下文压缩模板

每个阶段开始时，Master Agent 自动生成上下文摘要：

```markdown
# Quest 上下文摘要

## 项目背景
一句话描述项目在做什么

## 当前阶段
[X] 已完成 / [ ] 进行中 / [ ] 待开始

## 已完成的工作
- 需求文档已完成
- 技术方案已确认
- 核心模块已完成
- 测试覆盖率 72%

## 当前瓶颈
测试在 XXX 功能上失败，原因是 YYY

## 接下来
1. 修复 XXX 功能
2. 重跑测试
3. 生成最终报告
```

---

## 七、工具集分层设计

每个专家 Agent 只获得它需要的工具：

| Agent | 允许的工具 |
|-------|----------|
| Plan Expert | read, glob, grep, web_search, write, memory_search |
| Code Expert | read, write, exec, git, linter, formatter |
| Test Expert | exec, read, glob, write (测试文件) |
| Review Expert | read, glob, exec (安全扫描), linter |

关键设计：不把 bash/exec 写权限给 Review Expert，防止它绕过验证直接修代码。

---

## 八、改进后的完整流程图

```
用户提交需求
     │
     ▼
  Plan Expert  理解需求 -> 拆解任务 -> 输出 requirements.md
     │
     ▼ 用户确认方案
  Code Expert  写代码 -> 提交代码 -> 输出 changes.md
     │
     ▼ Review Expert 通过
  Test Expert  写测试 -> 运行测试 -> 输出 coverage.md
     │
     ▼ 测试通过
  Review Expert  代码审查 -> 安全审计 -> 输出 quality-report.md
     │
     ▼ 质量达标
  报告生成器  结构化输出 -> delivery-report.md
     │
     ▼ 用户确认
     交付完成
```

---

## 九、落地行动计划

第一周：搭建基础框架
- 创建 .quest/ 目录结构
- 编写四个专家 Agent 的系统提示词模板
- 实现简单的状态机 state.json
- 配置阶段门控规则

第二周：引入独立验证
- 将 Test Expert 和 Code Expert 完全分离
- 添加 Review Expert 的代码审查功能
- 实现测试覆盖率自动检查

第三周：增强恢复能力
- 实现每个阶段的快照机制
- 添加失败后的自动回滚
- 实现上下文压缩脚本

第四周：与 Claude Code 集成
- 封装成可复用的 Claude Code 项目模板
- 编写快捷命令
- 整理最佳实践文档

---

## 十、总结

| 维度 | 原设计 | 改进后 |
|------|--------|--------|
| Agent 架构 | 单 Agent 全流程 | 四专家流水线 |
| 上下文管理 | 依赖记忆 | 结构化文档交接 |
| 验证机制 | Agent 自测自 | 独立 Review Expert |
| 失败恢复 | 手动重试 | 自动快照 + 回滚 |
| 工具权限 | 全放开 | 按阶段精确授权 |
| 报告质量 | 依赖最后对话 | 结构化模板生成 |

核心洞察：AI 编程的瓶颈不在于模型有多强，而在于工程基础设施能不能支撑长链路、可靠执行的任务。
