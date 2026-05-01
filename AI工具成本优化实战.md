# 自费上班时代，我是如何把AI工具成本砍掉60%的

---

去年Q3，我的团队月度AI API账单是2.8万美金。

那时候我们刚all in AI辅助开发，Copilot、ChatGPT、Claude轮着上，代码审查用AI、重构用AI、连写周报都用AI。效率确实上来了，但账单也上来了。

直到有一天，CFO把我叫进办公室，指着那条陡峭的曲线问我："这个东西，能不能便宜点？"

我回去认真算了一笔账，发现我们花的冤枉钱远比我想象的多。用了三个月时间做优化，把成本砍到了1.1万美金/月。效率没降，甚至因为某些优化，反而更快了。

这篇文章，把我的实战经验全部分享出来。

---

## 1. 为什么突然开始"精打细算"

先说个冷知识：大部分人用AI工具，根本不知道自己花了多少钱。

AI API的计费是按Token算的。Token是什么？可以简单理解为"文字的最小计费单位"。一个中文汉字大约等于1-2个Token，一段代码可能几十个Token，一次对话可能消耗几千到几万Token。

你以为的"一次对话"：问一个问题，收一个答案。

实际的计费：这个问题 + 所有历史对话 + 系统提示词 + 答案，每次请求都在重复付费。

我举个例子。我们团队有个客服AI系统，上线后日均处理1万轮对话。跑了两个月，突然发现Token消耗高达每天2亿。算一下：2亿Token/天，1亿Token只够撑5天。这还是接入的是相对便宜的模型。

更可怕的是上下文累积效应。第一轮对话可能只消耗500 Token，第十轮可能变成5000 Token，因为历史全都带进去了。到第一百轮的时候，你每次问一句话，后台实际上在处理一部中篇小说。

这就是AI成本失控的核心原因：**看不见的累积，看得见的账单。**

---

## 2. Token计费的几个坑，你踩过几个

### 坑一：上下文滚雪球

这是最大的隐形杀手。

AI对话不是孤立的一次请求。每次你发消息，模型都会把之前所有的对话历史一起传进去。这意味着：

- 第1轮：500 Token
- 第5轮：2500 Token（500 × 5）
- 第10轮：5000 Token（指数级增长）
- 第30轮：15000 Token+

你每多聊一轮，下一轮的成本就涨一截。这不是bug，是设计。但很多人用着用着就忘了，直到账单寄来才恍然大悟。

### 坑二：输入比输出贵，但输出也没便宜到哪去

AI模型对输入和输出分别计费，而且计费标准不同。

以GPT-4o为例：
- 输入：$2.5/1M Token
- 输出：$10/1M Token

输出是输入的4倍。但很多人只盯着输出看，觉得少说几句就行了。实际上输入端的浪费更严重——System Prompt几千Token，每次请求都重复计算，你以为那是"固定配置"，其实是"固定成本"。

### 坑三：PDF、文档直接扔给AI，白扔钱

我见过最夸张的案例：一个技术文档分析任务，产品经理把一份50页的PDF直接发给ChatGPT。PDF本身的页眉、页脚、水印、隐藏字符、表格样式代码，全都被算进Token。这份PDF实际内容可能只有30KB，但发给AI的时候变成了几百KB的Token消耗。

后来我们做了个实验：把这50页PDF提取纯文本，删掉格式代码和无关内容，压缩到20KB。再发给同一个AI任务，结果：
- 费用节省了97%
- 回答质量没有任何下降

那些页眉页脚、字体颜色、PDF元数据，对AI理解内容毫无帮助，但AI会全部吞进去计费。

### 坑四：Agent的Token消耗是对话的4倍

如果你在用AI Agent（自主规划+执行的那种），成本会再翻几倍。

因为Agent不只是一问一答。它会：
1. 思考下一步该做什么
2. 调用工具
3. 读取文件
4. 再思考
5. 再调用
6. 汇总结果

每一步都在消耗Token。企业级Agent的Token消耗通常是普通对话的4倍以上。

---

## 3. 8个立竿见影的省钱技巧

