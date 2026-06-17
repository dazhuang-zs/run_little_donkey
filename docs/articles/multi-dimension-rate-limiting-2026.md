# 多维度限流实战：用户×资源×时间，三个维度一起限才有意义

单维度限流能解决80%的问题。但生产环境里，真正的麻烦永远来自那20%的交叉场景。

一个免费用户凌晨3点用GPT-4o跑批量任务。单看用户维度，免费用户配额500 Token/天，没超。单看资源维度，GPT-4o模型配额30000 TPM，也没超。单看时间维度，凌晨3点是错峰时段，应该放行。三个维度单独看都没问题，合在一起：免费用户不该在凌晨用最贵的模型跑批量任务，这是你在补贴他。

多维度限流的核心问题：**单一维度永远存在盲区，只有多个维度同时约束，才能既保护系统又保护成本。**

## 一、三个维度各自解决什么问题

先搞清楚每个维度在防御什么，才能知道怎么组合。

### 1.1 用户维度：防御恶意用户和无序用量

用户维度限流的本质是**公平性**和**成本控制**。

公平性：付费用户不应该因为免费用户滥用而变慢。
成本控制：每个用户的用量直接对应你的API账单。

```
免费用户：500 Token/天，每秒最多1个请求
付费用户：50,000 Token/天，每秒最多10个请求
企业用户：500,000 Token/天，每秒最多50个请求
```

但用户维度限流有一个致命盲区：**它不关心用户在调哪个模型。**

一个免费用户调GPT-4o-mini，成本低，可以宽容。同一个免费用户调GPT-4o，成本是前者的17倍，必须限制。用户维度看不到这个区别。

### 1.2 资源维度：防御系统过载和单点故障

资源维度限流的本质是**系统稳定性**。

- GPU显存：KV Cache膨胀导致OOM
- RPM/TPM配额：触碰供应商限流阈值
- 连接池：HTTP连接耗尽

资源维度的问题是：**它不区分用户。**

高优先级用户和低优先级用户共享同一个资源池，一旦资源紧张，所有人一起慢。

### 1.3 时间维度：利用峰谷差异，降低成本

时间维度限流的本质是**成本优化**和**错峰调度**。

典型场景：
- DeepSeek凌晨0:30-8:30降价50%-75%，批量任务应该自动调度到这个时段
- 工作日9:00-18:00是业务高峰，非实时任务排队
- 月末预算快耗尽时，自动降级模型

时间维度的盲区：**它不关心是谁在请求，也不关心请求有多紧急。**

凌晨3点自动调度批量任务，但VIP用户的实时对话也被延迟了，这是错误的。

## 二、多维度组合：真实的决策逻辑

单一维度给你一个布尔值（允许/拒绝）。多维度给你一个**决策树**。

### 2.1 决策树：三个维度同时判断

```
请求进入
  ├── 用户维度检查
  │   ├── 用户不存在/被封禁 → 直接拒绝
  │   ├── 用户配额已耗尽 → 降级模型 or 拒绝
  │   └── 用户配额充足 → 继续
  │
  ├── 资源维度检查
  │   ├── 目标模型TPM已用80% → 进入排队 or 降级
  │   ├── GPU显存不足 → 拒绝 or 切到CPU推理
  │   └── 资源充足 → 继续
  │
  └── 时间维度检查
      ├── 当前是错峰时段 + 请求是非实时的 → 延迟执行
      ├── 当前是高峰时段 + 用户是免费用户 → 限制并发
      └── 时间维度通过 → 执行
```

关键点：**三个维度不是串联的，是有优先级的。**

用户维度优先级最高。一个被封禁的用户，不管资源和时间是啥情况，都应该直接拒绝。资源维度第二。系统都要OOM了，再VIP的用户也得排队。时间维度第三。成本优化是锦上添花，不是生死线。

### 2.2 组合限流的代码实现

