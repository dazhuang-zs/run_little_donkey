# AI时代的限流：当Token比QPS更致命，你的系统可能正在裸奔

传统限流按请求数（QPS）计数，LLM API限流按Token维度计量。这是两套完全不同的游戏规则。

你以为用令牌桶控住了并发，结果一条长Prompt直接打爆TPM配额。你以为指数退避能兜底429，结果DeepSeek凌晨3点错峰降价，你的重试策略比风控还慢。你以为多Key轮询就能突破上限，结果所有Key共享同一个组织级配额池。

这篇文章不讲令牌桶和漏桶的区别。讲的是：当你的后端从调MySQL变成调GPT-4o，限流这件事发生了什么本质变化，以及怎么在生产环境活下去。

## 一、LLM API的限流规则，和你想的不一样

### 1.1 三维限流：RPM × TPM × 并发

传统API限流就一个维度：每秒请求数。超了就429，逻辑简单。

LLM API至少三个维度同时生效：

| 限流维度 | 含义 | 超限后果 |
|---------|------|---------|
| RPM | 每分钟请求数 | 429 Too Many Requests |
| TPM | 每分钟Token数 | 429，但更隐蔽 |
| 并发数 | 同时在处理的请求数 | 429或503 |

关键坑点：**任何一个维度超了都触发429，但你的日志里只看到429，分不清是哪个维度超的。**

真实案例：某团队调GPT-4o做批量文本审核，RPM配额500，TPM配额30000。他们控制每分钟请求不超过400，以为很安全。结果每条Prompt平均3000 Token，400 × 3000 = 120万Token/分钟，远超30000 TPM。429疯狂报错，团队排查了两天才发现是TPM超限，不是RPM。

### 1.2 主流LLM API限流对比（2026年6月）

| 供应商 | 模型 | RPM | TPM | 并发 | 价格（输入/输出，每百万Token） |
|--------|------|-----|-----|------|------|
| OpenAI | gpt-4o | 500（Tier 1） | 30,000 | - | $2.5 / $10 |
| OpenAI | gpt-4o-mini | 500 | 200,000 | - | $0.15 / $0.6 |
| OpenAI | o1 | 500 | 30,000 | - | $15 / $60 |
| OpenAI | gpt-4.5 | 100 | 100,000 | - | $75 / $150 |
| DeepSeek | V4-Pro | - | - | 500 | ¥2 / ¥8（缓存未命中） |
| DeepSeek | V4-Flash | - | - | 2500 | ¥0.1 / ¥0.5 |
| 阿里云百炼 | Qwen-Max | 60 | 60,000 | - | ¥2 / ¥6 |
| 火山引擎 | DeepSeek-V3 | 1000 | 5,000,000 | - | ¥1 / ¥2 |

数据来源：各供应商官方定价页面，2026年6月。OpenAI数据基于Tier 1账户，更高Tier额度不同。火山引擎500万TPM为初始配额，可能是目前全网最高。

**注意**：DeepSeek官方"不设硬性并发上限"，但负载高时动态限流。翻译成人话：没超的时候很宽裕，超了没有明确指标可参考，你只能靠429响应头猜。

### 1.3 TPM才是真正的杀手

为什么说Token维度比请求维度更致命？三个原因：

**原因一：Token消耗不可预测**

调MySQL，一次查询的数据量基本可控。调LLM，一条短Prompt可能50个Token，一条长文档Prompt可能50000个Token，差距1000倍。你根本无法用固定的"每秒N次请求"来建模。

**原因二：输出Token你控制不了**

输入Token你至少能预计算（用tiktoken），输出Token由模型决定。用户问"总结这篇文章"，模型可能输出200 Token；用户问"详细分析每个段落的论证逻辑"，模型可能输出3000 Token。同一个RPM，TPM波动10倍。

**原因三：Streaming不减免限流**

这是个常见误解。Streaming是分块返回，但Token计量方式和非Streaming完全相同。OpenAI按完整输出Token计费和限流，跟是否Stream无关。很多人以为Streaming能"省Token"，其实省的只是用户等待时间。

## 二、传统限流方案在LLM场景下的五个死法

### 2.1 死法一：令牌桶只计请求，不计Token

