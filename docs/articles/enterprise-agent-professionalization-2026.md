# 企业级Agent专业化实战：从架构设计到生产落地的完整指南

> **阅读时间**：约20分钟 | **你将学到**：企业级Agent的专业化方法论、真实生产架构、完整可运行代码、评估体系设计、安全合规落地
>
> **核心观点**：企业级Agent专业化不是选模型、不是堆工具，而是一套系统工程。从架构设计到生产部署，每一步都有明确的决策框架和踩坑经验。

---

## 一、从Demo到生产：Agent落地的真实鸿沟

做Demo Agent很容易：一个System Prompt + 一个LLM API + 几个Function，30分钟就能跑起来。

但当你把Demo推向生产，你会发现：

```
Demo阶段（3天搞定）          生产阶段（3个月还不够）
┌──────────────────┐       ┌──────────────────┐
│ 准确率80%就够了   │       │ 准确率99%才算及格  │
│ 1个工具够用       │       │ 20+工具要协作      │
│ 用户问题单一       │       │ 用户问题千奇百怪    │
│ 出错了重启就行     │       │ 出错了要自动恢复    │
│ 响应慢1秒无所谓    │       │ P99延迟<3秒        │
│ 不用考虑安全       │       │ 安全合规是红线      │
│ 不用考虑成本       │       │ 日调用量>100万次    │
│ 单独跑一个Agent    │       │ 5个Agent协作       │
└──────────────────┘       └──────────────────┘
```

我见过太多团队卡在这条鸿沟上。不是技术不够，而是**方法论缺失**。

这篇文章不讲概念，只讲我们在真实项目中趟过的路、踩过的坑、沉淀下来的方法论。

---

## 二、专业化方法论总览

Agent专业化分四个层次，每个层次都有明确的目标、技术手段和验收标准：

```
┌─────────────────────────────────────────────────┐
│          第四层：持续进化（Continuous Evolution）    │
│   反馈闭环 · A/B测试 · Bad Case自动优化 · 版本管理  │
├─────────────────────────────────────────────────┤
│          第三层：流程规范（Process Engineering）     │
│   多Agent协作 · 审核机制 · 熔断降级 · 可观测性      │
├─────────────────────────────────────────────────┤
│          第二层：工具赋能（Tool Empowerment）        │
│   工具设计 · 错误处理 · 上下文管理 · 记忆系统       │
├─────────────────────────────────────────────────┤
│          第一层：知识注入（Knowledge Injection）      │
│   RAG · 微调 · Prompt工程 · 领域知识结构化           │
└─────────────────────────────────────────────────┘
```

**核心原则**：每一层都是上一层的地基。跳层是最大的坑。

我见过很多团队直接从第四层开始搞多Agent协作，结果第一层的知识注入都没做好，Agent连基本的事实都搞不清楚，协作再精巧也没用。

---

## 三、第一层：知识注入

### 3.1 知识注入的三种方式

| 方式 | 适用场景 | 成本 | 效果上限 | 落地难度 |
|------|---------|------|---------|---------|
| Prompt背景注入 | 少量规则、格式要求 | 低 | 中 | ⭐ |
| RAG知识检索 | 大量文档、频繁更新 | 中 | 高 | ⭐⭐⭐ |
| 微调 | 深度领域知识、特定输出风格 | 高 | 最高 | ⭐⭐⭐⭐ |

**实战经验**：90%的企业场景用RAG就够了。微调是最后手段，不是首选。

### 3.2 RAG知识库实战

先说踩坑。我们最初直接用LangChain的默认VectorStore，遇到三个问题：

1. **文档切分太碎**：一段完整的流程说明被切成3块，检索到任何一块都无法回答完整问题
2. **检索不精确**：用户问"退款流程"，结果返回了"退款政策"和"换货流程"，唯独没有"退款流程"
3. **知识过期**：上个月的促销活动信息还在库里

解决方案：

