# AI 开发进阶（第4篇）：Context Engineering 深入——长上下文的真相与大坑

> 适合读者：已读完基础9篇 + 第①②③篇，被"百万 token 上下文"宣传误导，想真实了解长上下文
> 预计阅读时间：35分钟
> 作者：AI小渔村

---

## 前言：百万 token 上下文，可能是最大的智商税

2026年，各家都在宣传"百万 token 上下文"：

- Kimi：200万 token
- GPT-4o：128k token  
- Claude 3：200k token
- 通义千问：100万 token

但实际情况是：
- **能用好 10k token 上下文的团队，已经超过 90% 的竞争者**
- **百万 token 上下文，大多数场景是过度设计**

这篇讲的是：**什么时候真的需要长上下文、为什么大多数情况下不需要、以及怎么处理长上下文的坑**。

---

## 一、长上下文的真实情况

### 1.1 上下文越长，问题越多

```
Token 数量    →    问题严重程度
─────────────────────────────────
1k-2k         →    基本没问题
5k-10k        →    开始有遗忘
20k-50k       →    中间信息遗忘严重
100k+         →    需要特殊技巧
200k+         →    大多数模型处理不好
```

**核心问题：中间信息遗忘**

模型对上下文的不同位置，注意力是不同的：

```
开头：★★★★★ 记得最清楚
中间：★☆☆☆☆ 容易忘记
结尾：★★★★☆ 最后的信息记得比较清楚
```

这就是著名的 **"中间丢失"（Lost in the Middle）问题**。

### 1.2 长上下文的三个大坑

**大坑 1：模型根本不支持**

有些模型宣传"百万 token"，实际效果：
- 有的只支持输入，不支持输出
- 有的支持但严重降智
- 有的是 API 限制，不是模型能力

**大坑 2：成本爆炸**

| Token 数量 | 费用（估算） |
|------------|-------------|
| 1k | $0.002 |
| 10k | $0.02 |
| 100k | $0.20 |
| 1M | $2.00 |

如果你每天处理 1 万个请求，每个请求 100k token：
- 每天成本：$2,000
- 每月成本：**$60,000+

**大坑 3：延迟太高**

100k token 的输入，推理延迟可能是：
- 首 token：3-5 秒
- 完全输出：30-60 秒

用户不可能等这么久。

---

## 二、什么时候真的需要长上下文？

### 2.1 适合长上下文的场景

| 场景 | 适合的上下文长度 | 示例 |
|------|----------------|------|
| **长文档问答** | 10k-50k | 读一本书回答问题 |
| **代码库分析** | 30k-100k | 分析整个项目结构 |
| **长对话历史** | 5k-20k | 多轮对话记住上下文 |
| **长程推理** | 10k-30k | 复杂问题需要多步推理 |

### 2.2 不需要长上下文的场景

| 场景 | 不适合的原因 | 应该用什么 |
|------|------------|------------|
| 简单问答 | 问题本身就很短 | 直接问，不需要上下文 |
| 单轮对话 | 不需要记住历史 | 不存储历史消息 |
| 工具调用 | 只关心当前参数 | 只传相关参数 |
| 分类/提取 | 输入就是全部信息 | 直接处理输入 |

### 2.3 判断法则

**简单判断：你能用一句话说清楚需要什么信息吗？**

- 能 → 不需要长上下文
- 不能（比如需要参考整篇文档） → 可能需要

**更准确的判断：这个任务需要在很多信息中找到答案吗？**

- 是（比如在 100 页文档中找某个答案） → 需要 RAG，不是长上下文
- 否（比如基于某个原则推理） → 不需要长上下文

---

## 三、正确处理长上下文的方法

### 3.1 方法一：RAG（不是越长越好）

**核心思路**：不把���有内容都塞给模型，而是只传递**最相关的内容**。

```python
from dataclasses import dataclass
from typing import List
import numpy as np

@dataclass
class RetrievedChunk:
    content: str
    similarity: float
    source: str

class NaiveRAG:
    """简单的 RAG 实现"""
    
    def __init__(self, chunks: List[str], embeddings):
        self.chunks = chunks
        self.embeddings = embeddings
        self.chunk_embeddings = embeddings.encode(chunks)
    
    def retrieve(self, query: str, top_k: int = 3) -> List[RetrievedChunk]:
        """检索最相关的内容"""
        
        query_embedding = self.embeddings.encode([query])[0]
        
        # 计算相似度
        similarities = np.dot(self.chunk_embeddings, query_embedding)
        
        # 取 top_k
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return [
            RetrievedChunk(
                content=self.chunks[i],
                similarity=float(similarities[i]),
                source=f"chunk_{i}"
            )
            for i in top_indices
        ]
    
    def build_context(self, query: str, retrieved: List[RetrievedChunk]) -> str:
        """构建上下文"""
        
        context_parts = [
            f"[参考文档 {r.source}]" for r in retrieved
        ]
        context_parts.append(f"[用户问题] {query}")
        
        return "\n\n".join(context_parts)


# 使用示例
chunks = [
    "第一章：Python 基础语法...",
    "第二章：函数和模块...",
    "第三章：面向对象编程...",
    # ... 更多 chunks
]

rag = NaiveRAG(chunks, embeddings)

# 用户问题：什么是面向对象
query = "什么是面向对象"
retrieved = rag.retrieve(query, top_k=2)

context = rag.build_context(query, retrieved)
# 构建的上下文可能只有 500-1000 token，而不是把整本书都塞进去
```