令牌桶算法的典型实现：每次请求扣1个令牌。但LLM场景下，一条消耗5000 Token的请求和一条消耗50 Token的请求，对TPM配额的占用完全不同。

```python
# 传统令牌桶：只计请求数，LLM场景下必死
class NaiveRateLimiter:
    def __init__(self, max_rpm=500):
        self.max_rpm = max_rpm
        self.requests = []

    def allow(self):
        now = time.time()
        self.requests = [t for t in self.requests if now - t < 60]
        if len(self.requests) < self.max_rpm:
            self.requests.append(now)
            return True
        return False
```

这个限流器对传统API有效，对LLM API无效。它保护了RPM，完全没保护TPM。

**修复：Token-aware限流器**

```python
import tiktoken
from collections import deque
import time

class TokenAwareRateLimiter:
    """同时控制RPM和TPM的限流器"""

    def __init__(self, max_rpm=500, max_tpm=30000, model="gpt-4o"):
        self.max_rpm = max_rpm
        self.max_tpm = max_tpm
        self.enc = tiktoken.encoding_for_model(model)
        # 记录最近60秒内的请求和Token消耗
        self.request_history = deque()  # (timestamp, token_count)
        self.total_tokens = 0

    def _cleanup(self, now):
        """清理60秒窗口外的记录"""
        while self.request_history and now - self.request_history[0][0] > 60:
            _, tokens = self.request_history.popleft()
            self.total_tokens -= tokens

    def estimate_tokens(self, prompt: str, max_output_tokens: int = 1000) -> int:
        """预估本次请求的Token消耗"""
        input_tokens = len(self.enc.encode(prompt))
        return input_tokens + max_output_tokens

    def allow(self, prompt: str, max_output_tokens: int = 1000) -> bool:
        now = time.time()
        self._cleanup(now)

        estimated = self.estimate_tokens(prompt, max_output_tokens)

        # 同时检查RPM和TPM
        rpm_ok = len(self.request_history) < self.max_rpm
        tpm_ok = self.total_tokens + estimated <= self.max_tpm

        if rpm_ok and tpm_ok:
            self.request_history.append((now, estimated))
            self.total_tokens += estimated
            return True
        return False

    def record_actual(self, actual_tokens: int, estimated_tokens: int):
        """请求完成后，用实际Token消耗修正统计"""
        diff = actual_tokens - estimated_tokens
        self.total_tokens += diff
```

关键点：`estimate_tokens`在请求前预估消耗，`record_actual`在请求后修正误差。预估不可能100%准确（输出Token不可预知），但比完全不考虑Token维度强100倍。

### 2.2 死法二：指数退避没加Jitter，雷群效应

指数退避是处理429的标准方案。但多个客户端同时被429后，退避时间序列相同，会同时重试，再次触发429，循环往复。这就是"雷群效应"（Thundering Herd）。

```python
# 错误示范：无Jitter的指数退避
@retry(wait=wait_exponential(multiplier=1, min=4, max=60))
async def call_llm(prompt):
    # 10个客户端同时被429
    # 退避序列都是 4s, 8s, 16s, 32s...
    # 4秒后10个请求同时涌入 → 再次429
    pass
```

**修复：加入随机Jitter**

```python
import random
from tenacity import retry, wait_exponential_jitter, stop_after_attempt
from tenacity import retry_if_exception_type
import openai

client = openai.AsyncOpenAI(api_key="sk-xxx")

@retry(
    wait=wait_exponential_jitter(initial=4, max=60, jitter=8),
    stop=stop_after_attempt(6),
    retry=retry_if_exception_type(openai.RateLimitError),
    reraise=True,
)
async def call_with_jitter(prompt: str) -> str:
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
```

`wait_exponential_jitter`在指数退避基础上叠加0~8秒的随机延迟。10个客户端的退避时间变成4+random秒，打散了重试波峰。

更精细的做法：**解析Retry-After响应头**