下面直接上干货，每个技巧都经过实战验证。

### 技巧1：清理"烂菜叶"，提升输入纯度

**核心原则：只喂AI它真正需要的东西。**

文档处理流程：
1. PDF → 提取纯文本（用PyMuPDF、pdfplumber等工具）
2. 删除页眉页脚、水印、隐藏字符
3. 删除重复出现的固定文本（如"机密文件-禁止外传"这类每页都有的）
4. 删除格式代码（HTML标签、LaTeX源码等）
5. 压缩到最小必要体积

一个10MB的PDF，处理后可能变成10KB的干净文本。省99%的费用就是这么来的。

代码文件也一样。如果你让AI分析一个项目，不要直接扔整个仓库。先搞清楚你要解决的具体问题，再告诉AI"去看src/services/user.ts的第23-45行"。精准定位节省的不仅是Token，还有AI的注意力。

### 技巧2：控制多媒体输入大小

图片要压缩。如果你的工作流涉及OCR或者图片理解，先把图片resize到合理尺寸。1080p够用了，不需要4K原图。

语音输入同理。转文字前可以先做降采样，核心信息不受影响。

### 技巧3：适时新开对话

这是最简单但最容易被忽视的技巧。

对话历史是隐形成本。每个新话题、新任务，强烈建议开一个新对话窗口。你以为你在"继续思考"，实际上你在不断付"历史累积费"。

我的习惯是：
- 每个独立任务 = 一个新对话
- 复杂任务拆成多个小步骤，每步一个新对话
- 对话超过20轮就新建，不管问题有没有解决完

有些人担心"换对话会不会丢失上下文"。会的。但你要问自己：这个上下文真的值得每个月多花几千美金吗？大部分情况下不值得。

### 技巧4：Prompt压缩——LLMLingua

这是微软亚洲研究院出的一个工具，可以把长Prompt压缩到原来的5%，同时保持95%以上的性能。

原理是：识别Prompt中的关键信息（主要是问题本身和约束条件），删掉冗余的解释和填充词。

```python
# LLMLingua集成示例（LlamaIndex）
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.postprocessorLLMLingua import LLMLinguaPostprocessor

# 原始10000 token的Prompt，压缩后可能只剩500 token
processor = LLMLinguaPostprocessor(
    model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
    device="cpu"
)

# 在你的RAG pipeline里加入这个后处理步骤
query_engine = RetrieverQueryEngine.from_args(
    retriever=retriever,
    postprocessor=[processor]
)
```

这个工具特别适合RAG（检索增强生成）场景。你的知识库检索可能返回一堆相关段落，加起来几千Token，用LLMLingua压缩一下，既省钱又不损失关键信息。

### 技巧5：语义缓存——减少重复调用

这个技巧的威力最大，但也需要一点工程投入。

核心思路：不是所有问题都需要调用LLM。语义上高度相似的问题，可以直接返回缓存结果。

**适用场景：**
- FAQ类问答
- 重复性的代码审查意见
- 标准化的技术解释
- 经常被问到的问题

**不适用的场景：**
- 每次输入都不同的开放式问题
- 需要实时数据的查询
- 高度个性化的任务

语义缓存的技术实现需要两个组件：
1. **向量数据库**：存储问题的语义向量
2. **相似度匹配**：新问题过来时，找到最接近的已缓存问题

```python
import redis
import numpy as np

class SemanticCache:
    """语义缓存：用向量相似度匹配，避免重复调用LLM"""

    def __init__(self, redis_url: str, threshold: float = 0.85):
        self.redis = redis.from_url(redis_url)
        self.threshold = threshold  # 相似度阈值，越高越严格

    def get(self, query: str, embed_func) -> str | None:
        """查询缓存，命中则返回缓存的响应"""
        query_vec = embed_func(query)
        # 用向量做相似度搜索
        results = self.redis.ft("sem_idx").search(
            query_vec.tolist(),
            {"LIMIT": 1, "WITHSCORES": True}
        )
        if results and results[0].score >= self.threshold:
            cached = self.redis.hgetall(results[0].id)
            return cached.get("response")
        return None

    def set(self, query: str, response: str, embed_func):
        """写入缓存"""
        cache_key = f"cache:{hash(query)}"
        query_vec = embed_func(query)
        self.redis.hset(cache_key, mapping={
            "query": query,
            "response": response,
            "embedding": np.array(query_vec).tobytes(),
            "timestamp": str(int(time.time()))
        })
        # 设置TTL，自动过期
        self.redis.expire(cache_key, 86400 * 7)  # 7天过期
```

