# AI 开发进阶（第3篇）：大模型推理加速与成本控制——从 API 到自部署的全链路优化

> 适合读者：已读完基础9篇 + 第①②篇，想让 Agent 更快、更便宜
> 预计阅读时间：40分钟
> 作者：AI小渔村

---

## 前言：成本是 Agent 落地的生死线

前两篇我们讨论了评估体系和可观测性。但即使你知道了 Agent 好不好、能不能跑，**成本」仍然是一个致命问题：

- 一个复杂的 Agent 请求，可能消耗 $0.5 - $2.0
- 日活 1 万用户，每月成本轻松超过 $15,000
- 老板问："能不能再便宜点？"

这篇讲的是：**如何让 Agent 更快、更便宜**，覆盖从 API 调优到自部署的全链路优化。

---

## 一、成本到底花在哪了？

### 1.1 成本的三个组成部分

```
总成本 = Token 成本 + 推理延迟成本 + 基础设施成本

Token 成本 = (输入 Token 数 × 输入单价) + (输出 Token 数 × 输出单价)
推理延迟成本 = 等待时间 × 服务器/算力成本
基础设施成本 = 服务器、存储、网络等固定开销
```

以 GPT-4o 为例（2026年5月价格）：

| 模型 | 输入（缓存未命中） | 输出 |
|------|------------------|------|
| GPT-4o | $2.50 / 1M | $10.00 / 1M |
| GPT-4o-mini | $0.15 / 1M | $0.60 / 1M |

**优化方向**：
- 减少 Token 消耗（输入压缩、输出精简）
- 减少调用次数（结果复用、缓存）
- 模型路由（简单任务用小模型）

---

## 二、输入优化：减少 Token 消耗

### 2.1 上下文压缩

长对话的痛点：历史消息占了一大半 token，但模型真正需要的是最近的信息。

**解法：摘要压缩**

```python
from dataclasses import dataclass
from typing import List, Dict
import json

@dataclass
class Message:
    role: str
    content: str
    timestamp: str = ""

class ContextCompressor:
    """上下文压缩器"""
    
    def __init__(self, llm, max_tokens: int = 6000, keep_recent: int = 5):
        self.llm = llm
        self.max_tokens = max_tokens
        self.keep_recent = keep_recent
    
    def compress(self, messages: List[Message]) -> List[Message]:
        """压缩对话历史"""
        
        # 保留最近 N 条消息（完整保留）
        recent = messages[-self.keep_recent:]
        
        # 更早的消息需要压缩
        older = messages[:-self.keep_recent]
        
        if not older:
            return recent
        
        # 估算当前 token 数
        current_tokens = sum(self.estimate_tokens(m.content) for m in recent)
        
        if current_tokens >= self.max_tokens:
            # 最近的消息也已经太长，直接截断
            return self._truncate(recent, self.max_tokens)
        
        # 对更早的消息做摘要
        available_tokens = self.max_tokens - current_tokens
        summary = await self._summarize(older, available_tokens)
        
        return [Message(
            role="system",
            content=f"[对话历史摘要] {summary}"
        )] + recent
    
    async def _summarize(self, messages: List[Message], max_tokens: int) -> str:
        """用 LLM 生成摘要"""
        
        conversation_text = "\n".join([
            f"{m.role}: {m.content[:200]}"  # 每条取前200字符
            for m in messages
        ])
        
        prompt = f"""请用 100 字以内概括以下对话的核心内容：

{conversation_text}

摘要："""
        
        response = await self.llm.chat([
            {"role": "user", "content": prompt}
        ])
        
        return response.content
    
    def estimate_tokens(self, text: str) -> int:
        """估算 token 数（简单实现）"""
        return len(text) // 4  # 约等于
    
    def _truncate(self, messages: List[Message], max_tokens: int) -> List[Message]:
        """截断消息"""
        truncated = []
        total_tokens = 0
        
        for m in reversed(messages):
            tokens = self.estimate_tokens(m.content)
            if total_tokens + tokens > max_tokens:
                break
            truncated.insert(0, m)
            total_tokens += tokens
        
        return truncated
```