### 3.2 方法二：分层摘要

**核心思路**：把长文档层层往上抽象，需要看细节时再下沉。

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class DocumentNode:
    content: str      # 当前层内容
    level: int         # 层级（越大越概要）
    children: List['DocumentNode'] = None
    
    def token_count(self) -> int:
        return len(self.content) // 4

class HierarchicalSummarizer:
    """分层摘要器"""
    
    def __init__(self, llm, chunk_size: int = 2000):
        self.llm = llm
        self.chunk_size = chunk_size
    
    def build_hierarchy(self, full_document: str) -> DocumentNode:
        """构建文档层级"""
        
        # 1. 分 chunk
        chunks = self._split_into_chunks(full_document)
        
        # 2. 每个 chunk 生成摘要（Level 1）
        level1_nodes = []
        for chunk in chunks:
            summary = self._summarize(chunk, level=1)
            level1_nodes.append(DocumentNode(
                content=summary,
                level=1,
                children=[]
            ))
        
        # 3. Level 1 摘要合成 Level 2
        if len(level1_nodes) > 1:
            level2_summary = self._summarize(
                "\n".join(n.content for n in level1_nodes),
                level=2
            )
            root = DocumentNode(
                content=level2_summary,
                level=2,
                children=level1_nodes
            )
        else:
            root = level1_nodes[0]
        
        return root
    
    def _split_into_chunks(self, document: str) -> List[str]:
        """分块"""
        chunks = []
        for i in range(0, len(document), self.chunk_size):
            chunks.append(document[i:i+self.chunk_size])
        return chunks
    
    async def _summarize(self, text: str, level: int) -> str:
        """生成摘要"""
        
        prompt = f"""请用{level * 50}字以内概括以下内容的核心要点：

{text}

要点："""
        
        response = await self.llm.chat([{"role": "user", "content": prompt}])
        return response.content.strip()
    
    def retrieve_relevant(self, root: DocumentNode, query: str, 
                         target_tokens: int = 3000) -> str:
        """根据查询检索相关内容"""
        
        # 粗筛：遍历所有 Level 1 节点，找相关的
        relevant_nodes = []
        for node in (root.children or [root]):
            if self._is_relevant(query, node.content):
                relevant_nodes.append(node)
        
        # 细选：凑够目标 token 数
        result_parts = []
        current_tokens = 0
        
        for node in relevant_nodes:
            node_tokens = node.token_count()
            if current_tokens + node_tokens > target_tokens:
                continue
            result_parts.append(node.content)
            current_tokens += node_tokens
        
        return "\n\n".join(result_parts)
    
    def _is_relevant(self, query: str, content: str) -> bool:
        """简单判断是否相关"""
        query_words = set(query.lower().split())
        content_lower = content.lower()
        return any(word in content_lower for word in query_words)
```

### 3.3 方法三：滑动窗口（适合对话）

**核心思路**：不要一次性加载所有历史，而是用窗口滑动，保持最近的上下文。

```python
from dataclasses import dataclass, field
from typing import List
from collections import deque

@dataclass
class Message:
    role: str  # "user" / "assistant"
    content: str