```python
from enum import Enum
from dataclasses import dataclass
import time

class UserTier(Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class TaskPriority(Enum):
    REALTIME = "realtime"    # 用户等待的实时对话
    BATCH = "batch"           # 可以延迟的批量任务
    BACKGROUND = "background"  # 后台分析任务

@dataclass
class RateLimitContext:
    """限流决策的上下文：三个维度 + 任务类型"""
    user_id: str
    user_tier: UserTier
    model: str
    task_priority: TaskPriority
    estimated_tokens: int
    current_hour: int  # 0-23

class MultiDimensionRateLimiter:
    """多维度组合限流器"""

    # 用户维度：每日Token配额
    USER_DAILY_QUOTA = {
        UserTier.FREE: 500,
        UserTier.PRO: 50_000,
        UserTier.ENTERPRISE: 500_000,
    }

    # 资源维度：模型TPM配额（简化，实际应该从供应商API动态获取）
    MODEL_TPM_LIMIT = {
        "gpt-4o": 30_000,
        "gpt-4o-mini": 200_000,
        "deepseek-chat": 1_000_000,
    }

    # 时间维度：错峰时段定义
    OFFPEAK_HOURS = range(0, 8)  # 凌晨0点到8点

    def __init__(self):
        self.user_daily_usage = {}  # user_id -> (date, tokens_used)
        self.model_tpm_usage = {}   # model -> deque of (timestamp, tokens)

    def check(self, ctx: RateLimitContext) -> tuple[bool, str, dict]:
        """
        三维度组合检查
        返回：(是否允许, 拒绝原因, 建议操作)
        """
        # 第一维：用户维度
        user_ok, user_reason = self._check_user_quota(ctx)
        if not user_ok:
            return False, user_reason, {"action": "downgrade_model"}

        # 第二维：资源维度
        resource_ok, resource_reason = self._check_resource_quota(ctx)
        if not resource_ok:
            return False, resource_reason, {"action": "queue_or_downgrade"}

        # 第三维：时间维度
        time_action = self._check_time_schedule(ctx)
        if time_action == "defer":
            return False, "非实时任务，建议错峰执行", {"action": "defer", "defer_until": "00:30"}

        return True, "pass", {"action": "execute"}

    def _check_user_quota(self, ctx: RateLimitContext) -> tuple[bool, str]:
        """检查用户维度：日配额 + 速率"""
        quota = self.USER_DAILY_QUOTA[ctx.user_tier]

        # 获取用户今日已用量
        today = time.strftime("%Y-%m-%d")
        usage = self.user_daily_usage.get(ctx.user_id)
        if usage and usage[0] == today:
            used = usage[1]
        else:
            used = 0
            self.user_daily_usage[ctx.user_id] = (today, 0)

        if used + ctx.estimated_tokens > quota:
            return False, f"用户{ctx.user_id}日配额已用尽({used}/{quota})"

        # 记录用量
        self.user_daily_usage[ctx.user_id] = (today, used + ctx.estimated_tokens)
        return True, ""

    def _check_resource_quota(self, ctx: RateLimitContext) -> tuple[bool, str]:
        """检查资源维度：模型TPM"""
        tpm_limit = self.MODEL_TPM_LIMIT.get(ctx.model, 30_000)

        now = time.time()
        if ctx.model not in self.model_tpm_usage:
            self.model_tpm_usage[ctx.model] = []

        usage_deque = self.model_tpm_usage[ctx.model]
        # 清理60秒窗口外的记录
        while usage_deque and now - usage_deque[0][0] > 60:
            usage_deque.popleft()

        current_tpm = sum(t for _, t in usage_deque)
        if current_tpm + ctx.estimated_tokens > tpm_limit:
            return False, f"模型{ctx.model} TPM即将超限({current_tpm}/{tpm_limit})"

        usage_deque.append((now, ctx.estimated_tokens))
        return True, ""

    def _check_time_schedule(self, ctx: RateLimitContext) -> str:
        """
        检查时间维度
        返回：'execute'（立即执行）或 'defer'（建议延迟）
        """
        # 实时任务不管什么时间都立即执行
        if ctx.task_priority == TaskPriority.REALTIME:
            return "execute"

        # 非实时任务，在错峰时段内立即执行（享受低价）
        if ctx.current_hour in self.OFFPEAK_HOURS:
            return "execute"

        # 非实时任务，在高峰时段，建议延迟到错峰时段
        if ctx.task_priority == TaskPriority.BATCH:
            return "defer"

        # 后台任务，高峰时段降低并发
        return "execute"  # 后台任务有单独的并发控制，这里不直接延迟
```

### 2.3 决策结果不是只有"允许"和"拒绝"

传统限流：允许 or 拒绝，二选一。

多维度限流：允许、拒绝、排队、降级、延迟执行，五选一。