### 2.2 System Prompt 精简

System Prompt 往往很长，但很多是车轱辘话。

**解法：提取核心指令，用 Few-shot 示例替代冗长说明**

```python
# 优化前（800+ tokens）
SYSTEM_PROMPT_LONG = """你是一个专业的客服助手。

你的职责是帮助用户解决问题。
你必须遵循以下原则：
1. 始终保持礼貌
2. 仔细阅读用户的问题
3. 提供准确、完整的答案
4. 如果不确定，请明确告知用户
5. 不要编造信息
...

[此处省略 500 字]"""

# 优化后（200 tokens）
SYSTEM_PROMPT_SHORT = """[角色] 专业客服，简洁准确地回答用户问题。
[原则] 不知道就说不知道，不要编造。
[格式] 优先用列表，控制在 3 点以内。"""
```

### 2.3 用户输入预处理

用户输入可能包含：
- 重复信息
- 无关背景
- 格式混乱

**解法：输入预处理**

```python
class InputPreprocessor:
    """用户输入预处理器"""
    
    def process(self, user_input: str) -> str:
        # 1. 去除重复空格、换行
        text = re.sub(r'\s+', ' ', user_input)
        
        # 2. 去除明显的车轱辘话
        text = self._remove_redundancy(text)
        
        # 3. 提取核心问题（简单实现）
        text = self._extract_core(text)
        
        return text.strip()
    
    def _remove_redundancy(self, text: str) -> str:
        """去除冗余表达"""
        patterns = [
            r'我之前已经说过.*?。',
            r'麻烦.*?一下',  # 麻烦看一下、麻烦处理一下
            r'谢谢.*?谢谢',  # 重复感谢
        ]
        for p in patterns:
            text = re.sub(p, '', text)
        return text
    
    def _extract_core(self, text: str) -> str:
        """提取核心问题"""
        # 简单实现：取第一段作为核心
        sentences = text.split('。')
        if len(sentences) > 3:
            # 如果超过 3 句，只保留前 2 句
            return '。'.join(sentences[:2]) + '。'
        return text
```

---

## 三、输出优化：减少无效 Token

### 3.1 输出长度限制

```python
class OutputLimiter:
    """输出长度限制器"""
    
    def __init__(self, max_output_tokens: int = 500):
        self.max_output_tokens = max_output_tokens
    
    def wrap_prompt(self, original_prompt: str) -> str:
        """在 prompt 中限制输出长度"""
        return f"""{original_prompt}

[重要] 请将回答控制在 {self.max_output_tokens} Token 以内。
- 优先给出核心答案
- 如需详细说明，另起一段
- 不要重复问题或解释你是 AI"""
```

### 3.2 结构化输出

让模型直接输出 JSON/结构化内容，减少解释性文字。

```python
from pydantic import BaseModel
from typing import Optional

class WeatherResponse(BaseModel):
    city: str
    date: str
    weather: str
    temperature: str
    suggestion: Optional[str] = None

# 在 prompt 中指定格式
PROMPT_WITH_FORMAT = """查询天气后，请按以下 JSON 格式输出：

```json
{{
  "city": "城市名",
  "date": "日期",
  "weather": "天气状况",
  "temperature": "温度范围",
  "suggestion": "出行建议（可选）"
}}
```"""

# 使用 LangChain 的 Pydantic 输出解析器
from langchain.output_parsers import PydanticOutputParser

parser = PydanticOutputParser(pydantic_object=WeatherResponse)

chain = prompt | llm | parser
result = chain.invoke({"query": "北京明天天气"})
# result 类型是 WeatherResponse，直接可用
```

---

## 四、模型路由：让合适的任务用合适的模型

### 4.1 什么时候用小模型？

| 场景 | 推荐模型 | 理由 |
|------|---------|------|
| 简单问答 | GPT-4o-mini | 成本只有 4o 的 6% |
| 意图分类 | GPT-4o-mini | 不需要推理能力 |
| 信息提取 | GPT-4o-mini | 结构化提取很简单 |
| 复杂推理 | GPT-4o | 需要强推理能力 |
| 创意写作 | GPT-4o | 需要更好的表达能力 |
| 代码生成 | GPT-4o | 逻辑复杂，容易出错 |

