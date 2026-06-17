# Agent四层记忆架构：为什么你的Agent总是失忆？

你有没有这种体验：跟Agent聊了三轮，它还记得你之前说的偏好。聊到第十轮，它开始问"你之前提到过什么来着？"——然后就真的忘了。

不是上下文窗口不够大，而是**记忆架构不完整**。

大多数Agent只有"工作记忆"（上下文窗口），没有"长期记忆"。就像人只有短期记忆，没有长期记忆一样——每段对话都是全新的开始。

## 一、四层记忆架构

参考认知科学对人类记忆的分类，Agent的记忆系统也应该分为四层。每一层的生命周期、存储方式、检索策略都不同。

```
┌───────────┐
│ 过程记忆 (Procedural) │ ← 最持久，技能和工作流程
│ 语义记忆 (Semantic) │ ← 长期，事实性知识和用户偏好
│ 情节记忆 (Episodic) │ ← 中期，过去的对话和事件记录
│ 工作记忆 (Working) │ ← 最短，当前上下文窗口
└───────────┘
```

### 1.1 工作记忆（Working Memory）
**生命周期**：当前会话
**容量限制**：上下文窗口大小（8K-128K tokens）
**实现方式**：LLM的context window，messages列表直接注入prompt

这是大多数Agent唯一拥有的记忆层。优点是零延迟（不需要检索），缺点是会话结束就清空，而且容量有限。

### 1.2 情节记忆（Episodic Memory）
**生命周期**：跨会话，但有时效性
**存储内容**：过去的对话片段、行为记录、事件日志
**实现方式**：向量化存储 + 摘要压缩

最简单的形式是结构化日志：
```python
episode = {
    "timestamp": "2026-06-15T10:30:00",
    "task": "帮用户分析基金持仓",
    "result": "成功，用户持有3只医药ETF",
    "user_feedback": "满意，要求后续定期推送医药行业分析"
}
```

随着时间，这些episode可以压缩成摘要，减少存储和检索成本。

### 1.3 语义记忆（Semantic Memory）
**生命周期**：永久（除非主动删除）
**存储内容**：用户偏好、事实性知识、领域概念
**实现方式**：KV Store（LangGraph store）或向量数据库

典型内容：
- "用户喜欢简洁的代码风格，不要过度设计"
- "用户的项目使用FastAPI + PostgreSQL技术栈"
- "用户对医药板块有持仓，关注创新药ETF"

### 1.4 过程记忆（Procedural Memory）
**生命周期**：永久，通过学习和反馈持续优化
**存储内容**：技能文档（Skill）、工作流程、操作规范
**实现方式**：可训练的Skill文档（如SkillOpt的best_skill.md）

这是最接近"肌肉记忆"的一层。Agent通过反复执行某个任务，把"怎么做"固化成技能文档，后续执行时直接加载，不需要重新学习。

## 二、为什么大多数Agent只有工作记忆？

三个原因：

### 2.1 实现复杂度
工作记忆是"免费的"——LLM天生支持上下文窗口。但要实现其他三层，需要：
- 存储后端（向量数据库/关系数据库/KV存储）
- 检索策略（相似性搜索/时间衰减/重要性打分）
- 写入策略（什么时候写、写什么、怎么压缩）

每一层都是额外的工程工作。

### 2.2 延迟成本
工作记忆的检索是O(1)（直接注入上下文）。其他记忆层的检索需要：
- 向量搜索（10-50ms）
- 数据库查询（5-20ms）
- 内容压缩和格式化（10-100ms）

虽然不高，但加起来会影响用户体验，尤其是在实时对话场景。

### 2.3 准确性问题
从长期记忆中检索出来的内容可能是过时的、不相关的、甚至是错误的。如果检索策略不够好，引入的错误信息反而会让Agent表现更差。

**这就是为什么大多数Agent选择"只用工工作记忆"——不是不知道其他层有用，而是实现成本和风险太高。**

## 三、完整的工程实现

以下是一个简化的四层记忆管理器实现（基于CSDN上多个开源实现综合）：

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class MemoryItem:
    """单条记忆"""
    id: str
    content: str
    memory_type: str  # semantic/episodic/procedural
    importance: float  # 0-1，重要性评分
    created_at: str
    last_accessed: str
    access_count: int = 0

class MemoryManager:
    def __init__(self, vector_store, kv_store):
        self.vector_store = vector_store  # 情节+语义记忆
        self.kv_store = kv_store        # 语义记忆（精确查询）
        self.working_memory = []         # 工作记忆（当前上下文）
    
    def retrieve(self, query: str, max_items: int = 5):
        """检索相关记忆"""
        # 1. 工作记忆：直接返回当前上下文
        working_context = self._format_working_memory()
        
        # 2. 情节记忆：向量搜索过去相似的任务
        episodes = self.vector_store.search(
            collection="episodic",
            query=query,
            limit=max_items
        )
        
        # 3. 语义记忆：精确查询用户偏好
        preferences = self.kv_store.get(f"user:{query.user_id}:preferences")
        
        # 4. 过程记忆：加载相关技能文档
        skills = self._load_relevant_skills(query)
        
        return {
            "working": working_context,
            "episodes": episodes,
            "preferences": preferences,
            "skills": skills
        }
    
    def consolidate(self):
        """记忆整合：把工作记忆中的重要内容转移到长期记忆"""
        # 检测重要片段（基于用户反馈、任务完成度、访问频率）
        important_items = self._detect_important_items(self.working_memory)
        
        for item in important_items:
            if item.type == "preference":
                # 写入语义记忆
                self.kv_store.set(f"user:{item.user_id}:preferences", item.content)
            elif item.type == "event":
                # 写入情节记忆
                self.vector_store.insert("episodic", item.to_vector())
            
            # 更新访问统计
            item.access_count += 1
            item.last_accessed = datetime.now().isoformat()