```python
class RateLimitDecision(Enum):
    ALLOW = "allow"              # 立即执行
    DENY = "deny"                # 直接拒绝
    QUEUE = "queue"              # 进入等待队列
    DOWNGRADE = "downgrade"      # 降级模型后执行
    DEFER = "defer"              # 延迟到错峰时段

@dataclass
class RateLimitResult:
    decision: RateLimitDecision
    reason: str
    alternative_model: str | None = None
    defer_until: str | None = None
    estimated_wait_seconds: int | None = None
```

这个设计的核心：**拒绝是最后的手段，前面有四层缓冲。**

## 三、用户维度深挖：不只是配额，还有行为模式

### 3.1 用户分级不能只看付费状态

很多团队的用户分级是：免费/付费/VIP，三档。但这不够。

真实生产环境至少需要五档：

| 用户档位 | 判断依据 | 限流策略 |
|---------|---------|---------|
| 新用户（注册<7天） | 注册时间 | 严格限流：500 Token/天，RPM=5 |
| 免费用户 | 未付费 | 基础限流：2000 Token/天，RPM=10 |
| 付费用户 | 已付费，月消费<$50 | 标准限流：50,000 Token/天，RPM=50 |
| VIP用户 | 月消费>$50 或 企业用户 | 宽松限流：500,000 Token/天，RPM=200 |
| 内部用户 | 你的员工/测试账号 | 不限流（但有成本告警） |

**为什么要给新用户最严格的限流？**

两个原因。第一，新注册用户里有一部分是批量注册来刷API额度的黑产。第二，新用户的用量模式还不明确，先给低配额观察7天，没问题再自动升级。

```python
def get_user_tier(user_id: str) -> UserTier:
    """根据用户ID判断用户档位，考虑注册时间和消费记录"""
    user = get_user_info(user_id)

    # 内部用户白名单
    if user_id in INTERNAL_USER_IDS:
        return UserTier.INTERNAL

    # 新用户（注册不到7天）
    if (datetime.now() - user.created_at).days < 7:
        return UserTier.NEW

    # 付费用户分级
    if user.total_paid_usd > 50:
        return UserTier.VIP
    elif user.total_paid_usd > 0:
        return UserTier.PRO

    return UserTier.FREE
```

### 3.2 单用户突发流量检测

用户维度的另一个核心问题：**一个用户突然发大量请求，是正常业务还是被盗号了？**

检测方法：滑动窗口内，如果该用户的请求量超过自身历史均值的3倍，触发风控。

```python
class UserBurstDetector:
    """单用户突发流量检测"""

    def __init__(self, history_window=100, burst_threshold=3.0):
        self.user_history = {}  # user_id -> deque of request timestamps
        self.burst_threshold = burst_threshold  # 超过历史均值3倍视为突发
        self.history_window = history_window

    def check_burst(self, user_id: str) -> tuple[bool, str]:
        now = time.time()

        if user_id not in self.user_history:
            self.user_history[user_id] = deque(maxlen=self.history_window)

        history = self.user_history[user_id]
        history.append(now)

        # 至少需要10条历史记录才能判断
        if len(history) < 10:
            return False, ""

        # 计算最近10分钟内的请求频率
        recent = [t for t in history if now - t < 600]
        avg_rate = len(recent) / 10  # 每分钟请求数

        # 计算历史平均频率（排除最近10分钟，避免自增强）
        older = [t for t in history if 600 < now - t < 3600]
        if not older:
            return False, ""
        hist_rate = len(older) / 50  # 历史50分钟内的平均速率

        if avg_rate > hist_rate * self.burst_threshold:
            return True, (
                f"用户{user_id}突发流量："
                f"当前{avg_rate:.1f}/min，历史均值{hist_rate:.1f}/min"
            )

        return False, ""
```

检测到突发后的处理策略：

1. **先发验证码**：不是直接封，而是下一条请求要求人机验证
2. **降低该用户的配额权重**：把该用户的TPM配额临时降到50%
3. **通知用户**："检测到您的账号有异常流量，请确认是否是本人操作"

### 3.3 用户配额耗尽后的优雅降级

用户配额用完了，直接返回429是最简单的做法。但用户体验很差。

更优雅的做法：**自动降级模型，而不是拒绝。**

