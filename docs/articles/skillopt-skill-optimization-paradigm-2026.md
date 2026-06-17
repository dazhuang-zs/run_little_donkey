# SkillOpt：把Agent的技能当"可训练权重"，而不是一次性Prompt

2026年5月，微软、上海交大、同济、复旦联合发表了一篇论文（arXiv:2605.23904），提出了一个反直觉的观点：

**Agent的Skill文档，不应该由人手写，而应该像模型权重一样被"训练"优化。**

这个想法催生了SkillOpt，一个在52个评测单元中全部最优或并列最优的技能优化器。GitHub 4300+ Stars，MIT协议，可以直接替换Claude Code、Cursor等的.md Skill文件。

## 一、问题：手写Skill文档为什么不够好？

当前主流Agent（Claude Code、Cursor、Windsurf等）都支持Skill系统——把"如何完成某类任务"写成Markdown文档，Agent执行时加载。

但手写Skill有几个问题：

### 1.1 写的人不是AI专家
大多数Skill是领域专家写的，他们知道"该做什么"，但不知道"怎么写AI才能理解"。人觉得清晰的指令，AI可能理解歧义。

### 1.2 没有反馈循环
手写Skill后，没有人告诉你"这条Skill让Agent表现更好了还是更差了"。你只能凭感觉。

### 1.3 不同模型需要不同的Skill
同一条Skill在GPT-5上效果好，在DeepSeek上可能效果差。但手写Skill是"一刀切"的。

SkillOpt的核心理念：**把Skill文档当作LLM Agent的"可训练权重"，用数据驱动的方式在文本空间中迭代优化。**

## 二、ReflACT循环：文本空间中的训练

SkillOpt的核心是ReflACT循环——一个6步迭代过程：

```
Rollout → Reflect → Aggregate → Select → Update → Validate
  ↓        ↓         ↓         ↓        ↓        ↓
 执行任务   反思结果   汇总经验   选最优   更新Skill  验证
```

### 2.1 Rollout：用当前Skill执行任务
Agent带着当前的best_skill.md执行一组任务，收集执行轨迹（trace）。

### 2.2 Reflect：反思失败原因
对每个执行轨迹，LLM分析：
- 哪些步骤成功了？Skill的哪些部分有帮助？
- 哪些步骤失败了？Skill的哪些部分误导了Agent？

### 2.3 Aggregate：汇总反思结论
把多个任务的反思维度合并，找到Skill中最需要修改的部分。

### 2.4 Select：选择最优修改
生成多个候选修改，用评估函数选最优的一个。

### 2.5 Update：更新Skill文档
用四种编辑操作之一修改Skill：

| 操作 | 说明 | 类比 |
|------|------|------|
| add | 在末尾追加新指令 | 新增一层神经网络 |
| insert_after | 在指定位置后插入 | 在特定层后加模块 |
| replace | 替换指定段落 | 替换某一层的权重 |
| delete | 删除无用指令 | 剪枝（删除冗余参数） |

### 2.6 Validate：严格门控
**最关键的一步。** 只有在held-out验证集上**严格更好**的修改才能被接受。否则，回滚到上一版本。

这就像深度学习中的早停（early stopping）和验证集门控，只不过发生在文本空间而不是参数空间。

## 三、四个关键机制

### 3.1 Edit Budget（编辑预算）
类比深度学习中的学习率（learning rate）。

默认edit budget = 4，带余弦衰减。即每次迭代最多修改4处，随着迭代次数增加逐渐减少修改幅度。

**为什么不是无限编辑？** 因为过度修改会导致Skill"漂移"——改了太多地方，反而把原本正确的部分也改坏了。就像学习率太大导致训练不稳定。

### 3.2 Validation Gate（验证门控）
类比深度学习中的验证集早停。

每次修改Skill后，在验证集上测试。只有严格更好的版本才能替换当前版本。如果连续多次修改都没有提升，停止迭代。

**这解决了一个核心问题：怎么知道Skill改好了而不是改坏了？** 没有验证门控的Skill优化，就是在黑暗中摸索。

### 3.3 Rejection Buffer（拒绝缓冲）
如果某次修改导致验证集性能下降，这个修改不会被直接丢弃，而是存入拒绝缓冲。下次迭代时，系统会参考被拒绝的修改，避免生成类似的有害编辑。

类比深度学习中的负样本学习——从失败中学习什么不该做。

### 3.4 Bounded Edit（有界编辑）
每次编辑操作的粒度受到约束。不能一次性重写整个Skill，只能在局部做add/insert/replace/delete。