```python
import httpx

class SmartRetryClient:
    """解析429响应头中的Retry-After，用服务端建议值作为退避基线"""

    def __init__(self, client: openai.AsyncOpenAI):
        self.client = client
        self.last_retry_after = 0

    async def call(self, prompt: str, max_retries: int = 5) -> str:
        for attempt in range(max_retries):
            try:
                return await self._do_call(prompt)
            except openai.RateLimitError as e:
                # 从响应头提取Retry-After
                retry_after = self._parse_retry_after(e)
                # 指数退避 + Jitter，基线取Retry-After和指数退避的最大值
                base_backoff = min(2 ** attempt, 60)
                effective_wait = max(retry_after, base_backoff)
                jitter = random.uniform(0, effective_wait * 0.3)
                wait_time = effective_wait + jitter

                print(f"429 hit, waiting {wait_time:.1f}s (attempt {attempt+1})")
                await asyncio.sleep(wait_time)
        raise Exception(f"Failed after {max_retries} retries")

    def _parse_retry_after(self, error) -> float:
        """从异常中提取Retry-After秒数"""
        # OpenAI SDK的错误对象可能包含response header
        if hasattr(error, 'response') and error.response:
            headers = error.response.headers
            if 'retry-after' in headers:
                try:
                    return float(headers['retry-after'])
                except (ValueError, TypeError):
                    pass
            # 也检查reset时间
            if 'x-ratelimit-reset' in headers:
                try:
                    reset_ts = float(headers['x-ratelimit-reset'])
                    return max(0, reset_ts - time.time())
                except (ValueError, TypeError):
                    pass
        return 0
```

这比无脑指数退避好在哪？服务端告诉你"1秒后可以重试"，你等1秒。服务端告诉你"60秒后重试"，你不会在第4秒就冲上去送死。

### 2.3 死法三：单Key打天下，配额全浪费

一个API Key的RPM/TPM是固定的。你以为自己有500 RPM，但实际上：

- OpenAI按组织（Organization）分配配额，同组织下所有Key共享
- DeepSeek按账户限流，多Key只增加了认证复杂度，没增加配额
- 火山引擎的500万TPM是按AccessKey分配的，确实可以多Key扩容

**关键区别**：OpenAI多Key不扩容（同一组织共享配额），火山引擎多Key真扩容（每Key独立配额），阿里云百炼按UID限流。

**修复：多Key池 + 智能路由**

```python
from dataclasses import dataclass
from collections import deque
import time
import threading

@dataclass
class KeyState:
    key: str
    rpm_limit: int
    tpm_limit: int
    request_times: deque  # 最近60秒的请求时间戳
    token_usage: deque    # 最近60秒的(timestamp, token_count)

class MultiKeyRouter:
    """多Key智能路由：选剩余配额最多的Key"""

    def __init__(self, keys: list[dict]):
        self.lock = threading.Lock()
        self.key_states = []
        for k in keys:
            self.key_states.append(KeyState(
                key=k["key"],
                rpm_limit=k.get("rpm_limit", 500),
                tpm_limit=k.get("tpm_limit", 30000),
                request_times=deque(),
                token_usage=deque(),
            ))

    def _cleanup(self, state: KeyState, now: float):
        while state.request_times and now - state.request_times[0] > 60:
            state.request_times.popleft()
        while state.token_usage and now - state.token_usage[0][0] > 60:
            _, tokens = state.token_usage.popleft()

    def pick_key(self, estimated_tokens: int = 0) -> str | None:
        """选择剩余配额最充裕的Key"""
        now = time.time()
        with self.lock:
            best_key = None
            best_score = -1

            for state in self.key_states:
                self._cleanup(state, now)

                rpm_remaining = state.rpm_limit - len(state.request_times)
                tpm_remaining = state.tpm_limit - sum(
                    t for _, t in state.token_usage
                )

                # 两个维度都要满足
                if rpm_remaining <= 0 or tpm_remaining < estimated_tokens:
                    continue

                # 评分：取两个维度的最小归一化值（短板效应）
                rpm_ratio = rpm_remaining / state.rpm_limit
                tpm_ratio = tpm_remaining / state.tpm_limit
                score = min(rpm_ratio, tpm_ratio)

                if score > best_score:
                    best_score = score
                    best_key = state

            if best_key is None:
                return None

            # 预占配额
            best_key.request_times.append(now)
            best_key.token_usage.append((now, estimated_tokens))
            return best_key.key
```