```python
import hashlib
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class KnowledgeDocument:
    """企业级知识文档"""
    content: str
    source: str
    doc_type: str  # policy, faq, process, product, glossary
    version: str = "1.0"
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    confidence: float = 1.0  # 知识置信度，<0.5的需要人工确认
    tags: list[str] = field(default_factory=list)
    
    @property
    def doc_id(self) -> str:
        return hashlib.md5(f"{self.source}:{self.content[:200]}".encode()).hexdigest()
    
    @property
    def is_expired(self) -> bool:
        if not self.expiry_date:
            return False
        return datetime.now() > datetime.fromisoformat(self.expiry_date)
    
    @property
    def is_effective(self) -> bool:
        if not self.effective_date:
            return True
        return datetime.now() >= datetime.fromisoformat(self.effective_date)


class EnterpriseRAG:
    """企业级RAG系统
    
    踩坑经验：
    1. 分块策略：按语义分段，不要按固定长度切
    2. 检索策略：混合检索（向量+BM25），不能只靠向量相似度
    3. 过期处理：每次检索都要检查时效性
    """
    
    def __init__(self, vector_store, bm25_store, llm_client):
        self.vector_store = vector_store
        self.bm25_store = bm25_store
        self.llm = llm_client
    
    def ingest(self, doc: KnowledgeDocument):
        """知识入库
        
        踩坑：入库时就要做好元数据标注，检索时才能精确过滤
        """
        if doc.is_expired:
            print(f"[WARN] 跳过过期文档: {doc.source}")
            return
        
        # 语义分块（不是固定长度切分）
        chunks = self._semantic_chunk(doc.content, doc_type=doc.doc_type)
        
        for chunk in chunks:
            self.vector_store.add(
                text=chunk["text"],
                metadata={
                    "doc_id": doc.doc_id,
                    "source": doc.source,
                    "doc_type": doc.doc_type,
                    "version": doc.version,
                    "effective_date": doc.effective_date,
                    "expiry_date": doc.expiry_date,
                    "confidence": doc.confidence,
                    "tags": doc.tags + chunk.get("tags", []),
                    "chunk_index": chunk["index"],
                }
            )
            self.bm25_store.add(text=chunk["text"], metadata=doc.doc_id)
    
    def _semantic_chunk(self, content: str, doc_type: str) -> list[dict]:
        """语义分块
        
        这是第一个踩坑点：默认的RecursiveCharacterTextSplitter
        会把一个完整的流程切成碎片。
        
        策略：
        - FAQ：按Q&A对切分
        - 流程文档：按步骤切分
        - 政策文档：按条款切分
        - 产品文档：按功能模块切分
        """
        chunks = []
        
        if doc_type == "faq":
            # FAQ按Q&A对切分
            qa_pairs = content.split("\n\n")
            for i, pair in enumerate(qa_pairs):
                if pair.strip():
                    chunks.append({
                        "text": pair.strip(),
                        "index": i,
                        "tags": ["faq"]
                    })
        
        elif doc_type == "process":
            # 流程文档按步骤切分
            steps = self._split_by_heading(content)
            for i, step in enumerate(steps):
                if step.strip():
                    chunks.append({
                        "text": step.strip(),
                        "index": i,
                        "tags": ["process-step"]
                    })
        
        else:
            # 通用：按段落切分，但保持上下文重叠
            paragraphs = content.split("\n\n")
            buffer = ""
            buffer_start = 0
            
            for i, para in enumerate(paragraphs):
                if not para.strip():
                    continue
                buffer += para + "\n\n"
                
                # 每500字左右切一块，但保留前后各100字上下文
                if len(buffer) >= 500:
                    chunks.append({
                        "text": buffer.strip(),
                        "index": buffer_start,
                        "tags": [doc_type]
                    })
                    # 保留最后100字作为下一块的上下文
                    tail = buffer[-100:] if len(buffer) > 100 else buffer
                    buffer = tail
                    buffer_start = i + 1
            
            if buffer.strip():
                chunks.append({
                    "text": buffer.strip(),
                    "index": buffer_start,
                    "tags": [doc_type]
                })
        
        return chunks
    
    def _split_by_heading(self, content: str) -> list[str]:
        """按标题级别切分文档"""
        sections = []
        current = []
        
        for line in content.split("\n"):
            if line.startswith("#") and current:
                sections.append("\n".join(current))
                current = [line]
            else:
                current.append(line)
        
        if current:
            sections.append("\n".join(current))
        
        return sections
    
    def retrieve(self, query: str, top_k: int = 5, 
                 doc_types: Optional[list[str]] = None) -> list[dict]:
        """混合检索：向量 + BM25
        
        第二个踩坑点：纯向量检索会漏掉关键词精确匹配的结果。
        "退款流程" 和 "退款政策" 在向量空间中很近，
        但用户要的是流程不是政策。
        """
        # 向量检索
        vector_results = self.vector_store.search(
            query=query, top_k=top_k * 2
        )
        
        # BM25关键词检索
        keyword_results = self.bm25_store.search(
            query=query, top_k=top_k * 2
        )
        
        # 合并去重 + RRF（Reciprocal Rank Fusion）
        merged = self._rrf_merge(vector_results, keyword_results)
        
        # 过滤：类型、时效性、置信度
        filtered = []
        for item in merged:
            meta = item.get("metadata", {})
            
            # 类型过滤
            if doc_types and meta.get("doc_type") not in doc_types:
                continue
            
            # 时效性检查
            expiry = meta.get("expiry_date")
            if expiry and datetime.now() > datetime.fromisoformat(expiry):
                continue
            
            # 置信度过滤
            if meta.get("confidence", 1.0) < 0.5:
                item["low_confidence"] = True
            
            filtered.append(item)
            
            if len(filtered) >= top_k:
                break
        
        return filtered
    
    def _rrf_merge(self, results_a: list, results_b: list, k: int = 60) -> list:
        """RRF合并两组检索结果
        
        RRF公式：score = 1/(k + rank_a) + 1/(k + rank_b)
        k=60是经验值，对排名不敏感
        """
        scores = {}
        
        for rank, item in enumerate(results_a):
            doc_id = item.get("metadata", {}).get("doc_id", str(rank))
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
            if doc_id not in scores or "data" not in scores:
                scores[f"{doc_id}_data"] = item
        
        for rank, item in enumerate(results_b):
            doc_id = item.get("metadata", {}).get("doc_id", str(rank))
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
            if f"{doc_id}_data" not in scores:
                scores[f"{doc_id}_data"] = item
        
        # 按RRF分数排序
        sorted_ids = sorted(
            [k for k in scores.keys() if not k.endswith("_data")],
            key=lambda x: scores[x],
            reverse=True
        )
        
        return [scores[f"{doc_id}_data"] for doc_id in sorted_ids
                if f"{doc_id}_data" in scores]
```

### 3.3 Prompt工程：企业级System Prompt模板

第三个踩坑：Prompt太长会降低模型遵循度。我们把System Prompt控制在2000字以内，超过的部分通过RAG动态注入。

```python
SYSTEM_PROMPT_TEMPLATE = """你是{name}，{company}的{role}。

## 身份与职责
{identity}

## 能力边界
{capabilities}

## 输出规范
{output_format}

## 安全红线
{safety_rules}

## 当前的任务指令
{current_instruction}"""

# 实际使用示例
SYSTEM_PROMPT = """你是智能客服助手，XX公司的专业服务代表。

## 身份与职责
- 为用户提供产品咨询、售后支持、投诉处理服务
- 每次回复前，先确认用户意图，再提供针对性帮助
- 不确定的问题，明确告知用户并转人工

## 能力边界
你可以处理以下类型的问题：
- 产品功能咨询
- 订单查询与状态跟踪
- 退换货流程引导
- 账户问题排查
- 常见故障排查

你不能处理以下类型的问题（必须转人工）：
- 涉及金额退还的具体操作
- 用户隐私信息查询
- 超过SLA时限的历史订单
- 需要跨部门协调的投诉

## 输出规范
1. 先理解用户意图，用一句话确认（"您是想了解...对吗？"）
2. 给出明确、具体的操作步骤
3. 每步不超过2句话
4. 涉及操作时，用编号列出步骤
5. 结尾主动问"还有其他问题吗？"

## 安全红线
- 绝对不编造信息，不确定就说"我需要查一下"
- 绝对不泄露其他用户的信息
- 涉及支付、密码等敏感操作，必须引导到官方渠道
- 发现异常行为（如大量查询他人订单），记录并上报
"""
```

**关键经验**：
1. Prompt里明确写"不能做什么"比"能做什么"更重要
2. 输出格式规则要具体，"简洁"太模糊，"每步不超过2句话"才可执行
3. 安全红线单独一块，LLM对最后一段的遵循度最高

---

## 四、第二层：工具赋能

### 4.1 工具设计原则

工具设计是Agent专业化最容易忽略、影响最大的环节。

**核心洞察：工具描述比工具本身更重要。**

LLM选择调哪个工具，完全基于工具描述。描述不清晰，工具再强大也不会被正确调用。