```

## 四、存储后端选型

不同记忆层适合不同的存储后端：

| 记忆层 | 推荐存储 | 原因 |
|--------|---------|------|
| 工作记忆 | LLM上下文窗口（原生支持） | 零延迟，不需要外部存储 |
| 情节记忆 | 向量数据库（Qdrant/Pinecone） | 相似性搜索，适合检索"相似的任务" |
| 语义记忆 | KV Store（Redis/SQLite）或图数据库（Neo4j） | 精确查询（用户ID→偏好），或关系查询（概念之间的关联） |
| 过程记忆 | 文件系统（Markdown文档）或向量数据库 | Skill文档需要版本管理和语义搜索 |

**混合存储策略**：大多数生产级Agent使用"向量+关系+KV"的混合方案。向量数据库负责相似性检索，关系数据库负责精确查询和关联关系，KV Store负责高速缓存。

## 五、记忆管理的三个核心机制

### 5.1 时间衰减（Time Decay）
不是所有记忆都永远重要。随着时间推移，访问频率低的记忆应该自动降级或删除。

```python
def decay_score(memory_item: MemoryItem) -> float:
    """计算记忆的衰减后重要性"""
    days_since_access = (datetime.now() - datetime.fromisoformat(memory_item.last_accessed)).days
    decay_factor = 0.95 ** days_since_access  # 每天衰减5%
    return memory_item.importance * decay_factor * (1 + memory_item.access_count * 0.1)
```

### 5.2 重要性打分（Importance Scoring）
写入时评估这条记忆的重要性，避免存储无用信息。

打分维度：
- **用户显式标记**（"记住这个"）→ 重要性=1.0
- **任务关键性**（支付信息、安全配置）→ 重要性=0.8
- **访问频率**（被检索过的记忆）→ 重要性=0.5 + 0.1*访问次数
- **时间新鲜度**（最近的信息更有用）→ 重要性=0.3 * (1 - days_old/365)

### 5.3 定期整合（Periodic Consolidation）
每隔一段时间（比如每周），把相关的情节记忆整合成语义记忆，删除冗余信息。

```
原始情节记忆（每天产生）:
  - 2026-06-10: 用户说喜欢简洁代码
  - 2026-06-12: 用户说不要过度设计
  - 2026-06-14: 用户说代码要直接，不要绕弯子

整合后的语义记忆（永久存储）:
  - "用户偏好：简洁直接的代码风格，反对过度设计"
```

## 六、LangGraph中的四层记忆实现

LangGraph提供了内置的记忆管理支持：

```python
from langgraph.checkpoint import MemorySaver
from langgraph.store import InMemoryStore

# 工作记忆：会话历史
checkpointer = MemorySaver()  # 自动管理messages列表

# 语义记忆：用户偏好和长期知识
store = InMemoryStore()  # KV Store，支持语义搜索

# 情节记忆：需要自己实现
# 方案1：用LangGraph的store存储episode，用相似度搜索检索
# 方案2：接入外部向量数据库（Qdrant/Pinecone）

# 过程记忆：Skill文档
# 方案：把Skill文档存在store里，Agent执行前加载
```

## 七、核心结论

**Agent的"失忆症"不是上下文窗口太小，而是记忆架构不完整。**

完整的记忆系统需要四层：
1. **工作记忆**——当前上下文，零延迟但容量有限
2. **情节记忆**——过去的事件记录，需要向量搜索
3. **语义记忆**——长期知识和偏好，需要KV或图存储
4. **过程记忆**——技能和工作流程，需要可训练的Skill文档

大多数Agent只有第一层。要做成"真正记住用户"的Agent，需要把四层都实现，并且做好**存储选型、检索策略、记忆整合**这三个工程难点。

**一句话总结**：Agent的记忆系统不是"上下文窗口够不够大"的问题，而是"你有没有给Agent装上长期记忆"的问题。

## 数据来源

- CSDN博客：《AI Agent长期记忆工程2026：让智能体真正"记住"一切的完整实现方案》
- CSDN博客：《Agent系列(六)：记忆管理——让Agent记住重要的事》（LangGraph实现）
- CSDN博客：《AI Agent的记忆系统架构2026：四种记忆类型与工程实现完全指南》
- 开源实现：多个GitHub项目中的MemoryManager代码示例（综合整理）
- LangGraph官方文档：MemorySaver + InMemoryStore使用指南