实际效果：一个客服系统，日均1万轮对话，合理配置语义缓存后，API调用量减少了40-50%，响应延迟降低了60-80%。

### 技巧6：多模型路由——让对的AI干对的活

不是所有任务都需要GPT-4o或者Claude Opus。

简单任务用小模型：
- 检查语法错误
- 解释一段代码在做什么
- 翻译简短文本
- 格式化输出

这些任务用GPT-4o-mini或者Claude Haiku就够了，速度快4倍，价格便宜10倍，但效果几乎一样。

高难度任务才上最强模型：
- 复杂架构设计
- 多模块重构
- 需要深度推理的问题

```python
def route_task(task: str, complexity: str = None) -> str:
    """智能路由：按任务复杂度选择最合适的模型"""
    simple_keywords = [
        "检查语法", "解释函数", "翻译", "格式化",
        "拼写检查", "简单计算", "查找bug"
    ]
    medium_keywords = [
        "重构代码", "写单元测试", "优化性能", "审查代码",
        "生成文档", "解释算法"
    ]

    if complexity == "simple" or any(k in task for k in simple_keywords):
        return "gpt-4o-mini"  # 便宜10倍，速度快4倍
    elif complexity == "medium" or any(k in task for k in medium_keywords):
        return "gpt-4o"  # 中等难度的主力模型
    else:
        return "claude-opus-4-7-20250611"  # 高难度任务才上最强模型
```

也可以更进一步：根据输入长度动态选择。如果用户只发了3句话，派小模型；如果用户扔了一个文件，派大模型。

### 技巧7：用量预警和月度上限

这个是财务保障，不是技术优化，但很重要。

设置用量上限的几种方式：

1. **平台级上限**：大部分AI API服务商都支持设置月度或每日用量上限
2. **应用级监控**：自己写一个Token计数器，每次API调用时累加，接近阈值时报警或熔断
3. **日志分析**：每周分析一次Token消耗分布，找出异常高的用户或场景

我建议每个团队都跑一周的Token计数，不用做任何优化，光是"看见数据"就能发现很多浪费。

```python
import tiktoken
from datetime import datetime, timedelta
from collections import defaultdict

class TokenMonitor:
    """Token消耗监控：谁在烧钱，一目了然"""

    def __init__(self, model: str = "gpt-4o"):
        self.encoding = tiktoken.encoding_for_model(model)
        self.daily_usage = defaultdict(int)
        self.monthly_limit = 10_000_000  # 月度上限：1000万Token

    def count(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def log(self, user_id: str, messages: list[dict]):
        """记录一次请求的Token消耗"""
        total = sum(self.count(msg.get("content", ""))
                   for msg in messages)
        today = datetime.now().strftime("%Y-%m-%d")
        self.daily_usage[f"{user_id}:{today}"] += total

    def check_limit(self, user_id: str) -> bool:
        """检查是否接近月度上限"""
        total = sum(v for k, v in self.daily_usage.items()
                   if k.startswith(user_id))
        return total < self.monthly_limit

    def report(self):
        """生成消耗报告"""
        total = sum(self.daily_usage.values())
        cost = total * 0.000015  # 粗略估算美元成本
        return {
            "total_tokens": total,
            "estimated_cost_usd": round(cost, 2),
            "limit": self.monthly_limit,
            "usage_rate": round(total / self.monthly_limit * 100, 2)
        }
```

### 技巧8：精准定位——减少上下文噪音

这个技巧免费，但很多人做不到。

错误示范：
> "帮我看看我的项目有什么问题"