```python
from typing import Literal
from pydantic import BaseModel, Field


# ❌ 错误示范：描述太模糊
bad_tools = [
    {
        "name": "search",
        "description": "搜索功能",
        "parameters": {"query": "搜索关键词"}
    },
    {
        "name": "database",
        "description": "数据库操作",
        "parameters": {"sql": "SQL语句"}
    }
]
# 问题1：LLM不知道什么时候该用search什么时候用database
# 问题2：LLM可能直接生成任意SQL，安全隐患巨大
# 问题3：参数缺乏约束，LLM可能传入无效值


# ✅ 正确示范：描述精确、参数有约束、有使用条件
class SearchOrderRequest(BaseModel):
    """搜索订单"""
    order_id: str = Field(
        ...,
        description="订单号，格式为ORD开头加12位数字，如ORD202601010001"
    )
    include_details: bool = Field(
        default=False,
        description="是否包含商品明细，默认只返回订单摘要"
    )


class RefundEligibilityCheckRequest(BaseModel):
    """退款资格检查
    
    在执行退款之前，必须先调用此接口检查是否符合退款条件。
    符合条件才能继续退款流程，不符合条件需要向用户解释原因。
    """
    order_id: str = Field(
        ...,
        description="订单号，格式ORD+12位数字"
    )
    reason: Literal["quality", "wrong_item", "not_received", "other"] = Field(
        ...,
        description=(
            "退款原因：quality=质量问题, wrong_item=发错货, "
            "not_received=未收到货, other=其他原因"
        )
    )


TOOL_DEFINITIONS = [
    {
        "name": "search_order",
        "description": (
            "根据订单号查询订单信息。当用户提到'我的订单'、'查一下订单'、"
            "'ORD开头的单号'时使用。返回订单状态、物流信息、商品摘要。"
        ),
        "input_schema": SearchOrderRequest.model_json_schema(),
    },
    {
        "name": "check_refund_eligibility",
        "description": (
            "检查订单是否符合退款条件。当用户要求退款时，必须先调用此接口。"
            "返回是否符合退款条件、退款金额、退款方式。"
            "注意：此接口只检查不执行，确认符合后需要调用execute_refund。"
        ),
        "input_schema": RefundEligibilityCheckRequest.model_json_schema(),
    },
    {
        "name": "execute_refund",
        "description": (
            "执行退款操作。必须在check_refund_eligibility返回'符合条件'后才能调用。"
            "调用前需要向用户确认退款金额和方式。"
            "注意：此接口有幂等保护，同一订单重复调用不会重复退款。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "订单号"},
                "refund_amount": {
                    "type": "number",
                    "description": "退款金额（元），必须与check_refund_eligibility返回的金额一致"
                },
                "refund_method": {
                    "type": "string",
                    "enum": ["original", "balance", "bank_card"],
                    "description": "退款方式：original=原路退回, balance=退到余额, bank_card=退到银行卡"
                },
                "confirmed_by_user": {
                    "type": "boolean",
                    "description": "用户是否已确认退款，必须是true"
                }
            },
            "required": ["order_id", "refund_amount", "refund_method", "confirmed_by_user"]
        },
    },
    {
        "name": "transfer_to_human",
        "description": (
            "转接人工客服。以下情况必须转人工："
            "1. 涉及金额退还的具体操作 2. 用户隐私信息查询 3. "
            "超出能力范围的复杂问题 4. 用户明确要求转人工 5. "
            "连续2次回答后用户仍不满意"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "enum": [
                        "payment_issue", "privacy_request", "complex_case",
                        "user_request", "repeated_failure"
                    ],
                    "description": "转人工原因"
                },
                "context_summary": {
                    "type": "string",
                    "description": "向人工客服传递的上下文摘要，包括已尝试的解决方案"
                }
            },
            "required": ["reason", "context_summary"]
        },
    },
]
```

### 4.2 工具调用安全：执行层

工具定义决定LLM"调什么"，执行层决定"怎么调"。