```python
MODEL_DOWNGRADE_MAP = {
    "gpt-4o": "gpt-4o-mini",
    "gpt-4o-mini": "deepseek-chat",
    "deepseek-chat": None,  # 最低档，无法再降级
}

def handle_quota_exhausted(
    user_id: str,
    original_model: str,
    prompt: str,
) -> tuple[bool, str, str]:
    """
    用户配额耗尽时的处理
    返回：(是否可以执行, 实际使用的模型, 提示信息)
    """
    user = get_user_info(user_id)

    # 免费用户配额耗尽 → 直接拒绝
    if user.tier == "free":
        return False, "", "今日免费配额已用尽，请明天再试或升级到Pro"

    # 付费用户配额耗尽 → 降级模型
    downgrade_model = MODEL_DOWNGRADE_MAP.get(original_model)
    if downgrade_model is None:
        return False, "", "今日配额已用尽，请明天再试"

    # 记录降级事件（用于后续分析用户真实需求）
    log_quota_downgrade(user_id, original_model, downgrade_model)

    return (
        True,
        downgrade_model,
        f"提示：您的配额已用尽，已自动切换到{downgrade_model}继续服务"
    )
```

关键设计：**降级时要明确告诉用户为什么降级。** 不告诉用户，他会以为你的服务变差了。告诉了，这是教育用户升级的好机会。

## 四、资源维度深挖：GPU显存和成本的双重约束

### 4.1 GPU显存限流：KV Cache是隐形杀手

调用LLM API的人不需要管GPU显存。但如果你是自己部署模型（用vLLM、TGI等推理框架），GPU显存就是你必须面对的问题。

核心问题：**KV Cache显存占用和输出Token数成线性关系。**

```
每生成一个Token，KV Cache增加：
2 × batch_size × num_layers × num_heads × head_dim × sizeof(float16)

以Llama-3-70B为例：
- num_layers = 80
- num_heads = 64
- head_dim = 128
- sizeof(float16) = 2 bytes
- 每Token KV Cache = 2 × 1 × 80 × 64 × 128 × 2 = ~2.6 MB

输出1000个Token → KV Cache占用2.6 GB
并发10个请求，每个输出1000 Token → 26 GB
```

传统限流只看并发数，不看每个请求的预期输出长度，结果就是：**并发数没超，但GPU显存爆了。**

```python
def estimate_kv_cache_bytes(
    model_name: str,
    batch_size: int,
    max_new_tokens: int,
) -> int:
    """预估KV Cache显存占用"""
    MODEL_CONFIGS = {
        "llama-3-70b": {"layers": 80, "heads": 64, "head_dim": 128},
        "llama-3-8b": {"layers": 32, "heads": 32, "head_dim": 128},
        "qwen-72b": {"layers": 80, "heads": 64, "head_dim": 128},
    }
    cfg = MODEL_CONFIGS[model_name]
    per_token_bytes = (
        2 * batch_size * cfg["layers"] * cfg["heads"] * cfg["head_dim"] * 2
    )
    return per_token_bytes * max_new_tokens

class GPUMemoryAwareLimiter:
    """GPU显存感知限流器"""

    def __init__(self, total_gpu_mem_mb: int):
        self.total_gpu_mem = total_gpu_mem_mb
        self.reserved_mem = int(total_gpu_mem_mb * 0.15)  # 预留15%

    def allow_request(
        self,
        model_name: str,
        batch_size: int,
        max_new_tokens: int,
    ) -> tuple[bool, str]:
        kv_bytes = estimate_kv_cache_bytes(model_name, batch_size, max_new_tokens)
        kv_mb = kv_bytes / (1024 * 1024)

        available_mb = self.total_gpu_mem - self.reserved_mem - self._get_current_usage()

        if kv_mb > available_mb:
            return False, (
                f"GPU显存不足：需要{kv_mb:.0f}MB，"
                f"可用{available_mb:.0f}MB。"
                f"建议减少max_new_tokens或降低并发"
            )

        return True, ""

    def _get_current_usage(self) -> int:
        """获取当前GPU显存使用量（MB）"""
        # 实际实现：调用nvidia-smi或vLLM的/metrics接口
        # 这里简化为返回固定值
        return 0
```

### 4.2 成本维度的限流：预算先于限流

很多团队的限流逻辑是：先限流，再看账单，发现超预算了再补救。

正确的做法：**预算是限流的最高优先级约束。**

