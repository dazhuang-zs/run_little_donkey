# AI写代码的致命缺陷：约束衰减——为什么你的Agent越长越笨？

你有没有这种体验：让AI写一个小函数，干净利落。让它写一个完整后端系统，前几个文件还挺靠谱，越往后越离谱——数据库字段对不上、API规范忘了遵守、业务规则写到一半就丢了。

不是幻觉，不是上下文溢出。这是一个被arXiv论文正式命名的现象：**约束衰减（Constraint Decay）**。

## 一、什么是约束衰减？

2026年5月，arXiv论文《Constraint Decay: The Fragility of LLM Agents in Backend Code Generation》（arXiv:2605.06445）给出了精确的定义和量化证据：

> 当结构约束逐渐累积时，Agent的性能出现显著下降。能力较强的配置在完整约束任务上比基线任务平均损失30分（assertion pass rate），而较弱的配置接近零分。

翻译成大白话：**约束越多，Agent越笨。不是慢慢笨，是断崖式笨。**

这个发现来自一组严格的对照实验。研究者固定了统一的API合约，在8个Web框架上设置了80个greenfield生成任务和20个feature-implementation任务，用双重评估（端到端行为测试 + 静态验证器）来隔离结构复杂度的影响。

## 二、为什么约束会衰减？三个根因

### 2.1 注意力稀释：上下文越长，约束越"透明"

LLM的注意力机制天然倾向近端信息。当你的约束（数据库schema、API规范、业务规则）写在prompt前面，而Agent已经生成了几百行代码后，模型对初始约束的注意力权重会自然下降。

这不是bug，是transformer架构的物理特性。就像人读到文章第10页，对第1页的细节记忆会模糊一样。

实验数据佐证：在Flask（极简框架，约束少）上，Agent表现尚可；但在FastAPI和Django（约定重于配置，约束隐含在框架惯例中）上，表现大幅下滑。隐式约束比显式约束更容易被"遗忘"。

### 2.2 ORM陷阱：数据层是重灾区

论文的错误分析发现，**数据层缺陷（data-layer defects）是约束衰减的首要根因**。

具体表现：
- 错误的查询构造（query composition错误）
- ORM运行时违规（ORM runtime violations）
- 关系映射遗漏（外键、级联、索引全忘）

为什么数据层最容易崩？因为ORM本身就是一层约束翻译器。模型需要在"业务逻辑→ORM语法→SQL语义"三层之间保持一致，任何一层偏移都会导致数据层崩溃。

### 2.3 惯性生成：模型倾向于"顺手写"

当约束与模型的训练分布不一致时，模型会退回到训练数据中最常见的模式，而不是遵守你指定的约束。

比如你要求"所有接口统一返回`{code, data, message}`格式"，模型前3个接口遵守了，第4个就开始返回裸数据。不是不知道，是"顺手"——训练数据中大量裸返回的样本形成了惯性。

## 三、约束衰减到底有多严重？

来看论文的核心数据：

| 任务类型 | 最小约束 | 部分约束 | 完整约束 | 分数下降 |
|---------|---------|---------|---------|---------|
| 强配置（GPT-5级别） | 85+ | 70+ | 55+ | -30分 |
| 弱配置（7B开源模型） | 60+ | 35+ | <10 | -50+分 |
| Flask框架 | 78+ | 72+ | 65+ | -13分 |
| Django框架 | 72+ | 55+ | 38+ | -34分 |

关键发现：
- **30%的生成结果因约束衰减而不可用**——即使使用了步骤拆分（Plan模式），约束衰减仍导致30%+的结果偏离需求
- 框架敏感度巨大：极简框架（Flask）的衰减幅度是重约定框架（Django）的1/3
- 弱模型接近"归零"：7B参数模型在完整约束下几乎无法完成生成

## 四、现有的缓解手段为什么不够？

### 4.1 Plan模式？不够

很多人以为"先规划再执行"能解决问题。论文证明：即使有显式的步骤拆分，约束衰减仍然发生。Plan只解决了"做什么"的问题，不解决"怎么做才不偏离约束"的问题。

### 4.2 更长的上下文？不够

约束衰减不是上下文溢出（overflow），而是注意力稀释（dilution）。给更多上下文不等于模型会更注意你的约束。128K上下文里塞100条约束，和8K上下文里塞10条约束，稀释程度是一样的。

### 4.3 更强的模型？缓解但不根治

强模型衰减更慢，但不是不衰减。GPT-5级别模型在完整约束下也损失30分。而且"更强模型"意味着更高成本——用4倍的价格换1.5倍的抗衰减能力，ROI很低。

## 五、真正有效的四个对抗策略

### 5.1 约束回溯机制（Constraint Backtracking）

论文作者的建议：在Agent循环中增加约束回溯步骤。不是等全部写完再检查，而是每生成一个文件/模块后，主动回查初始约束。