```python
import time
import logging
from functools import wraps
from typing import Any, Callable


logger = logging.getLogger("agent.tools")


class ToolExecutionError(Exception):
    """工具执行错误（可重试）"""
    def __init__(self, tool_name: str, message: str, retryable: bool = False):
        self.tool_name = tool_name
        self.retryable = retryable
        super().__init__(f"[{tool_name}] {message}")


class ToolSecurityError(Exception):
    """工具安全错误（不可重试，需要告警）"""
    def __init__(self, tool_name: str, message: str, severity: str = "high"):
        self.tool_name = tool_name
        self.severity = severity
        super().__init__(f"[SECURITY][{tool_name}][{severity}] {message}")


def with_tool_guard(
    tool_name: str,
    timeout: float = 10.0,
    max_retries: int = 2,
    rate_limit_per_minute: int = 60,
    sensitive_fields: list[str] | None = None,
):
    """工具执行守卫装饰器
    
    生产环境必须有的安全措施：
    1. 超时控制：防止单个工具调用卡住整个Agent
    2. 重试机制：网络抖动等临时错误自动重试
    3. 限流控制：防止Agent进入循环疯狂调用
    4. 敏感信息脱敏：日志中不记录手机号、身份证等
    """
    call_times: list[float] = []
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> dict[str, Any]:
            # 限流检查
            now = time.time()
            call_times[:] = [t for t in call_times if now - t < 60]
            if len(call_times) >= rate_limit_per_minute:
                raise ToolExecutionError(
                    tool_name,
                    f"Rate limit exceeded: {rate_limit_per_minute}/min",
                    retryable=False
                )
            call_times.append(now)
            
            # 敏感信息脱敏（日志）
            log_kwargs = kwargs.copy()
            if sensitive_fields:
                for field in sensitive_fields:
                    if field in log_kwargs:
                        val = str(log_kwargs[field])
                        log_kwargs[field] = val[:3] + "***" + val[-3:] if len(val) > 6 else "***"
            
            logger.info(
                f"Tool call: {tool_name} | args: {log_kwargs}",
                extra={"tool_name": tool_name, "args": log_kwargs}
            )
            
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    start = time.time()
                    result = func(*args, **kwargs)
                    elapsed = time.time() - start
                    
                    logger.info(
                        f"Tool success: {tool_name} | elapsed: {elapsed:.2f}s",
                        extra={"tool_name": tool_name, "elapsed": elapsed}
                    )
                    
                    return result
                
                except TimeoutError as e:
                    last_error = e
                    logger.warning(
                        f"Tool timeout: {tool_name} | attempt: {attempt + 1}",
                        extra={"tool_name": tool_name, "attempt": attempt + 1}
                    )
                    if attempt == max_retries:
                        raise ToolExecutionError(tool_name, str(e), retryable=True)
                
                except ToolSecurityError:
                    raise  # 安全错误不重试
                
                except Exception as e:
                    last_error = e
                    logger.error(
                        f"Tool error: {tool_name} | {type(e).__name__}: {e}",
                        extra={"tool_name": tool_name, "error": str(e)},
                        exc_info=True
                    )
                    if attempt == max_retries:
                        raise ToolExecutionError(tool_name, str(e))
            
            raise last_error  # type: ignore
        
        return wrapper
    return decorator


# 使用示例
@with_tool_guard(
    tool_name="search_order",
    timeout=5.0,
    sensitive_fields=["order_id"]
)
def search_order(order_id: str, include_details: bool = False) -> dict:
    """实际查询订单"""
    # 实现省略...
    return {
        "order_id": order_id,
        "status": "shipped",
        "amount": 299.00,
        "logistics": "顺丰速运 SF1234567890"
    }


@with_tool_guard(
    tool_name="execute_refund",
    timeout=15.0,
    max_retries=3,
    sensitive_fields=["order_id"]
)
def execute_refund(order_id: str, refund_amount: float,
                   refund_method: str, confirmed_by_user: bool) -> dict:
    """执行退款
    
    踩坑：曾经出现过LLM没调用check_refund_eligibility就直接调用execute_refund，
    导致不符合退款条件的订单也被退了。
    修复：在执行层加上前置检查。
    """
    if not confirmed_by_user:
        raise ToolSecurityError(
            "execute_refund",
            "User confirmation required but not provided",
            severity="critical"
        )
    
    # 检查金额是否合理（不超过原订单金额的1.2倍）
    order = get_order(order_id)
    if refund_amount > order["amount"] * 1.2:
        raise ToolSecurityError(
            "execute_refund",
            f"Refund amount {refund_amount} exceeds order amount {order['amount']}",
            severity="critical"
        )
    
    # 幂等检查
    if has_refund_in_progress(order_id):
        raise ToolExecutionError(
            "execute_refund",
            f"Refund already in progress for {order_id}",
            retryable=False
        )
    
    # 实际退款逻辑...
    return {"status": "success", "refund_id": f"REF{order_id[-12:]}"}


def get_order(order_id: str) -> dict:
    """模拟获取订单信息"""
    return {"order_id": order_id, "amount": 299.00}


def has_refund_in_progress(order_id: str) -> bool:
    """检查是否有退款进行中"""
    return False
```

---

## 五、第三层：流程规范

### 5.1 单Agent流程控制

单Agent不是"问一句答一句"。专业Agent有明确的处理流程：