```python
class BudgetAwareRateLimiter:
    """预算感知限流器：预算耗尽自动降级"""

    def __init__(
        self,
        daily_budget_usd: float,
        model_pricing: dict,  # {"gpt-4o": (2.5, 10), ...}
    ):
        self.daily_budget = daily_budget_usd
        self.spent_today = 0.0
        self.model_pricing = model_pricing
        self._load_spent_from_redis()

    def check_budget(
        self, model: str, estimated_input_tokens: int, estimated_output_tokens: int
    ) -> tuple[bool, str, str]:
        """检查预算，返回(是否允许, 原因, 建议模型)"""
        input_price, output_price = self.model_pricing[model]
        estimated_cost = (
            estimated_input_tokens / 1_000_000 * input_price
            + estimated_output_tokens / 1_000_000 * output_price
        )

        if self.spent_today + estimated_cost > self.daily_budget:
            # 预算不足，找更便宜的模型
            cheaper_model = self._find_cheaper_model(model)
            if cheaper_model:
                return (
                    True,
                    f"预算即将耗尽，自动降级到{cheaper_model}",
                    cheaper_model,
                )
            else:
                return False, "今日预算已用尽，请明天再试", ""

        return True, "", model

    def _find_cheaper_model(self, current_model: str) -> str | None:
        """找比当前模型便宜的替代模型"""
        current_price = sum(self.model_pricing[current_model])
        for model, (inp, out) in sorted(
            self.model_pricing.items(), key=lambda x: sum(x[1])
        ):
            if sum((inp, out)) < current_price:
                return model
        return None

    def record_actual_cost(self, cost: float):
        """记录实际花费"""
        self.spent_today += cost
        # 持久化到Redis
        self._save_spent_to_redis()
```

### 4.3 模型维度的差异化限流

不同模型的TPM/RPM配额不同，不能共用一个限流桶。

```python
MODEL_RATE_LIMITS = {
    "gpt-4o": {"rpm": 500, "tpm": 30_000},
    "gpt-4o-mini": {"rpm": 500, "tpm": 200_000},
    "deepseek-chat": {"rpm": 1000, "tpm": 1_000_000},
    "deepseek-v4-flash": {"rpm": 2500, "tpm": 5_000_000},
}

class ModelAwareRateLimiter:
    """模型维度限流器：每个模型独立限流"""

    def __init__(self):
        self.model_limiters = {}
        for model, limits in MODEL_RATE_LIMITS.items():
            self.model_limiters[model] = {
                "rpm": TokenBucket(limits["rpm"], limits["rpm"]),
                "tpm": TokenBucket(limits["tpm"], limits["tpm"]),
            }

    def allow(self, model: str, estimated_tokens: int) -> bool:
        limiter = self.model_limiters.get(model)
        if not limiter:
            return True  # 未知模型，不限制

        return (
            limiter["rpm"].allow()
            and limiter["tpm"].allow(estimated_tokens)
        )
```

关键点：**GPT-4o-mini的TPM是GPT-4o的6.7倍，两个模型必须独立限流。混在一起，mini的配额会被o拖垮。**

## 五、时间维度深挖：错峰调度和动态配额

### 5.1 DeepSeek错峰定价的时间维度调度

DeepSeek的错峰定价政策（2026年）：
- 北京时间每天0:30-8:30，cache命中降价50%，cache未命中降价75%，cache存储免费
- 非错峰时段，价格恢复正常

这意味着：**同样一个批量任务，凌晨跑比白天跑便宜一半到四分之三。**

```python
from datetime import datetime

class DeepSeekOffpeakScheduler:
    """DeepSeek错峰时段调度器"""

    OFFPEAK_START = (0, 30)  # 0:30
    OFFPEAK_END = (8, 30)    # 8:30

    def should_defer(self, task_type: str, current_time: datetime) -> bool:
        """判断任务是否应该延迟到错峰时段"""
        # 实时对话任务，不管什么时间都立即执行
        if task_type == "realtime":
            return False

        # 当前已经在错峰时段内，立即执行（享受低价）
        if self._is_offpeak(current_time):
            return False

        # 非实时任务，当前在非错峰时段，建议延迟
        return True

    def _is_offpeak(self, dt: datetime) -> bool:
        minutes = dt.hour * 60 + dt.minute
        start_minutes = self.OFFPEAK_START[0] * 60 + self.OFFPEAK_START[1]
        end_minutes = self.OFFPEAK_END[0] * 60 + self.OFFPEAK_END[1]
        return start_minutes <= minutes <= end_minutes

    def get_defer_delay_seconds(self, current_time: datetime) -> int:
        """计算距离错峰时段开始的秒数"""
        current_minutes = current_time.hour * 60 + current_time.minute
        start_minutes = self.OFFPEAK_START[0] * 60 + self.OFFPEAK_START[1]
        if current_minutes < start_minutes:
            return (start_minutes - current_minutes) * 60
        else:
            # 明天凌晨的错峰时段
            return (24 * 60 - current_minutes + start_minutes) * 60
```