正确示范：
> "我的用户认证模块在注册时偶尔会报500错误，错误日志是[具体日志]，用户表结构是[结构]，请看src/auth/register.ts这个文件，重点关注第45-67行的密码校验逻辑。"

AI不是神，它也需要上下文。给得太多，它会在噪音里迷失；给得太少，它会瞎猜。精准定位是性价比最高的投入。

还有一个技巧：告诉AI"不要做什么"有时候比告诉它"做什么"更重要。
> "请只分析性能问题，不要审查代码风格，不要检查安全漏洞。"

---

## 4. 一个真实项目的优化全过程

说完了技巧，来看一个真实案例。

**项目背景：** 内部代码审查AI助手，服务60人的开发团队，日均审查请求约300次。

**优化前数据：**
- 月度Token消耗：1.2亿
- 月度API费用：约$1800
- 平均响应延迟：8秒
- 团队满意度：中等（"有时候太慢了"）

### 第一步：跑Token计数，找出消耗分布

```python
import tiktoken
from collections import Counter

def audit_token_consumption(messages_log: list[dict]) -> dict:
    """审计一次对话的Token消耗分布"""
    encoding = tiktoken.encoding_for_model("gpt-4o")

    breakdown = {
        "system_prompt": 0,
        "user_input": 0,
        "history": 0,
        "output": 0
    }

    # 假设 messages_log 按时间顺序排列
    # 第一条是system prompt
    if messages_log and messages_log[0].get("role") == "system":
        breakdown["system_prompt"] = len(encoding.encode(
            messages_log[0].get("content", "")))

    # 最后一条是output
    if messages_log[-1].get("role") == "assistant":
        breakdown["output"] = len(encoding.encode(
            messages_log[-1].get("content", "")))

    # 中间是用户输入和历史
    for msg in messages_log[1:-1]:
        tokens = len(encoding.encode(msg.get("content", "")))
        if msg.get("role") == "user":
            breakdown["user_input"] += tokens
        else:
            breakdown["history"] += tokens

    return breakdown
```

跑了一周，发现问题：
- 每次请求的平均System Prompt是3500 Token（固定成本，每次都付）
- 对话历史平均累积到8000 Token（15轮对话后）
- 用户实际输入只有500 Token

**结论：75%的费用花在了上下文上，实际用户需求只占25%。**

### 第二步：逐项优化

**优化1：压缩System Prompt**

原来System Prompt写了800字的企业定制说明。压缩后：

```python
# 优化前：800字，详细但冗余
system_prompt_old = """
你是一个代码审查助手，为XX公司服务。
公司技术栈：Python/Go，前端React。
审查标准：代码风格、安全性、性能、可维护性...
你的名字是CodeReviewer，你的职责是...
"""

# 优化后：200字，精简核心
system_prompt_new = """
角色：代码审查助手
栈：Python/Go, React
维度：安全、性能、可维护性
输出：发现+建议+严重程度
"""
```

**节省：2600 Token/请求（约43%固定成本）**

**优化2：强制截断对话历史**

```python
MAX_HISTORY_TOKENS = 3000

def trim_history(messages: list[dict], max_tokens: int = MAX_HISTORY_TOKENS) -> list[dict]:
    """只保留最近N个Token的历史，超出则截断"""
    encoding = tiktoken.encoding_for_model("gpt-4o")

    # 从最新往最旧数，累计Token数
    result = []
    total = 0

    # 保留system prompt
    if messages and messages[0].get("role") == "system":
        result.append(messages[0])
        total = len(encoding.encode(messages[0].get("content", "")))

    # 从最后往前加，直到达到上限
    for msg in reversed(messages[1:]):
        msg_tokens = len(encoding.encode(msg.get("content", "")))
        if total + msg_tokens <= max_tokens:
            result.insert(1, msg)
            total += msg_tokens
        else:
            break  # 达到上限，后面的全扔掉

    return result
```

**节省：历史累积从8000 Token降到3000 Token**

**优化3：接入语义缓存**

常见问题建立缓存：