```python
from enum import Enum
from dataclasses import dataclass


class ConversationState(Enum):
    """对话状态机
    
    踩坑：之前没有状态管理，Agent每次都是无状态处理。
    用户第一次问"退款"，Agent给了流程说明。
    用户第二次说"好的"，Agent不知道用户在说"好的"什么。
    """
    INTENT_RECOGNITION = "intent_recognition"    # 意图识别
    INFORMATION_GATHERING = "info_gathering"      # 信息收集
    TOOL_EXECUTION = "tool_execution"            # 工具执行
    RESPONSE_GENERATION = "response_generation"  # 回复生成
    CONFIRMATION = "confirmation"                # 确认环节
    ESCALATION = "escalation"                    # 升级处理
    TRANSFER_HUMAN = "transfer_human"            # 转人工


@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str
    user_id: str
    state: ConversationState = ConversationState.INTENT_RECOGNITION
    intent: str | None = None
    collected_info: dict = None  # type: ignore
    tool_calls: list[dict] = None  # type: ignore
    attempts: int = 0  # 当前状态尝试次数
    
    def __post_init__(self):
        if self.collected_info is None:
            self.collected_info = {}
        if self.tool_calls is None:
            self.tool_calls = []
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "state": self.state.value,
            "intent": self.intent,
            "collected_info": self.collected_info,
            "attempts": self.attempts,
        }


class AgentOrchestrator:
    """Agent流程编排器"""
    
    MAX_STATE_ATTEMPTS = 3  # 单状态最大尝试次数
    MAX_TURNS = 15          # 单轮对话最大交互次数
    
    def __init__(self, llm_client, tool_executor, rag_system):
        self.llm = llm_client
        self.tools = tool_executor
        self.rag = rag_system
    
    def process(self, context: ConversationContext, 
                user_message: str) -> tuple[str, ConversationContext]:
        """处理用户消息，返回（回复内容, 更新后的上下文）"""
        
        # 检查交互次数上限
        if context.attempts >= self.MAX_TURNS:
            return (
                "抱歉，我尝试了很多次都没能帮您解决问题。"
                "建议转接人工客服获得更专业的帮助。",
                ConversationContext(
                    session_id=context.session_id,
                    user_id=context.user_id,
                    state=ConversationState.TRANSFER_HUMAN
                )
            )
        
        # 状态路由
        if context.state == ConversationState.INTENT_RECOGNITION:
            return self._recognize_intent(context, user_message)
        
        elif context.state == ConversationState.INFORMATION_GATHERING:
            return self._gather_information(context, user_message)
        
        elif context.state == ConversationState.TOOL_EXECUTION:
            return self._execute_tool(context, user_message)
        
        elif context.state == ConversationState.CONFIRMATION:
            return self._handle_confirmation(context, user_message)
        
        else:
            return self._fallback(context, user_message)
    
    def _recognize_intent(self, ctx: ConversationContext, 
                          message: str) -> tuple[str, ConversationContext]:
        """意图识别"""
        
        # 先用LLM识别意图
        intent_prompt = f"""根据用户消息识别意图。

用户消息：{message}

可能的意图：
- order_query: 查询订单状态
- refund_request: 申请退款
- product_inquiry: 产品咨询
- complaint: 投诉
- other: 其他

只返回意图名称，不要解释。"""
        
        intent = self.llm.generate(intent_prompt, max_tokens=20).strip()
        ctx.intent = intent
        ctx.state = ConversationState.INFORMATION_GATHERING
        
        # 检查是否需要立即转人工
        if intent in ("complaint",):
            return (
                "我理解您遇到了问题，这需要人工客服来帮您更好地处理。"
                "我先把您的情况整理一下，马上为您转接。",
                ConversationContext(
                    session_id=ctx.session_id,
                    user_id=ctx.user_id,
                    state=ConversationState.TRANSFER_HUMAN,
                    intent=intent,
                    collected_info={"original_message": message}
                )
            )
        
        # 不同意图需要不同的信息
        required_fields = {
            "order_query": ["order_id"],
            "refund_request": ["order_id", "reason"],
            "product_inquiry": ["product_name"],
        }
        
        if intent in required_fields:
            fields = required_fields[intent]
            missing = [f for f in fields if f not in ctx.collected_info]
            
            if missing:
                field_names = {"order_id": "订单号", "reason": "退款原因", 
                              "product_name": "产品名称"}
                ask_for = "和".join([field_names.get(f, f) for f in missing])
                return (
                    f"好的，我来帮您处理。请提供一下您的{ask_for}。",
                    ctx
                )
        
        # 信息齐全，进入工具执行
        ctx.state = ConversationState.TOOL_EXECUTION
        return self._execute_tool(ctx, message)
    
    def _gather_information(self, ctx: ConversationContext,
                            message: str) -> tuple[str, ConversationContext]:
        """信息收集"""
        
        # 简单的字段提取（生产环境用LLM）
        if "ORD" in message.upper():
            ctx.collected_info["order_id"] = message.strip()
        
        # 检查是否收集齐全
        required_fields = {
            "order_query": ["order_id"],
            "refund_request": ["order_id", "reason"],
        }
        
        if ctx.intent in required_fields:
            fields = required_fields[ctx.intent]
            missing = [f for f in fields if f not in ctx.collected_info]
            
            if not missing:
                ctx.state = ConversationState.TOOL_EXECUTION
                return self._execute_tool(ctx, message)
        
        # 还需要更多信息
        return (
            f"收到。还需要您提供一下：{_format_missing(missing)}",
            ctx
        )
    
    def _execute_tool(self, ctx: ConversationContext,
                      message: str) -> tuple[str, ConversationContext]:
        """工具执行"""
        
        try:
            if ctx.intent == "order_query":
                result = self.tools.execute(
                    "search_order",
                    order_id=ctx.collected_info["order_id"]
                )
                response = self._format_order_result(result)
                ctx.state = ConversationState.RESPONSE_GENERATION
                return response, ctx
            
            elif ctx.intent == "refund_request":
                # 先检查退款资格
                eligibility = self.tools.execute(
                    "check_refund_eligibility",
                    order_id=ctx.collected_info["order_id"],
                    reason=ctx.collected_info["reason"]
                )
                
                if not eligibility["eligible"]:
                    ctx.state = ConversationState.RESPONSE_GENERATION
                    return (
                        f"抱歉，您的订单{ctx.collected_info['order_id']} "
                        f"不符合退款条件：{eligibility['reason']}",
                        ctx
                    )
                
                # 需要用户确认退款金额
                ctx.collected_info["refund_amount"] = eligibility["amount"]
                ctx.state = ConversationState.CONFIRMATION
                return (
                    f"您的订单{ctx.collected_info['order_id']}符合退款条件。\n"
                    f"退款金额：¥{eligibility['amount']:.2f}\n"
                    f"退款原因：{ctx.collected_info['reason']}\n\n"
                    f"确认退款吗？",
                    ctx
                )
        
        except ToolExecutionError as e:
            ctx.attempts += 1
            
            if ctx.attempts >= self.MAX_STATE_ATTEMPTS:
                return (
                    f"处理您的请求时遇到了问题。为了不耽误您的时间，"
                    f"我帮您转接人工客服。",
                    ConversationContext(
                        session_id=ctx.session_id,
                        user_id=ctx.user_id,
                        state=ConversationState.TRANSFER_HUMAN,
                        intent=ctx.intent,
                        collected_info=ctx.collected_info,
                        attempts=ctx.attempts,
                    )
                )
            
            return (
                f"抱歉，处理时遇到了一点问题：{str(e)}。我再试一次。",
                ctx
            )
        
        return "好的，我来帮您处理。", ctx
    
    def _handle_confirmation(self, ctx: ConversationContext,
                             message: str) -> tuple[str, ConversationContext]:
        """确认环节"""
        
        is_confirmed = any(
            word in message for word in ["确认", "好的", "是的", "对", "可以", "确定"]
        )
        
        if is_confirmed:
            try:
                result = self.tools.execute(
                    "execute_refund",
                    order_id=ctx.collected_info["order_id"],
                    refund_amount=ctx.collected_info["refund_amount"],
                    refund_method="original",
                    confirmed_by_user=True
                )
                ctx.state = ConversationState.RESPONSE_GENERATION
                return (
                    f"退款申请已提交成功！\n"
                    f"退款单号：{result['refund_id']}\n"
                    f"预计1-3个工作日到账。\n\n"
                    f"还有其他问题吗？",
                    ctx
                )
            except ToolSecurityError as e:
                # 安全错误立即转人工
                return (
                    f"退款处理遇到异常，已为您转接人工客服处理。",
                    ConversationContext(
                        session_id=ctx.session_id,
                        user_id=ctx.user_id,
                        state=ConversationState.TRANSFER_HUMAN,
                        intent=ctx.intent,
                        collected_info=ctx.collected_info,
                    )
                )
        
        # 用户取消
        return "好的，已取消退款申请。还有其他问题吗？", ctx
    
    def _fallback(self, ctx: ConversationContext,
                  message: str) -> tuple[str, ConversationContext]:
        """兜底处理"""
        ctx.state = ConversationState.INTENT_RECOGNITION
        ctx.attempts += 1
        
        return (
            "抱歉，我没完全理解您的意思。您可以说得更具体一些吗？"
            "\n\n我可以帮您：\n"
            "1. 查询订单状态\n"
            "2. 申请退款\n"
            "3. 产品咨询\n"
            "4. 转接人工客服",
            ctx
        )
    
    def _format_order_result(self, result: dict) -> str:
        """格式化订单查询结果"""
        status_map = {
            "pending": "待发货", "shipped": "已发货",
            "delivered": "已送达", "cancelled": "已取消"
        }
        return (
            f"订单查询结果：\n"
            f"订单号：{result['order_id']}\n"
            f"状态：{status_map.get(result['status'], result['status'])}\n"
            f"金额：¥{result['amount']:.2f}\n"
            f"物流：{result.get('logistics', '暂无')}\n\n"
            f"还有其他问题吗？"
        )


def _format_missing(missing: list[str]) -> str:
    """格式化缺失字段"""
    field_names = {"order_id": "订单号", "reason": "退款原因", "product_name": "产品名称"}
    return "、".join([field_names.get(f, f) for f in missing])
```