### 4.2 路由实现

```python
from enum import Enum
from typing import Optional
import asyncio

class ModelType(Enum):
    FAST = "gpt-4o-mini"      # 快速、便宜
    BALANCED = "gpt-4o"        # 平衡
    POWER = "gpt-4o-2024-05"   # 强力

class ModelRouter:
    """模型路由器"""
    
    def __init__(self, llm_factory):
        self.llm_factory = llm_factory
        self.router_prompt = """请根据任务复杂度选择合适的模型：
- 简单任务（问答、分类、提取）：选择 "fast"
- 中等任务（需要一定推理）：选择 "balanced"
- 复杂任务（深度推理、创意、代码）：选择 "power"

只返回一个词：fast / balanced / power

任务：{task}"""
    
    async def route(self, task: str) -> ModelType:
        """路由任务到合适的模型"""
        
        # 判断任务复杂度
        response = await self.llm_factory.create().achat([
            {"role": "user", "content": self.router_prompt.format(task=task)}
        ])
        
        choice = response.content.strip().lower()
        
        if "fast" in choice:
            return ModelType.FAST
        elif "power" in choice:
            return ModelType.POWER
        else:
            return ModelType.BALANCED
    
    async def route_batch(self, tasks: list[str]) -> list[ModelType]:
        """批量路由"""
        return await asyncio.gather(*[self.route(t) for t in tasks])
    
    def get_llm(self, model_type: ModelType):
        """获取对应模型"""
        return self.llm_factory.create(model_type.value)


# 使用示例
async def handle_request(task: str):
    router = ModelRouter(llm_factory)
    
    # 自动路由
    model_type = await router.route(task)
    llm = router.get_llm(model_type)
    
    # 根据模型不同，成本也不同
    cost_map = {
        ModelType.FAST: 0.001,
        ModelType.BALANCED: 0.01,
        ModelType.POWER: 0.03
    }
    
    print(f"使用模型: {model_type.value}, 预估成本: ${cost_map[model_type]}")
    
    return await llm.achat([{"role": "user", "content": task}])
```

### 4.3 路由效果

| 任务类型 | 路由前 | 路由后 | 成本降低 |
|---------|--------|--------|---------|
| 简单问答 | $0.01 | $0.0006 | **94%** |
| 意图分类 | $0.01 | $0.0006 | **94%** |
| 复杂推理 | $0.01 | $0.01 | 0% |
| **平均** | $0.01 | $0.003 | **70%** |

---

## 五、自部署：终极成本优化

### 5.1 什么时候需要自部署？

- 日均 API 调用量 > 100,000 次
- 对数据安全有严格要求（不能发送给第三方）
- 需要深度定制（微调、特殊优化）
- 有自己的 GPU 资源

### 5.2 自部署架构

```
┌─────────────────────────────────────────────┐
│                 用户请求                      │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│                 负载均衡                       │
│                   (Nginx)                    │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│              API Gateway                      │
│              (FastAPI)                       │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│            vLLM 推理集群                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ GPU 1   │  │ GPU 2   │  │ GPU 3   │   │
│  │(A100 80G)│  │(A100 80G)│  │(A100 80G)│   │
│  └─────────┘  └─────────┘  └─────────┘   │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│              模型权重                         │
│         (Qwen3-32B / LLaMA3-70B)          │
└─────────────────────────────────────────────┘
```

### 5.3 vLLM 部署实战

```bash
# 1. 安装 vLLM
pip install vllm

# 2. 启动 vLLM 服务
vllm serve Qwen/Qwen2.5-32B-Instruct \
    --dtype half \              # 使用半精度
    --gpu-memory-utilization 0.95 \  # GPU 显存利用率
    --max-model-len 8192 \     # 最大上下文长度
    --tensor-parallel-size 2   # 张量并行（2 卡）
    --port 8000

# 3. 测试
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-32B-Instruct",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 100
  }'
```

### 5.4 量化：进一步降低成本