这个路由器的核心思路：**永远选剩余配额比例最高的Key**，而不是简单轮询。轮询在Key配额不同时（比如一个Tier 1一个Tier 3）会严重浪费高配额Key。

### 2.4 死法四：重试不区分错误类型

429要重试，401不用重试（Key无效），500可以重试（服务端临时故障），400不该重试（请求参数有问题）。

但很多团队用`try/except Exception`一把梭，所有错误都重试。结果：

- 401错误重试10次 → Key被风控锁定
- 400错误重试10次 → 浪费配额+浪费时间
- 429错误没重试 → 直接抛异常，任务中断

**修复：精确的异常分类处理**

```python
from openai import (
    RateLimitError,      # 429 - 限流，应该重试
    AuthenticationError,  # 401 - 认证失败，不重试
    BadRequestError,      # 400 - 请求参数错，不重试
    APIConnectionError,   # 网络错误，可以重试
    APITimeoutError,      # 超时，可以重试
    InternalServerError,  # 500 - 服务端故障，可以重试
)

RETRYABLE_ERRORS = (
    RateLimitError,
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
)

FATAL_ERRORS = (
    AuthenticationError,
    BadRequestError,
)

@retry(
    wait=wait_exponential_jitter(initial=4, max=120, jitter=8),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(RETRYABLE_ERRORS),
    reraise=True,
)
async def safe_llm_call(prompt: str, client: openai.AsyncOpenAI) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            timeout=30,
        )
        return response.choices[0].message.content
    except FATAL_ERRORS as e:
        # 致命错误：记录日志，立即失败，不重试
        print(f"Fatal error: {type(e).__name__}: {e}")
        raise
```

### 2.5 死法五：没有降级方案，429就是系统崩溃

传统后端调数据库挂了，你有缓存兜底。调LLM API被限流了，你有……什么都没有？

大部分LLM应用的调用链是这样的：

```
用户请求 → 你的后端 → LLM API → 返回结果
```

中间没有缓存，没有降级，没有备用通道。一旦429，整个请求链断裂。

**修复：多级降级策略**

```python
class LLMClientWithFallback:
    """带降级的LLM客户端：模型降级 → 供应商降级 → 缓存兜底"""

    def __init__(self):
        # 模型优先级：强模型 → 轻模型 → 更轻模型
        self.model_tiers = [
            {"model": "gpt-4o", "max_tokens": 4096},
            {"model": "gpt-4o-mini", "max_tokens": 4096},
            {"model": "deepseek-chat", "max_tokens": 4096},
        ]
        # 缓存：相同/相似Prompt的最近结果
        self.cache = TTLCache(maxsize=1000, ttl=3600)
        self.clients = {
            "openai": openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")),
            "deepseek": openai.AsyncOpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com/v1",
            ),
        }

    async def call(self, prompt: str, use_cache: bool = True) -> str:
        # 第一级：缓存命中
        if use_cache:
            cache_key = hashlib.md5(prompt.encode()).hexdigest()
            if cache_key in self.cache:
                return self.cache[cache_key]

        # 第二级：逐级降级模型
        for tier in self.model_tiers:
            try:
                result = await self._call_with_retry(tier["model"], prompt)
                if use_cache:
                    self.cache[cache_key] = result
                return result
            except (RateLimitError, InternalServerError) as e:
                print(f"Model {tier['model']} failed: {e}, falling back...")
                continue

        # 第三级：所有模型都挂了，返回预设降级响应
        return self._degraded_response(prompt)

    def _degraded_response(self, prompt: str) -> str:
        """系统级降级：所有LLM不可用时的兜底"""
        return (
            "抱歉，AI服务暂时繁忙，请稍后重试。"
            "如果问题紧急，请联系人工客服。"
        )
```

降级逻辑说明：
1. **模型降级**：GPT-4o → GPT-4o-mini → DeepSeek-Chat。从贵到便宜，从强到快
2. **供应商降级**：OpenAI挂了切DeepSeek，DeepSeek也挂了切阿里云
3. **缓存兜底**：相同Prompt直接返回历史结果（适合FAQ、模板化生成场景）
4. **优雅失败**：全部不可用时，返回明确的降级提示，而不是500错误

## 三、Token维度的精确限流实现