**为什么？** 因为Skill文档中有很多"稳定有效"的指令，大量重写会破坏这些已经验证过的部分。局部编辑更安全、更可控。

## 四、实验结果

SkillOpt在6个benchmark × 7个目标模型 × 3种执行环境 = 52个评测单元上，全部最优或并列最优。

| 对比方法 | 平均提升（vs手写Skill） |
|---------|----------------------|
| 手写Skill | 基线 |
| 少量示例（Few-shot） | +3~8分 |
| 自动Prompt优化 | +5~12分 |
| SkillOpt | **+19~25分** |

关键发现：
- **模型越弱，SkillOpt的提升越大。** 7B参数模型提升+25分，GPT-5级别模型提升+19分。因为弱模型更需要好指令来弥补能力差距。
- **优化后的Skill可以跨模型迁移。** 在GPT-5上优化的Skill，用在Claude上也有提升（虽然不如原生优化的多）。
- **优化收敛快。** 大多数Skill在3-5轮迭代后就收敛了。

## 五、SkillOpt vs 其他方法

| 维度 | 手写Skill | Few-shot | Auto-Prompt | SkillOpt |
|------|----------|----------|-------------|----------|
| 优化空间 | 人工经验 | 输入端 | 输入端 | **Skill文档（系统端）** |
| 反馈机制 | 无 | 无 | 单轮评估 | **多轮迭代+验证门控** |
| 编辑粒度 | 全文重写 | 新增示例 | 改写prompt | **局部编辑（4种操作）** |
| 过拟合防护 | 无 | 无 | 无 | **验证集门控+拒绝缓冲** |
| 额外推理成本 | 0 | +10-30% | +5-15% | **0（优化后Skill零额外成本）** |

最后一点至关重要：SkillOpt的优化发生在"训练时"，不在"推理时"。优化完的Skill直接替换原来的.md文件，Agent加载后执行速度和原来一样快。

## 六、如何使用SkillOpt

### 6.1 安装

```bash
pip install skillopt
# 或从源码
git clone https://github.com/microsoft/SkillOpt.git
cd SkillOpt
pip install -e .
```

### 6.2 准备数据

你需要三样东西：
1. **初始Skill文档**（best_skill.md，300-2000 token）
2. **训练任务集**（一组带标注的输入-输出对）
3. **验证任务集**（和训练集不同的另一组）

### 6.3 运行优化

```python
from skillopt import SkillOptimizer

optimizer = SkillOptimizer(
    model="gpt-5",           # 目标模型
    edit_budget=4,           # 编辑预算
    max_iterations=10,       # 最大迭代次数
    validation_strict=True   # 严格验证门控
)

optimized_skill = optimizer.optimize(
    initial_skill="best_skill.md",
    train_tasks="train_tasks.jsonl",
    val_tasks="val_tasks.jsonl"
)

# 保存优化后的Skill
optimized_skill.save("best_skill_optimized.md")
```

### 6.4 替换现有Skill

优化后的Skill就是一份Markdown文档，直接替换Claude Code的`.claude/skills/`、Cursor的`.cursor/rules/`、或任何支持Skill文档的Agent框架的对应文件。

## 七、更深层启示：从Prompt工程到技能训练

SkillOpt代表了一个范式转变：

**过去**：人写Skill → Agent执行 → 人凭感觉调整 → 循环
**现在**：人写初始Skill → SkillOpt自动训练 → 验证集保证不退化 → Agent用优化版Skill执行

这个转变有几个重要含义：

1. **Skill是可训练的，不是一次性的。** 就像模型权重需要训练数据来优化，Skill也需要执行反馈来优化。
2. **优化发生在文本空间，不是参数空间。** 不需要GPU，不需要梯度，只需要LLM调用和验证集。
3. **优化的Skill零额外推理成本。** 不像RAG（每次检索有延迟）或Few-shot（每次注入有token开销），优化后的Skill就是一份更好的指令文档。

**一句话总结**：SkillOpt把"写好Prompt"从一门手艺变成了一门工程——有数据、有验证、有迭代、有保证。

## 数据来源

- arXiv:2605.23904 — SkillOpt: Executive Strategy for Self-Evolving Agent Skills (Microsoft/Shanghai Jiao Tong University/Tongji University/Fudan University, 2026-05)
- SkillOpt GitHub: github.com/microsoft/SkillOpt (4300+ Stars, MIT协议)
- 相关论文：MUSE-Autoskill（五阶段技能生命周期框架）、SkillEvolver（元技能驱动在线学习）、EmbodiSkill（技能感知反思）
- 6 benchmark × 7 model × 3 environment = 52个评测单元，全部最优或并列最优