| 量化方法 | 精度损失 | 显存减少 | 推荐场景 |
|---------|---------|---------|---------|
| FP16 | 几乎无 | 50% | 首选 |
| INT8 | 2-3% | 75% | 显存不足时 |
| INT4 | 5-10% | 87% | 极致压缩 |

```bash
# INT8 量化部署
vllm serve Qwen/Qwen2.5-32B-Instruct \
    --dtype int8 \
    --quantization_method awq \
    --max-model-len 8192
```

### 5.5 自部署成本对比

| 方案 | 月成本 | 单次请求成本 |
|-----|-------|------------|
| GPT-4o API | $15,000 | $0.01 |
| GPT-4o-mini API | $2,000 | $0.001 |
| **自部署 Qwen3-32B** | **$3,000** | **$0.0005** |
| 自部署 LLaMA3-70B | $5,000 | $0.001 |

**结论**：日均请求量超过 100k 时，自部署开始划算。

---

## 六、缓存：让重复请求不花钱

### 6.1 什么可以缓存？

- 相同问题的回答
- 相同文档的摘要
- 相同搜索的结果
- 相同工具的返回值

### 6.2 缓存实现

```python
import hashlib
import json
from typing import Optional
import redis

class ResponseCache:
    """响应缓存"""
    
    def __init__(self, redis_client: redis.Redis, ttl_seconds: int = 3600):
        self.redis = redis_client
        self.ttl = ttl_seconds
    
    def _make_key(self, prompt: str, model: str) -> str:
        """生成缓存 key"""
        content = f"{model}:{prompt}"
        return f"cache:{hashlib.sha256(content.encode()).hexdigest()}"
    
    def get(self, prompt: str, model: str) -> Optional[str]:
        """获取缓存"""
        key = self._make_key(prompt, model)
        cached = self.redis.get(key)
        return cached.decode() if cached else None
    
    def set(self, prompt: str, model: str, response: str):
        """设置缓存"""
        key = self._make_key(prompt, model)
        self.redis.setex(key, self.ttl, response)


# 使用示例
async def chat_with_cache(llm, cache: ResponseCache, prompt: str):
    # 先查缓存
    cached = cache.get(prompt, llm.model_name)
    if cached:
        print("[CACHE HIT]")
        return cached
    
    # 没有缓存，调用 LLM
    response = await llm.chat(prompt)
    
    # 存入缓存
    cache.set(prompt, llm.model_name, response)
    
    return response
```

### 6.3 缓存命中率

| 场景 | 缓存命中率 | 成本降低 |
|------|-----------|---------|
| FAQ 客服 | 60-80% | 60-80% |
| 文档问答 | 30-50% | 30-50% |
| 开放对话 | 5-10% | 5-10% |

---

## 七、总结：成本优化路线图

```
阶段1：输入优化（现在）
  ↓   上下文压缩、Prompt 精简、输入预处理
阶段2：输出优化（下周）
  ↓   长度限制、结构化输出
阶段3：模型路由（下个月）
  ↓   简单任务用小模型，复杂任务用大模型
阶段4：自部署（3个月后）
  ↓   vLLM + 量化，高频场景自部署
阶段5：智能缓存（半年后）
  → 基于语义相似度的缓存
```

**核心思想**：成本优化是一个系统工程，从输入、输出、模型、部署、缓存五个层面同时发力。

---

## 踩坑经验汇总

1. **上下文压缩要谨慎**——不要压缩掉关键信息，尤其是 Agent 需要知道的历史决策
2. **模型路由不是 100% 准确**——路由模型也可能选错，准备兜底方案
3. **自部署的 GPU 成本不容忽视**——显卡折旧、电费、运维都是钱
4. **缓存不是万能的**——需要考虑缓存失效、更新一致性
5. **量化有精度损失**——INT4 在某些任务上效果明显下降，先测试再上线

---

**本篇代码**：https://github.com/dazhuang-zs/run_little_donkey/blob/master/docs/articles/ai-dev-advanced-03-inference-cost-optimization.md

**篇④预告**：Context Engineering 深入——长上下文的真相，讲百万 token 上下文的坑、压缩策略、什么时候真需要长上下文。