### 3.1 输入Token预估

输入Token可以在请求前计算，虽然不100%准确（不同分词器结果略有差异），但足够做限流决策。

```python
import tiktoken

class TokenEstimator:
    """Token预估器：支持多模型"""

    ENCODINGS = {
        "gpt-4o": "cl100k_base",
        "gpt-4o-mini": "cl100k_base",
        "gpt-4.5": "o200k_base",
        "deepseek-chat": "cl100k_base",  # 近似
    }

    def __init__(self):
        self._cache = {}

    def estimate_input(self, text: str, model: str = "gpt-4o") -> int:
        encoding_name = self.ENCODINGS.get(model, "cl100k_base")
        if encoding_name not in self._cache:
            self._cache[encoding_name] = tiktoken.get_encoding(encoding_name)
        enc = self._cache[encoding_name]
        return len(enc.encode(text))

    def estimate_total(
        self, prompt: str, model: str = "gpt-4o",
        max_output_tokens: int = 1000
    ) -> int:
        """预估总Token消耗 = 输入 + 最大输出"""
        return self.estimate_input(prompt, model) + max_output_tokens
```

### 3.2 输出Token预算分配

输出Token不可预知，但可以通过`max_tokens`参数设置上限。问题是：很多人设了`max_tokens=4096`，但实际输出只有200 Token。这导致TPM预估偏差巨大。

**动态max_tokens策略**：根据任务类型分配不同的输出Token预算

```python
class TokenBudgetManager:
    """根据任务类型动态分配输出Token预算"""

    # 不同任务的典型输出Token范围
    TASK_PROFILES = {
        "summarize": {"min": 100, "max": 500, "typical": 200},
        "translate": {"min": 200, "max": 2000, "typical": 500},
        "analyze": {"min": 500, "max": 4000, "typical": 1500},
        "code_generate": {"min": 200, "max": 8000, "typical": 2000},
        "chat": {"min": 50, "max": 1000, "typical": 150},
    }

    def get_max_tokens(self, task_type: str, prompt_length: int) -> int:
        profile = self.TASK_PROFILES.get(task_type, self.TASK_PROFILES["chat"])
        # 短Prompt通常意味着简单任务，降低输出预算
        if prompt_length < 500:
            return profile["min"] * 2
        elif prompt_length < 2000:
            return profile["typical"]
        else:
            return profile["max"]

    def get_typical_tokens(self, task_type: str) -> int:
        """返回典型Token消耗，用于TPM预估"""
        profile = self.TASK_PROFILES.get(task_type, self.TASK_PROFILES["chat"])
        return profile["typical"]
```

这样的好处：做摘要任务时，`max_tokens=500`而不是4096，TPM预估准确度提升8倍。

### 3.3 Redis + Lua的分布式Token-aware限流器

单机限流器只适用于单实例部署。生产环境通常多实例，需要分布式限流。

```lua
-- token_limiter.lua
-- KEYS[1]: 限流器key
-- ARGV[1]: RPM上限
-- ARGV[2]: TPM上限
-- ARGV[3]: 当前时间戳(毫秒)
-- ARGV[4]: 预估Token消耗
-- ARGV[5]: 窗口大小(毫秒, 默认60000)

local rpm_key = KEYS[1] .. ":rpm"
local tpm_key = KEYS[1] .. ":tpm"
local now = tonumber(ARGV[3])
local window = tonumber(ARGV[5] or 60000)
local estimated_tokens = tonumber(ARGV[4])

-- 清理过期记录
local function cleanup(zset_key, cutoff)
    redis.call('ZREMRANGEBYSCORE', zset_key, '-inf', cutoff)
end

local cutoff = now - window

-- 检查RPM
cleanup(rpm_key, cutoff)
local rpm_count = redis.call('ZCARD', rpm_key)
if rpm_count >= tonumber(ARGV[1]) then
    return {0, 'RPM_LIMIT', rpm_count}
end

-- 检查TPM
cleanup(tpm_key, cutoff)
local tpm_entries = redis.call('ZRANGE', tpm_key, 0, -1, 'WITHSCORES')
local tpm_total = 0
for i = 2, #tpm_entries, 2 do
    tpm_total = tpm_total + tonumber(tpm_entries[i])
end
if tpm_total + estimated_tokens > tonumber(ARGV[2]) then
    return {0, 'TPM_LIMIT', tpm_total}
end

-- 通过限流，记录请求
redis.call('ZADD', rpm_key, now, now .. ':' .. math.random(1000000))
redis.call('ZADD', tpm_key, now, estimated_tokens)

-- 设置过期时间，自动清理
redis.call('PEXPIRE', rpm_key, window)
redis.call('PEXPIRE', tpm_key, window)

return {1, 'OK', rpm_count + 1}
```