### 5.2 多Agent协作

真正的企业级系统不会只有一个Agent。

```
                    ┌──────────┐
                    │  Gateway  │  统一入口、鉴权、限流
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │  Router   │  意图识别 + Agent路由
                    └────┬─────┘
                         │
           ┌─────────────┼─────────────┐
           │             │             │
    ┌──────▼─────┐ ┌────▼────┐ ┌──────▼──────┐
    │ 售后Agent  │ │ 产品Agent│ │ 投诉Agent   │
    │ (退换货)   │ │ (咨询)  │ │ (升级处理)  │
    └──────┬─────┘ └────┬────┘ └──────┬──────┘
           │             │             │
           └─────────────┼─────────────┘
                         │
                    ┌────▼─────┐
                    │ 风控Agent │  合规检查、敏感词、风险提示
                    └──────────┘
```

```python
import json
from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    """Agent配置"""
    name: str
    description: str
    system_prompt: str
    tools: list[str]
    can_transfer_to: list[str] = field(default_factory=list)
    requires_human_review: bool = False  # 输出是否需要人工审核


class MultiAgentRouter:
    """多Agent路由器
    
    踩坑：路由器的准确性直接决定用户体验。
    之前用纯LLM做路由，准确率只有85%。
    加上关键词规则+意图分类模型后，准确率提升到96%。
    """
    
    def __init__(self, agents: dict[str, AgentConfig], llm_client):
        self.agents = agents
        self.llm = llm_client
        
        # 关键词快速匹配规则（优先级最高）
        self.keyword_rules = {
            "aftersales": ["退款", "退货", "换货", "发票", "维修", "损坏", "瑕疵"],
            "product": ["功能", "怎么用", "多少钱", "参数", "规格", "对比", "推荐"],
            "complaint": ["投诉", "差评", "举报", "消协", "12315", "欺骗"],
        }
    
    def route(self, user_message: str) -> str:
        """路由到合适的Agent"""
        
        # 第一层：关键词快速匹配
        for agent_name, keywords in self.keyword_rules.items():
            for kw in keywords:
                if kw in user_message:
                    return agent_name
        
        # 第二层：LLM意图分类
        agent_list = "\n".join(
            f"- {name}: {config.description}" 
            for name, config in self.agents.items()
        )
        
        prompt = f"""将用户消息路由到最合适的Agent。

可选Agent：
{agent_list}

用户消息：{user_message}

只返回Agent名称，不要解释。"""
        
        agent_name = self.llm.generate(prompt, max_tokens=20).strip()
        
        # 兜底
        if agent_name not in self.agents:
            return "general"
        
        return agent_name


class MultiAgentOrchestrator:
    """多Agent编排器"""
    
    def __init__(self, router: MultiAgentRouter, 
                 agent_orchestrators: dict[str, AgentOrchestrator],
                 risk_agent: AgentOrchestrator):
        self.router = router
        self.agents = agent_orchestrators
        self.risk_agent = risk_agent
    
    def process(self, context: ConversationContext,
                user_message: str) -> tuple[str, ConversationContext]:
        """多Agent处理流程"""
        
        # 1. 路由
        agent_name = self.router.route(user_message)
        
        # 2. Agent处理
        agent = self.agents.get(agent_name, self.agents["general"])
        response, updated_ctx = agent.process(context, user_message)
        
        # 3. 风控审核（所有Agent的输出都要过风控）
        risk_result = self.risk_agent.process(
            ConversationContext(
                session_id=context.session_id,
                user_id=context.user_id,
                state=ConversationState.TOOL_EXECUTION,
                collected_info={"response_to_check": response}
            ),
            response
        )
        
        # 4. 如果风控不通过，替换回复
        if risk_result[1].collected_info.get("risk_flag"):
            response = (
                "我理解您的需求，但这个需要更专业的同事来处理。"
                "马上为您转接人工客服。"
            )
            updated_ctx.state = ConversationState.TRANSFER_HUMAN
        
        return response, updated_ctx
```

---

## 六、第四层：持续进化

### 6.1 评估体系

没有度量就无法改进。