### 5.2 工作日vs周末的动态配额

ToB场景和ToC场景的流量模式完全不同。

ToB（企业用户）：工作日9:00-18:00是高峰，周末流量低
ToC（个人用户）：工作日晚上20:00-23:00是高峰，周末全天流量高

动态配额策略：**高峰时段自动收紧免费用户的配额，保障付费用户体验。**

```python
class DynamicQuotaAdjuster:
    """根据时间段动态调整用户配额"""

    # 工作日高峰时段
    PEAK_HOURS_WEEKDAY = list(range(9, 18))
    # ToC高峰时段
    PEAK_HOURS_TOC = [20, 21, 22]

    def get_effective_quota(self, user_tier: str, hour: int, is_weekday: bool) -> int:
        base_quota = self.BASE_QUOTA[user_tier]

        # 付费用户不受时间维度影响
        if user_tier in ("pro", "enterprise"):
            return base_quota

        # 免费用户，在高峰时段配额减半
        is_peak = False
        if is_weekday and hour in self.PEAK_HOURS_WEEKDAY:
            is_peak = True
        if not is_weekday and hour in self.PEAK_HOURS_TOC:
            is_peak = True

        return base_quota // 2 if is_peak else base_quota
```

### 5.3 月末预算保护的动态降级

很多团队的LLM API预算是按月设置的。到月末发现预算快用完了，紧急刹车。

更好的做法：**把月度预算均匀分配到每天，每天动态校准。**

```python
class MonthlyBudgetSmoother:
    """月度预算平滑：避免月末突然耗尽"""

    def __init__(self, monthly_budget: float):
        self.monthly_budget = monthly_budget
        self.daily_budget = monthly_budget / 30

    def get_remaining_daily_budget(self, today_spent: float) -> float:
        return max(0, self.daily_budget - today_spent)

    def get_suggested_model(self, original_model: str, today_spent: float) -> str:
        """根据今日预算消耗建议模型"""
        remaining = self.get_remaining_daily_budget(today_spent)
        if remaining < 1.0:  # 今日预算剩余不足1美元
            return "gpt-4o-mini"  # 强制降级到便宜模型
        elif remaining < 5.0:
            return original_model  # 预算紧张，但还能用原计划
        return original_model
```

## 六、三个维度组合的真实生产案例

### 案例一：AI写作工具的配额体系

某AI写作工具，日活5万，日均LLM调用200万次。他们的多维度限流体系：

**用户维度：**
- 免费用户：每日可生成3篇文章，每篇最多500字
- Pro用户（$9.9/月）：每日100篇，每篇最多2000字
- Team用户（$29/月）：不限篇数，每篇最多5000字

**资源维度：**
- 免费用户只能调gpt-4o-mini，且输出长度强制max_tokens=300
- Pro用户可调用gpt-4o，max_tokens=1000
- Team用户可调用所有模型，max_tokens=2000

**时间维度：**
- 所有用户的实时对话请求立即执行
- AI写作（文章生成）在高峰时段（工作日9:00-12:00, 14:00-18:00）进入排队，最长等待5分钟
- 批量导入文档分析任务，自动调度到凌晨0:30-8:30执行

**效果：**
- 月度LLM成本从$12万降到$3.8万（主要是错峰调度+模型降级）
- 付费用户P99延迟从8.2秒降到1.4秒（主要是高峰时段限制免费用户并发）
- 系统零OOM（主要是KV Cache预估+显存感知限流）

### 案例二：企业AI客服系统的多租户限流

某SaaS客服平台，承载200+企业客户的AI客服机器人。每个客户有自己的API Key，共享推理集群。

**用户维度（租户维度）：**
- Starter套餐：1000次对话/天
- Pro套餐：10000次对话/天
- Enterprise套餐：不限次数，但有TPM上限