Python调用端：

```python
import redis
import json

class DistributedTokenLimiter:
    def __init__(self, redis_url: str, rpm_limit: int, tpm_limit: int):
        self.redis = redis.from_url(redis_url)
        self.rpm_limit = rpm_limit
        self.tpm_limit = tpm_limit
        with open("token_limiter.lua", "r") as f:
            self.script = self.redis.register_script(f.read())

    def allow(self, key: str, estimated_tokens: int) -> tuple[bool, str]:
        now = int(time.time() * 1000)
        result = self.script(
            keys=[f"ratelimit:{key}"],
            args=[self.rpm_limit, self.tpm_limit, now, estimated_tokens, 60000],
        )
        return bool(result[0]), result[1].decode()
```

## 四、多模型调度：不只是限流，是成本控制

### 4.1 按任务复杂度路由

不是所有请求都需要GPT-4o。简单的分类、提取、翻译用GPT-4o-mini就够了，成本差17倍。

```
GPT-4o: $2.5/$10 每百万Token
GPT-4o-mini: $0.15/$0.6 每百万Token
```

**语义路由器**：根据Prompt内容自动选择模型

```python
class SemanticModelRouter:
    """根据任务复杂度路由到不同模型"""

    # 简单任务的判断规则
    SIMPLE_PATTERNS = [
        r"翻译", r"translate",
        r"总结", r"summarize",
        r"分类", r"classify",
        r"提取", r"extract",
        r"格式化", r"format",
    ]

    MEDIUM_PATTERNS = [
        r"分析", r"analyze",
        r"比较", r"compare",
        r"解释", r"explain",
        r"改写", r"rewrite",
    ]

    def route(self, prompt: str) -> dict:
        prompt_lower = prompt.lower()

        # 简单任务 → 便宜模型
        for pattern in self.SIMPLE_PATTERNS:
            if re.search(pattern, prompt_lower):
                return {
                    "model": "gpt-4o-mini",
                    "max_tokens": 500,
                    "estimated_cost_per_1k": 0.00015,
                }

        # 中等任务 → 中等模型
        for pattern in self.MEDIUM_PATTERNS:
            if re.search(pattern, prompt_lower):
                return {
                    "model": "deepseek-chat",
                    "max_tokens": 2000,
                    "estimated_cost_per_1k": 0.00014,
                }

        # 复杂任务 → 强模型
        return {
            "model": "gpt-4o",
            "max_tokens": 4096,
            "estimated_cost_per_1k": 0.005,
        }
```

效果：一个日均10万次调用的系统，如果60%是简单任务，通过语义路由每月省$5000+。

### 4.2 成本感知的动态降级

不只是"挂了才降级"，而是"快超预算了主动降级"。

```python
class CostAwareLLMClient:
    """成本感知客户端：预算到上限时自动降级模型"""

    def __init__(self, daily_budget_usd: float = 100):
        self.daily_budget = daily_budget_usd
        self.spent = 0
        self.tiers = [
            # (预算比例, 模型, max_tokens)
            (0.6, "gpt-4o", 4096),         # 前60%预算用最强模型
            (0.85, "gpt-4o-mini", 4096),    # 60-85%预算用轻模型
            (1.0, "deepseek-chat", 2000),   # 85-100%预算用最便宜模型
        ]

    def _current_tier(self) -> tuple:
        ratio = self.spent / self.daily_budget
        for threshold, model, max_tokens in self.tiers:
            if ratio < threshold:
                return (model, max_tokens)
        # 超预算：只允许最便宜的模型
        return self.tiers[-1][1], self.tiers[-1][2]

    async def call(self, prompt: str) -> str:
        model, max_tokens = self._current_tier()
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            # 记录实际消耗
            usage = response.usage
            cost = self._calculate_cost(model, usage)
            self.spent += cost
            return response.choices[0].message.content
        except RateLimitError:
            # 被限流时，尝试降级
            return await self._fallback_call(prompt)

    def _calculate_cost(self, model: str, usage) -> float:
        PRICING = {
            "gpt-4o": (2.5 / 1_000_000, 10 / 1_000_000),
            "gpt-4o-mini": (0.15 / 1_000_000, 0.6 / 1_000_000),
            "deepseek-chat": (0.14 / 1_000_000, 0.28 / 1_000_000),
        }
        input_price, output_price = PRICING.get(model, (0, 0))
        return usage.prompt_tokens * input_price + usage.completion_tokens * output_price
```