```python
CACHED_RESPONSES = {
    "如何运行测试": "执行 `pytest tests/` 即可运行所有测试。",
    "如何部署": "执行 `make deploy` 部署到staging，`make deploy-prod` 部署到生产。",
    "代码规范文档在哪": "见 docs/code-style.md",
    "如何新建分支": "`git checkout -b feature/你的分支名`",
}

def get_cached_response(query: str) -> str | None:
    """快速缓存查询：针对常见问题"""
    query_lower = query.lower()
    for key, response in CACHED_RESPONSES.items():
        if key in query_lower or similar(query_lower, key) > 0.8:
            return response
    return None
```

**节省：约30%的请求直接命中缓存，不走API**

**优化4：多模型路由**

```python
from collections import Counter

COMPLEXITY_PATTERNS = {
    "critical": [  # 高危问题，强审查
        r"登录|认证|权限",
        r"支付|订单|金额",
        r"用户数据|隐私",
    ],
    "medium": [  # 中等复杂度
        r"重构|重写",
        r"新增接口|新增模块",
        r"性能问题",
    ],
    "simple": [  # 简单问题，轻量审查
        r"修复bug|fix",
        r"注释|docstring",
        r"变量重命名",
    ],
}

def estimate_complexity(diff_content: str) -> str:
    """根据代码变更内容评估复杂度"""
    import re
    content_lower = diff_content.lower()

    for level, patterns in COMPLEXITY_PATTERNS.items():
        if any(re.search(p, content_lower) for p in patterns):
            return level
    return "medium"  # 默认中等

def select_model(complexity: str) -> str:
    """根据复杂度选择模型"""
    return {
        "critical": "gpt-4o",      # 高危必须仔细审
        "medium": "gpt-4o-mini",   # 中等用小模型
        "simple": "gpt-4o-mini",   # 简单更不在话下
    }.get(complexity, "gpt-4o-mini")
```

### 优化结果

| 指标 | 优化前 | 优化后 | 变化 |
|------|--------|--------|------|
| 月度Token | 1.2亿 | 4200万 | -65% |
| 月度费用 | $1800 | $630 | -65% |
| 平均延迟 | 8秒 | 3.2秒 | -60% |
| 审查通过率 | 78% | 82% | +4% |

成本降了，延迟降了，审查质量反而提高了——因为AI不再被冗长的上下文干扰，注意力更集中。

---

## 5. 总结：省钱不是目的，高效才是

写到这里，我想说几句真心话。

我不反对为AI付费。AI确实提升了我们的开发效率，这一点无可否认。但"为AI付费"和"乱烧钱"是两回事。

我见过太多团队，AI用得很嗨，账单出来了才傻眼。然后要么砍需求，要么砍AI。两败俱伤。

真正健康的姿势是：**花该花的钱，省该省的钱。**

哪些钱该花：
- 核心业务场景的深度推理
- 需要最强模型才能解决的高难度问题
- 真正创造价值的AI应用

哪些钱该省：
- 重复问答（缓存它）
- 无脑上传大文件（清理它）
- 什么都用最强模型（路由它）
- 对话历史无限累积（截断它）

这8个技巧，没有一个是"牺牲效率换省钱"。它们的本质是：**减少噪音，让AI把算力用在真正重要的地方。**

最后送你一句话，与所有在AI时代自费的开发者共勉：

> 不要为AI付冤枉钱。把省下来的预算，用在真正重要的地方。

---

**附：快速检查清单**

每次提交AI任务前，花30秒过一遍：

- [ ] 我的输入是否干净？有没有多余的水印、页眉、格式代码？
- [ ] 这个问题是否需要调用LLM？还是可以用缓存？
- [ ] 用的是合适的模型吗？语法检查不需要GPT-4o
- [ ] 对话历史是不是太长了？超过20轮建议新建
- [ ] 我的System Prompt有没有冗余信息？
- [ ] 有没有告诉AI"不要做什么"？

30秒，省下的可能是几十美金。

---

*本文涉及的价格数据基于2024年主流API定价，实际费用请以各平台最新账单为准。*