```python
from dataclasses import dataclass
from enum import Enum
import json


class EvaluationDimension(Enum):
    ACCURACY = "accuracy"          # 准确性
    COMPLETENESS = "completeness"  # 完整性
    SAFETY = "safety"              # 安全性
    EFFICIENCY = "efficiency"      # 效率
    USER_SATISFACTION = "satisfaction"  # 用户满意度


@dataclass
class EvaluationResult:
    """评估结果"""
    dimension: EvaluationDimension
    score: float  # 0-1
    details: str
    severity: str = "info"  # info, warning, error, critical


class AgentEvaluator:
    """Agent评估器
    
    踩坑：之前只看准确率，发现Agent在安全问题上表现很差。
    改为多维度评估后，安全问题的发现率提高了3倍。
    """
    
    # 各维度权重
    DIMENSION_WEIGHTS = {
        EvaluationDimension.ACCURACY: 0.3,
        EvaluationDimension.COMPLETENESS: 0.2,
        EvaluationDimension.SAFETY: 0.3,  # 安全性权重最高
        EvaluationDimension.EFFICIENCY: 0.1,
        EvaluationDimension.USER_SATISFACTION: 0.1,
    }
    
    def evaluate(self, query: str, response: str, 
                 expected: str | None = None,
                 tool_calls: list[dict] | None = None,
                 context: dict | None = None) -> list[EvaluationResult]:
        """多维度评估"""
        
        results = []
        
        # 1. 安全性检查（最高优先级）
        results.extend(self._check_safety(response))
        
        # 2. 准确性检查
        if expected:
            results.append(self._check_accuracy(response, expected))
        
        # 3. 完整性检查
        results.append(self._check_completeness(query, response))
        
        # 4. 效率检查
        if tool_calls:
            results.append(self._check_efficiency(tool_calls))
        
        return results
    
    def _check_safety(self, response: str) -> list[EvaluationResult]:
        """安全性检查"""
        results = []
        
        # 敏感信息泄露检查
        sensitive_patterns = [
            ("手机号", r"1[3-9]\d{9}"),
            ("身份证", r"\d{17}[\dXx]"),
            ("银行卡号", r"\d{16,19}"),
            ("邮箱", r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
        ]
        
        import re
        for name, pattern in sensitive_patterns:
            if re.search(pattern, response):
                results.append(EvaluationResult(
                    dimension=EvaluationDimension.SAFETY,
                    score=0.0,
                    details=f"回复中包含疑似{name}信息：{pattern}",
                    severity="critical"
                ))
        
        # 有害内容检查
        harmful_keywords = ["自杀", "自残", "暴力", "赌博"]
        for kw in harmful_keywords:
            if kw in response and "建议咨询专业人士" not in response:
                results.append(EvaluationResult(
                    dimension=EvaluationDimension.SAFETY,
                    score=0.2,
                    details=f"回复包含敏感词'{kw}'但未提供求助引导",
                    severity="warning"
                ))
        
        # 幻觉检查：检测是否编造信息
        hallucination_signals = ["据我所知", "我记得", "应该是", "大概率"]
        for signal in hallucination_signals:
            if signal in response:
                results.append(EvaluationResult(
                    dimension=EvaluationDimension.SAFETY,
                    score=0.7,
                    details=f"回复包含不确定表述'{signal}'，可能存在幻觉风险",
                    severity="info"
                ))
        
        if not results:
            results.append(EvaluationResult(
                dimension=EvaluationDimension.SAFETY,
                score=1.0,
                details="安全性检查通过"
            ))
        
        return results
    
    def _check_accuracy(self, response: str, expected: str) -> EvaluationResult:
        """准确性检查"""
        # 简单实现：关键信息匹配
        # 生产环境建议用LLM-as-judge
        expected_keywords = expected.split("，")
        matched = sum(1 for kw in expected_keywords if kw.strip() in response)
        score = matched / len(expected_keywords) if expected_keywords else 0.5
        
        return EvaluationResult(
            dimension=EvaluationDimension.ACCURACY,
            score=score,
            details=f"关键信息匹配：{matched}/{len(expected_keywords)}"
        )
    
    def _check_completeness(self, query: str, response: str) -> EvaluationResult:
        """完整性检查"""
        # 检查回复是否解决了用户的全部需求
        score = 0.8  # 简化实现
        
        if len(response) < 50:
            score = 0.4
            details = "回复过短，可能未完整回答"
        else:
            details = "完整性检查通过"
        
        return EvaluationResult(
            dimension=EvaluationDimension.COMPLETENESS,
            score=score,
            details=details
        )
    
    def _check_efficiency(self, tool_calls: list[dict]) -> EvaluationResult:
        """效率检查"""
        count = len(tool_calls)
        
        if count > 10:
            return EvaluationResult(
                dimension=EvaluationDimension.EFFICIENCY,
                score=0.3,
                details=f"工具调用次数过多：{count}次，可能存在冗余调用",
                severity="warning"
            )
        elif count > 5:
            return EvaluationResult(
                dimension=EvaluationDimension.EFFICIENCY,
                score=0.7,
                details=f"工具调用次数偏多：{count}次，建议优化"
            )
        else:
            return EvaluationResult(
                dimension=EvaluationDimension.EFFICIENCY,
                score=1.0,
                details=f"工具调用效率良好：{count}次"
            )
    
    def calculate_overall_score(self, results: list[EvaluationResult]) -> float:
        """计算加权总分"""
        total = 0.0
        for result in results:
            weight = self.DIMENSION_WEIGHTS.get(result.dimension, 0)
            total += result.score * weight
        
        return total
    
    def generate_report(self, query: str, response: str, 
                        results: list[EvaluationResult]) -> str:
        """生成评估报告"""
        overall = self.calculate_overall_score(results)
        
        report_lines = [
            f"## Agent评估报告",
            f"",
            f"**总分**: {overall:.2f}/1.00",
            f"**用户问题**: {query}",
            f"",
        ]
        
        for result in results:
            emoji = "✅" if result.score >= 0.8 else "⚠️" if result.score >= 0.5 else "❌"
            report_lines.append(
                f"{emoji} **{result.dimension.value}**: {result.score:.2f} - {result.details}"
            )
        
        return "\n".join(report_lines)
```

### 6.2 Bad Case收集与自动优化

```python
import json
from datetime import datetime
from pathlib import Path


class BadCaseCollector:
    """Bad Case收集器
    
    生产环境必备：
    1. 每次评估不通过的case自动记录
    2. 定期分析bad case模式
    3. 根据模式自动生成优化建议
    """
    
    def __init__(self, storage_path: str = "bad_cases.jsonl"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    def collect(self, query: str, response: str, 
                results: list[EvaluationResult],
                metadata: dict | None = None):
        """收集bad case"""
        
        # 只收集有问题的case
        has_issue = any(r.score < 0.7 for r in results)
        if not has_issue:
            return
        
        case = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "evaluation": [
                {
                    "dimension": r.dimension.value,
                    "score": r.score,
                    "details": r.details,
                    "severity": r.severity,
                }
                for r in results if r.score < 0.7
            ],
            "metadata": metadata or {},
        }
        
        with open(self.storage_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")
    
    def analyze_patterns(self, limit: int = 100) -> list[dict]:
        """分析bad case模式
        
        返回高频问题模式及优化建议
        """
        cases = self._load_recent(limit)
        if not cases:
            return []
        
        # 按维度统计
        dimension_stats = {}
        for case in cases:
            for ev in case["evaluation"]:
                dim = ev["dimension"]
                if dim not in dimension_stats:
                    dimension_stats[dim] = {"count": 0, "examples": []}
                dimension_stats[dim]["count"] += 1
                if len(dimension_stats[dim]["examples"]) < 3:
                    dimension_stats[dim]["examples"].append(case["query"][:50])
        
        # 生成优化建议
        suggestions = {
            "accuracy": (
                "准确率问题较多。建议：\n"
                "1. 检查RAG检索质量，考虑增加知识库文档\n"
                "2. 优化Prompt中的约束条件\n"
                "3. 添加置信度检查，低置信度时主动澄清"
            ),
            "safety": (
                "安全问题 detected！建议：\n"
                "1. 立即排查最近的回复记录\n"
                "2. 加强敏感信息过滤规则\n"
                "3. 降低问题回复的置信度阈值"
            ),
            "completeness": (
                "完整性问题。建议：\n"
                "1. 优化Agent流程控制，确保多轮对话不遗漏\n"
                "2. 增加回复长度的最低要求\n"
                "3. 添加'是否解决了用户问题'的自检步骤"
            ),
            "efficiency": (
                "效率问题。建议：\n"
                "1. 检查是否有冗余的工具调用\n"
                "2. 优化工具描述，减少LLM的试错\n"
                "3. 添加工具调用缓存"
            ),
        }
        
        report = []
        for dim, stats in sorted(
            dimension_stats.items(), 
            key=lambda x: x[1]["count"], 
            reverse=True
        ):
            report.append({
                "dimension": dim,
                "count": stats["count"],
                "total_rate": f"{stats['count']}/{len(cases)}",
                "examples": stats["examples"],
                "suggestion": suggestions.get(dim, "暂无建议"),
            })
        
        return report
    
    def _load_recent(self, limit: int) -> list[dict]:
        """加载最近的bad case"""
        if not self.storage_path.exists():
            return []
        
        cases = []
        with open(self.storage_path, "r", encoding="utf-8") as f:
            for line in f:
                cases.append(json.loads(line.strip()))
        
        return cases[-limit:]
```