**资源维度（模型维度）：**
- 每个租户的TPM配额独立计算
- 推理集群总TPM上限100万，所有租户共享
- 当总TPM使用率超过80%，所有非Enterprise租户降级到轻模型

**时间维度：**
- 每个租户可以设置自己的"营业时间"，非营业时间 incoming 消息进入队列，营业时间开始时批量处理
- 所有租户的批量训练任务（知识库更新）统一在凌晨2:00-6:00执行

**关键踩坑：**

初期所有租户共用一个TPM限流桶，结果某个Starter套餐的客户写了个脚本疯狂调用API（他们的Key泄露了），把整个集群的TPM打满了，所有租户都开始报429。

修复方案：**每个租户独立的TPM限流桶 + 集群总TPM限流桶，双重约束。** 租户级桶保护单个租户不超用，集群级桶保护整体不触碰供应商上限。

```python
class TenantRateLimiter:
    """租户级 + 集群级双重限流"""

    def __init__(self):
        self.tenant_limiters = {}  # tenant_id -> TokenAwareRateLimiter
        self.cluster_limiter = TokenAwareRateLimiter(
            max_tpm=1_000_000,  # 集群总TPM上限
        )

    def allow(self, tenant_id: str, prompt: str) -> tuple[bool, str]:
        # 第一层：租户级限流
        tenant_limiter = self.tenant_limiters.get(tenant_id)
        if tenant_limiter is None:
            return False, f"租户{tenant_id}未配置限流规则"
        tenant_ok, tenant_reason = tenant_limiter.allow(prompt)
        if not tenant_ok:
            return False, tenant_reason

        # 第二层：集群级限流
        cluster_ok, cluster_reason = self.cluster_limiter.allow(prompt)
        if not cluster_ok:
            return False, f"集群资源紧张，请稍后重试：{cluster_reason}"

        return True, "pass"
```

## 七、实战：从0到1搭建多维度限流体系

按优先级排序：

### 第一步：用户维度（1天）

给用户分档：新用户/免费/付费/VIP。每档设置每日Token配额和RPM上限。新用户给最严格的限制。

这一步投入产出比最高。它直接解决"一个用户刷爆你的API账单"的问题。

### 第二步：资源维度 - 模型级限流（半天）

给每个模型配置独立的RPM和TPM限流桶。不要混在一起。

如果你用的是多个供应商（OpenAI + DeepSeek + 阿里云），每个供应商也要独立限流。供应商A的配额用完了，自动切到供应商B。

### 第三步：资源维度 - 成本感知（1天）

把API定价写进配置文件。每次请求前预估成本，累计到日预算里。预算用到80%的时候开始告警，用到100%的时候自动降级模型。

### 第四步：时间维度 - 错峰调度（1天）

识别你的流量模式：ToB还是ToC，高峰时段是什么时候。非实时任务写个延迟执行队列，错峰时段用cron job触发。

如果你在用DeepSeek，直接按他们的错峰定价来调度，成本能降50%以上。

### 第五步：多维度组合（2天）

把前面三个维度串起来，写成一个统一的决策函数。决策优先级：用户维度 > 资源维度 > 时间维度。

同时，给每个维度定义"降级路径"：用户配额耗尽 → 降级模型；资源紧张 → 进入排队；错峰时段外 → 延迟执行。

### 第六步：可观测性（1天）

监控三个维度各自的"拒绝率"：

| 指标 | 含义 | 告警阈值 |
|------|------|---------|
| 用户维度拒绝率 | 配额耗尽导致的拒绝比例 | >10% |
| 资源维度拒绝率 | TPM/RPM超限导致的拒绝比例 | >5% |
| 时间维度延迟率 | 被延迟执行的非实时任务比例 | 监控即可 |
| 降级触发次数 | 自动降级模型的次数 | 按日环比突变告警 |

## 写在最后

单一维度限流是"能跑"。多维度限流是"能跑且跑得久"。

用户维度解决"谁在用"的问题。资源维度解决"用什么"的问题。时间维度解决"什么时候用"的问题。三个维度各自有盲区，合在一起才能覆盖生产环境的复杂场景。

最核心的一句话：**限流不是只有"允许"和"拒绝"两个选项。降级、排队、延迟执行，都是限流策略的一部分。**

把这句话写进你的代码注释里。下次做限流设计的时候，想想除了return 429，你还能做什么。