### 4.3 Batch API：不急的任务别用实时接口

OpenAI和Anthropic都提供Batch API，24小时内返回结果，价格是实时的50%，而且**不占RPM/TPM配额**。

适合场景：
- 批量文本分类
- 数据集标注
- 历史文档摘要
- 内容审核（非实时）

```python
import openai
import json

client = openai.OpenAI()

def submit_batch(tasks: list[dict]) -> str:
    """提交批量任务到Batch API"""

    # 构建批量请求文件
    requests = []
    for i, task in enumerate(tasks):
        requests.append({
            "custom_id": f"task-{i}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": task["prompt"]}],
                "max_tokens": 500,
            }
        })

    # 上传请求文件
    input_file = client.files.create(
        file=json.dumps(requests).encode(),
        purpose="batch"
    )

    # 创建批量任务
    batch = client.batches.create(
        input_file_id=input_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )

    return batch.id

def check_batch(batch_id: str):
    """检查批量任务状态"""
    batch = client.batches.retrieve(batch_id)
    return {
        "status": batch.status,
        "completed": batch.request_counts.completed,
        "failed": batch.request_counts.failed,
        "total": batch.request_counts.total,
    }
```

一个实际的成本对比：1万条文本分类任务，实时API费用约$15，Batch API约$7.5，省了50%。更重要的是不占配额，你的实时接口不会被批量任务挤爆。

## 五、可观测性：限流不能靠猜

### 5.1 必须监控的指标

| 指标 | 含义 | 告警阈值 |
|------|------|---------|
| 429错误率 | 被限流的请求比例 | >5% |
| 平均TTFT | 首Token延迟 | >3s |
| TPM使用率 | Token消耗/配额 | >80% |
| RPM使用率 | 请求消耗/配额 | >80% |
| 模型降级率 | 被迫降级的请求比例 | >10% |
| 缓存命中率 | 缓存兜底的比例 | 监控即可 |

### 5.2 从429响应头提取配额信息

OpenAI的429响应头里藏着金矿，不解析就浪费了：

```
x-ratelimit-limit-requests: 500
x-ratelimit-limit-tokens: 30000
x-ratelimit-remaining-requests: 487
x-ratelimit-remaining-tokens: 24500
x-ratelimit-reset-requests: 45s
x-ratelimit-reset-tokens: 12s
```

`remaining`告诉你还剩多少配额，`reset`告诉你配额什么时候恢复。基于这些数据可以做自适应限流，而不是傻等。

```python
class QuotaAwareClient:
    """解析响应头，自适应调节请求速率"""

    def __init__(self):
        self.remaining_rpm = 500
        self.remaining_tpm = 30000
        self.reset_rpm_at = 0
        self.reset_tpm_at = 0

    def _update_quota(self, response):
        """从响应头更新配额状态"""
        headers = response.headers if hasattr(response, 'headers') else {}

        if 'x-ratelimit-remaining-requests' in headers:
            self.remaining_rpm = int(headers['x-ratelimit-remaining-requests'])
        if 'x-ratelimit-remaining-tokens' in headers:
            self.remaining_tpm = int(headers['x-ratelimit-remaining-tokens'])
        if 'x-ratelimit-reset-requests' in headers:
            self.reset_rpm_at = time.time() + self._parse_duration(
                headers['x-ratelimit-reset-requests']
            )
        if 'x-ratelimit-reset-tokens' in headers:
            self.reset_tpm_at = time.time() + self._parse_duration(
                headers['x-ratelimit-reset-tokens']
            )

    def should_throttle(self) -> bool:
        """是否应该主动降速"""
        # 任一维度剩余配额低于20%，触发主动限流
        rpm_low = self.remaining_rpm < 100
        tpm_low = self.remaining_tpm < 6000
        return rpm_low or tpm_low

    @staticmethod
    def _parse_duration(value: str) -> float:
        """解析类似 '45s' 或 '1200ms' 的时长字符串"""
        value = str(value).strip()
        if value.endswith('ms'):
            return float(value[:-2]) / 1000
        elif value.endswith('s'):
            return float(value[:-1])
        try:
            return float(value)
        except ValueError:
            return 60
```