实现思路：
```python
# 在Agent循环中增加约束检查点
def agent_loop_with_constraint_check(task, constraints):
    completed_files = []
    for step in decompose(task):
        # 生成代码
        code = llm.generate(step, context=build_context(constraints, completed_files))
        # 约束回溯检查
        violations = check_constraints(code, constraints)
        if violations:
            # 重新生成，带上违反的约束作为强化prompt
            code = llm.regenerate(step, 
                context=build_context(constraints, completed_files),
                focus=violations)
        completed_files.append(code)
    return completed_files
```

关键：约束不是写在开头就完事，而是要在每个生成步骤中**反复注入**。

### 5.2 规格先行（Spec-First）

字节跳动内部的AI辅助开发流程数据：直接让AI写代码，返工率60%+；先让AI产出Spec（规格说明），人类审核通过后再写代码，一次通过率提升到70%+。

为什么有效？因为Spec本身就是约束的显式化。当约束从"写在prompt里的文字"变成"经过审核的正式文档"，模型在生成时有更强的锚点。

### 5.3 编译器反馈循环（Compiler-in-the-Loop）

这是目前对抗约束衰减最激进的方案，来自另一篇arXiv论文（2605.23772）。

研究用Claude Code + Lean 4定理证明器做程序验证，端到端成功率达到98.1%。

核心机制：不是让Agent"自觉遵守约束"，而是用编译器/验证器**强制检查**。Agent每写一步，编译器立刻反馈是否符合规范。不符合就改，直到通过。

| 阶段 | 成功率 |
|------|--------|
| 规范认证 | 98.8% |
| 实现认证 | 87.5% |
| 端到端流程 | 98.1% |

这个方案的本质：**不信任Agent的自觉性，用机器验证替代人类审查。**

### 5.4 SkillOpt范式：把约束固化成可训练的技能

微软SkillOpt（arXiv:2605.23904，GitHub 4300+ Stars）提供了一个更优雅的思路：把约束遵循能力固化成Skill文档，用训练循环不断优化。

具体做法：
1. 把"如何遵守XX约束"写成Skill文档（best_skill.md，300-2000 token）
2. 用ReflACT循环（Rollout→Reflect→Aggregate→Select→Update→Validate）在文本空间中迭代优化
3. 只有在验证集上严格更好的Skill才能替换当前版本（Validation Gate）
4. 最终产出的Skill直接塞给Agent用，零额外推理成本

实验数据：在52个评测单元中全部最优，GPT-5.5上平均提升+19到+25分。

关键洞察：SkillOpt不是在推理时对抗衰减，而是在训练时**预防腐化**。一个经过优化的Skill，本身就是高约束遵循度的指令集。

## 六、约束衰减对不同角色的实际影响

### 对应用开发者
你的API规范、数据schema、业务规则，在长对话中会被Agent逐渐遗忘。对策：每5-10轮主动注入关键约束，或者用Spec-First流程把约束固化为正式文档。

### 对Agent框架开发者
纯ReAct循环是不够的。你需要在循环中增加约束回溯步骤，或者支持外部验证器接入。vLLM的Continuous Batching解决了GPU利用率问题，但没人解决Agent的"约束利用率"问题。

### 对团队Leader
不要指望Agent一次性生成完整后端系统。拆成小任务、每步验证、约束反复注入，才能把可用率从40%拉到80%+。这不是偷懒，是对抗约束衰减的工程纪律。

## 七、约束衰减的深层启示

约束衰减揭示了一个更深层的问题：**当前LLM Agent的本质是"短期记忆型选手"**。

它能记住你上一轮说的话，但记不住你第1轮说的规则。它能遵守眼前的约束，但无法在长序列中持续维持约束遵循。

这和人类初级工程师的表现惊人相似：新手写代码也经常"写着写着就忘了需求"。区别在于，人类可以通过Code Review、测试、结对编程来纠偏，而Agent目前缺少这些"外部约束维持机制"。

所以，解决约束衰减的终极方向不是更强的模型，而是**更好的约束维持系统**：

1. **约束回溯**——主动反复注入，而不是写一次就完
2. **机器验证**——编译器/测试/形式化验证替代人类审查
3. **技能固化**——约束遵循能力训练成可复用的Skill
4. **Spec-First**——约束先于代码，审核先于生成

约束衰减不是Agent的绝症，但它是一个警钟：**AI写代码的瓶颈，不在生成能力，而在约束维持能力。**

## 数据来源

- arXiv:2605.06445 — Constraint Decay: The Fragility of LLM Agents in Backend Code Generation (2026-05-07)
- arXiv:2605.23772 — Agentic Proving for Program Verification (Claude Code + Lean 4)
- arXiv:2605.23904 — SkillOpt: Executive Strategy for Self-Evolving Agent Skills (Microsoft, 2026-05)
- 字节跳动AI辅助开发实践数据（Spec-First模式返工率对比）
- SkillOpt GitHub: github.com/microsoft/SkillOpt (4300+ Stars, MIT协议)