class SlidingWindowContext:
    """滑动窗口上下文"""
    
    def __init__(self, max_tokens: int = 8000, keep_system: bool = True):
        self.max_tokens = max_tokens
        self.keep_system = keep_system
        self.messages: deque = deque()
        self.system_prompt: str = ""
    
    def set_system(self, prompt: str):
        """设置系统提示"""
        self.system_prompt = prompt
    
    def add_message(self, role: str, content: str):
        """添加消息"""
        self.messages.append(Message(role=role, content=content))
        self._ensure_limit()
    
    def _ensure_limit(self):
        """确保不超过 token 限制"""
        while self._total_tokens() > self.max_tokens and len(self.messages) > 1:
            # 移除最老的消息（保留系统提示）
            if self.keep_system and self.messages[0].role == "system":
                break
            self.messages.popleft()
    
    def _total_tokens(self) -> int:
        """计算总 token 数"""
        total = sum(len(m.content) // 4 for m in self.messages)
        if self.system_prompt:
            total += len(self.system_prompt) // 4
        return total
    
    def get_context_for_llm(self) -> List[dict]:
        """获取发送给 LLM 的上下文"""
        result = []
        
        if self.system_prompt:
            result.append({"role": "system", "content": self.system_prompt})
        
        result.extend([
            {"role": m.role, "content": m.content}
            for m in self.messages
        ])
        
        return result
    
    def summarize_old_messages(self, llm) -> str:
        """压缩旧消息成摘要"""
        
        if len(self.messages) <= 2:
            return ""
        
        old_messages = list(self.messages)[:-2]  # 保留最近 2 条
        
        prompt = f"""请用 100 字概括以下对话的核心内容：

{chr(10).join(f"{m.role}: {m.content[:100]}" for m in old_messages)}

摘要："""
        
        return llm.chat(prompt).content.strip()


# 使用示例
ctx = SlidingWindowContext(max_tokens=8000)
ctx.set_system("你是一个专业助手。")

# 对话进行中
ctx.add_message("user", "帮我查一下北京天气")
ctx.add_message("assistant", "北京今天晴，15-25度")

ctx.add_message("user", "那上海呢？")
# 此时只会发送：上海呢？+ 最近的历史（因为有完整上下文）
# 更早的历史如果超过了窗口，会被压缩成摘要
```

---

## 四、长上下文的工程实践

### 4.1 判断是否需要长上下文的决策树

```
这个任务需要参考多少外部信息？
    │
    ├─ ≤2,000 token ──→ 不需要，直接放在 prompt 里
    │
    ├─ 2,000-10,000 token ──→ RAG，取相关片段
    │
    ├─ 10,000-50,000 token ──→ 分层摘要 + RAG
    │
    └─ 50,000+ token ──→ 真的需要长上下文，确认利弊后再决定
```

### 4.2 长上下文的降级策略

当检测到上下文过长时，自动降级：

```python
class ContextFallback:
    """上下文降级策略"""
    
    def __init__(self, rag, summarizer, window_context):
        self.rag = rag
        self.summarizer = summarizer
        self.window = window_context
    
    async def handle_long_context(self, query: str, 
                                   full_document: str) -> str:
        """处理可能很长的上下文"""
        
        # 自动判断需要哪种方式
        doc_tokens = len(full_document) // 4
        
        if doc_tokens <= 2000:
            # 直接用
            return full_document
        
        elif doc_tokens <= 10000:
            # RAG 取相关片段
            retrieved = self.rag.retrieve(query, top_k=3)
            return self.rag.build_context(query, retrieved)
        
        elif doc_tokens <= 50000:
            # 分层摘要
            if not hasattr(self, '_doc_tree'):
                self._doc_tree = self.summarizer.build_hierarchy(full_document)
            return self.summarizer.retrieve_relevant(self._doc_tree, query)
        
        else:
            # 真正的长上下文，降级用户期望
            print(f"[警告] 文档长达 {doc_tokens} token，可能影响效果")
            print("[建议] 考虑分段落处理，或使用 RAG")
            
            # 实在要用，给出警告
            return "[长文档模式] " + full_document[:50000] + "\n[已截断]"
```

### 4.3 上下文监控

在可观测性系统中，加入上下文长度监控：

```python
class ContextMonitor:
    """上下文监控"""
    
    def __init__(self, metrics_collector):
        self.metrics = metrics_collector
    
    def record_context_size(self, request_id: str, token_count: int):
        """记录上下文长度"""
        
        self.metrics.record("context_tokens", token_count, {
            "request_id": request_id
        })
        
        # 告警
        if token_count > 50000:
            print(f"[警告] 请求 {request_id} 上下文长达 {token_count} token")
        
        if token_count > 100000:
            self.metrics.alert("context_too_long", {
                "request_id": request_id,
                "tokens": token_count
            })
```

---

## 五、总结：长上下文使用原则

```
原则1：尽量不要用长上下文
  ↓
  能用 RAG 就用 RAG，能压缩就压缩
  
原则2：非要用，优先选分层摘要
  ↓
  而不是直接把整个文档塞给模型
  
原则3：时刻监控成本
  ↓
  100k token = $0.20/请求，一万个请求就是 $2000
  
原则4：做好降级预案
  ↓
  当上下文超长时，自动切到备选方案
```

---

## 踩坑经验汇总

1. **不要被"百万 token"宣传迷惑**——99% 的场景不需要，用不好还有副作用
2. **RAG 比长上下文更靠谱**——只传相关内容，而不是整篇文档
3. **分层摘要要注意信息丢失**——压缩过的内容可能丢失关键细节
4. **滑动窗口 + 摘要组合最好用**——既保持上下文，又控制长度
5. **长上下文延迟很高**——100k 输入，首 token 可能要 3-5 秒，用户体验很差

---

**本篇代码**：https://github.com/dazhuang-zs/run_little_donkey/blob/master/docs/articles/ai-dev-advanced-04-context-engineering-deep.md

**篇⑤预告**：多模态 Agent 实战——视觉+动作的 Agent，讲 GPT-4o/Gemini 视觉理解、Tool Use with Vision、AI Agent 操作浏览器/桌面。