### 5.3 简易监控方案

不需要Prometheus全家桶，一个简单的统计脚本就能救命：

```python
from collections import deque
from datetime import datetime

class SimpleRateLimitMonitor:
    """轻量级限流监控：每100次调用统计一次"""

    def __init__(self, alert_callback=None):
        self.history = deque(maxlen=1000)
        self.alert_callback = alert_callback or print

    def record(self, success: bool, error_type: str = None, model: str = None):
        self.history.append({
            "time": datetime.now(),
            "success": success,
            "error_type": error_type,
            "model": model,
        })

        # 每100次调用检查一次
        if len(self.history) % 100 == 0:
            self._check_health()

    def _check_health(self):
        recent = list(self.history)[-100:]
        errors = [r for r in recent if not r["success"]]
        error_rate = len(errors) / len(recent)

        if error_rate > 0.05:
            error_types = {}
            for e in errors:
                t = e.get("error_type", "unknown")
                error_types[t] = error_types.get(t, 0) + 1

            self.alert_callback(
                f"⚠️ 限流告警：最近100次调用错误率 {error_rate:.1%}\n"
                f"错误分布：{error_types}"
            )

        # 429错误率单独统计
        rate_limit_errors = [
            r for r in errors if r.get("error_type") == "RateLimitError"
        ]
        if len(rate_limit_errors) > 3:
            self.alert_callback(
                f"🚨 429错误率过高：{len(rate_limit_errors)}/100，"
                f"建议检查限流配置或增加Key"
            )
```

## 六、实战清单：从0到1搭建LLM限流体系

按优先级排序，先做最救命的事：

### 第一步：区分错误类型（1小时）

别再用`except Exception`一把梭。把429、401、500、400分开处理。429重试，401立即失败，500降级。这是投入产出比最高的一步。

### 第二步：Token-aware限流（半天）

用`tiktoken`预估输入Token，`max_tokens`控制输出上限，把RPM和TPM同时纳入限流决策。单机用`deque`滑动窗口，多实例上Redis+Lua。

### 第三步：指数退避+Jitter（1小时）

把`wait_exponential`改成`wait_exponential_jitter`，或者手动解析`Retry-After`响应头。一行代码的事，但能避免雷群效应。

### 第四步：模型降级（半天）

搭一个三层降级链：GPT-4o → GPT-4o-mini → DeepSeek-Chat。根据任务复杂度路由，根据成本预算降级。不急的任务上Batch API。

### 第五步：监控告警（1小时）

统计429错误率、TPM使用率、降级率。错误率>5%就告警，别等到系统全面崩溃才发现。

### 第六步：多Key路由（可选）

日均调用量超过单Key配额的50%时，考虑多Key。注意OpenAI同组织共享配额，需要不同组织的Key才有意义。火山引擎每Key独立配额，扩容最划算。

## 写在最后

传统限流解决的是"请求太多服务器扛不住"的问题。LLM限流解决的是"Token消耗不可预测、成本不可控、多供应商规则不统一"的问题。维度变了，打法也得变。

核心就三件事：
1. **按Token限流，不是按请求**。TPM才是杀手，RPM只是表面。
2. **降级不是失败，是设计**。多模型、多供应商、缓存兜底，每一层都是保险。
3. **可观测性不是可选项**。不监控429错误率的LLM应用，和裸奔没区别。

别等生产环境被429打爆了才想起来加限流。现在就去检查你的代码里是不是还在用`except Exception`。