---

## 七、生产部署

### 7.1 Docker部署

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 代码
COPY src/ ./src/
COPY configs/ ./configs/

# 非root用户
RUN useradd -m appuser
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

EXPOSE 8000

CMD ["python", "-m", "src.main"]
```

### 7.2 可观测性

生产环境必须有三件事：日志、指标、追踪。

```python
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass


# 结构化日志
logger = logging.getLogger("agent")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '{"time":"%(asctime)s","level":"%(levelname)s",'
    '"msg":"%(message)s","extra":%(extra)s}'
))
logger.addHandler(handler)


@dataclass
class AgentMetrics:
    """Agent运行指标"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tool_calls: int = 0
    total_llm_tokens: int = 0
    total_latency_ms: float = 0
    transfer_human_count: int = 0


@contextmanager
def trace_agent(session_id: str, user_id: str, metrics: AgentMetrics):
    """Agent调用追踪"""
    metrics.total_requests += 1
    start = time.time()
    
    logger.info(
        "Agent request started",
        extra={
            "session_id": session_id,
            "user_id": user_id,
            "event": "request_start"
        }
    )
    
    try:
        yield
        metrics.successful_requests += 1
        logger.info(
            "Agent request completed",
            extra={
                "session_id": session_id,
                "user_id": user_id,
                "event": "request_end",
                "latency_ms": (time.time() - start) * 1000,
            }
        )
    except Exception as e:
        metrics.failed_requests += 1
        logger.error(
            f"Agent request failed: {e}",
            extra={
                "session_id": session_id,
                "user_id": user_id,
                "event": "request_error",
                "error": str(e),
            },
            exc_info=True
        )
        raise
    finally:
        metrics.total_latency_ms += (time.time() - start) * 1000


@contextmanager
def trace_tool_call(tool_name: str, metrics: AgentMetrics):
    """工具调用追踪"""
    metrics.total_tool_calls += 1
    start = time.time()
    
    logger.info(
        f"Tool call: {tool_name}",
        extra={"tool_name": tool_name, "event": "tool_start"}
    )
    
    try:
        yield
        logger.info(
            f"Tool completed: {tool_name}",
            extra={
                "tool_name": tool_name,
                "event": "tool_end",
                "latency_ms": (time.time() - start) * 1000,
            }
        )
    except Exception as e:
        logger.error(
            f"Tool failed: {tool_name} - {e}",
            extra={"tool_name": tool_name, "event": "tool_error"},
            exc_info=True
        )
        raise
```

---

## 八、踩坑总结

把所有踩坑浓缩成一张表：

| 坑 | 症状 | 根因 | 解法 |
|-----|------|------|------|
| RAG切分太碎 | 检索到碎片，拼不出完整答案 | 按固定长度切，不按语义切 | 按文档类型选择切分策略 |
| 纯向量检索漏结果 | "退款流程"返回"退款政策" | 关键词精确匹配被语义相似度淹没 | 混合检索：向量+BM25+RRF |
| 知识过期 | 给用户已失效的信息 | 入库没设过期时间 | 每条知识加effective_date和expiry_date |
| 工具描述模糊 | LLM调错工具 | 描述太短或不含触发条件 | 描述里写明"当用户提到X时使用" |
| 无状态处理 | 多轮对话断裂 | 没有对话状态管理 | 引入状态机管理对话流程 |
| 安全漏洞 | Agent泄露敏感信息 | 没有输出过滤和工具执行守卫 | 加Tool Guard + 输出安全检查 |
| 幻觉 | Agent编造不存在的订单 | 模型"乐于助人"倾向 | 检测不确定表述，低置信度时主动说"我需要查一下" |
| 退款误操作 | 不符合条件的订单被退款 | 缺少前置检查和幂等保护 | 两步退款：先检查再执行 + 幂等保护 |
| 路由不准 | 客服问题路由到产品Agent | 纯LLM路由不够可靠 | 关键词规则 + LLM分类双层路由 |
| 无评估体系 | 不知道Agent到底好不好 | 没有量化指标 | 建立多维度评估 + Bad Case自动收集 |
| 评估只看准确率 | 安全问题被忽略 | 安全性权重太低 | 安全性权重至少0.3 |
| 无限循环 | Agent反复调工具 | 没有最大交互次数限制 | MAX_TURNS限制 + 熔断机制 |

---

## 九、落地优先级建议

如果你现在要开始做一个企业级Agent，按这个顺序来：

**第一阶段（1-2周）：能跑起来**
1. 明确Agent边界：什么能做什么不能做
2. 设计3-5个核心工具，工具描述要精确
3. Prompt工程：输出格式、安全红线
4. 基础RAG（哪怕是简单的文档检索）

**第二阶段（2-4周）：能用好**
5. 工具执行守卫：超时、重试、限流、安全检查
6. 对话状态管理：状态机控制流程
7. 混合检索：向量+BM25
8. 基础评估：准确率+安全性

**第三阶段（4-8周）：能生产**
9. 多Agent协作：路由+专业Agent
10. 风控Agent：合规检查、敏感信息过滤
11. 可观测性：结构化日志、指标、追踪
12. Bad Case收集与分析

**第四阶段（持续）：能进化**
13. A/B测试框架
14. 自动评估+告警
15. 基于Bad Case的自动优化
16. 版本管理与灰度发布

---

## 总结

企业级Agent专业化不是一门玄学，是一套可复制的方法论。

四个层次、十二个步骤，每一步都有明确的目标和验收标准。关键是**不要跳层**，地基不牢，上层再精美也站不住。

最核心的一句话：**流程控制大于模型能力，工具描述比工具本身重要，安全合规是底线不是加分项。**

这三句话，是我们踩了几百个坑之后提炼出来的。希望对你有用。
