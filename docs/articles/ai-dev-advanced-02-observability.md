# AI 开发进阶（第2篇）：AI 系统可观测性——让 Agent 的运行过程"可见、可追、可调试"

> 适合读者：已读完基础9篇 + 第①篇评估体系，想让 Agent 系统可运维、可监控
> 预计阅读时间：35分钟
> 作者：AI小渔村

---

## 前言：Agent 系统需要"仪表盘"

第①篇我们讨论了如何评估 Agent 的质量、安全和成本。但评估是事后的分析，生产环境需要的是**实时监控**：

- 当前有多少请求在处理？
- 每个请求走到哪一步了？
- 哪个 Agent 正在调用什么工具？
- 成本有没有异常飙升？
- 用户反馈怎么样？

**没有可观测性（Observability），Agent 系统就是一个黑盒。**

这篇讲的是：如何给 Agent 系统装上"仪表盘"和"黑匣子"，让运行过程**可见、可追、可调试**。

---

## 一、可观测性的三大支柱

在 Agent 系统中，经典的可观测性三支柱同样适用：

```
┌─────────────────────────────────────────────────┐
│            Agent 可观测性体系                   │
├─────────────────────────────────────────────────┤
│  1. _logs（日志）                              │
│     → 记录系统运行中的关键事件                 │
│     → 问题发生时，能看到"发生了什么"          │
│                                                 │
│  2. _metrics（指标）                            │
│     → 量化系统的运行状态                       │
│     → 实时了解"系统好不好"                   │
│                                                 │
│  3. _traces（链路追踪）                        │
│     → 记录请求的完整调用路径                   │
│     → 问题发生时，能看到"问题出在哪一步"      │
└─────────────────────────────────────────────────┘
```

在 Agent 系统中，还需要额外关注：

- **Token 使用量**（成本监控）
- **工具调用链路**（Agent 特有）
- **模型推理质量**（输出监控）

---

## 二、日志体系设计

### 2.1 日志记录的四个级别

```python
import logging
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
import json

class AgentLogLevel(Enum):
    DEBUG = 10      # 详细调试信息
    INFO = 20       # 一般信息
    WARNING = 30    # 警告
    ERROR = 40      # 错误

class AgentLogger:
    """Agent 系统专用日志器"""
    
    def __init__(self, service_name: str):
        self.logger = logging.getLogger(f"agent.{service_name}")
        self.logger.setLevel(AgentLogLevel.INFO)
        
        # 控制台输出
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        ))
        self.logger.addHandler(handler)
    
    def log_request_start(self, request_id: str, user_id: str, task: str):
        """记录请求开始"""
        self.logger.info(json.dumps({
            "event": "request_start",
            "request_id": request_id,
            "user_id": user_id,
            "task": task[:200],  # 截断避免日志过长
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def log_agent_thinking(self, request_id: str, thought: str, step: int):
        """记录 Agent 思考过程"""
        self.logger.debug(json.dumps({
            "event": "agent_thinking",
            "request_id": request_id,
            "step": step,
            "thought": thought[:500],
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def log_tool_call(self, request_id: str, tool_name: str, 
                      params: Dict[str, Any], result: Any, duration_ms: float):
        """记录工具调用"""
        # 敏感参数脱敏
        safe_params = self._sanitize_params(params)
        
        self.logger.info(json.dumps({
            "event": "tool_call",
            "request_id": request_id,
            "tool_name": tool_name,
            "params": safe_params,
            "success": not isinstance(result, Exception),
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def log_llm_call(self, request_id: str, model: str, 
                     prompt_tokens: int, completion_tokens: int, 
                     latency_ms: float, cost_usd: float):
        """记录 LLM 调用"""
        self.logger.info(json.dumps({
            "event": "llm_call",
            "request_id": request_id,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def log_request_end(self, request_id: str, success: bool, 
                        error: Optional[str] = None, total_cost_usd: float = 0):
        """记录请求结束"""
        self.logger.info(json.dumps({
            "event": "request_end",
            "request_id": request_id,
            "success": success,
            "error": error,
            "total_cost_usd": total_cost_usd,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def _sanitize_params(self, params: Dict) -> Dict:
        """参数脱敏"""
        sensitive_keys = {"api_key", "token", "password", "secret", "credential"}
        return {
            k: "***REDACTED***" if any(s in k.lower() for s in sensitive_keys) else v
            for k, v in params.items()
        }
```

### 2.2 日志最佳实践

1. **每个请求必须有 request_id**——串联所有日志
2. **结构化日志**——用 JSON，方便后续分析
3. **敏感信息必须脱敏**——api_key、token 等
4. **日志级别要合理**——INFO 记录关键事件，DEBUG 记录详细过程

---

## 三、指标监控体系

### 3.1 核心指标定义

```python
from dataclasses import dataclass, field
from typing import List
from collections import defaultdict
import time

@dataclass
class AgentMetrics:
    """Agent 系统核心指标"""
    
    # 请求级指标
    request_count: int = 0
    request_success: int = 0
    request_failed: int = 0
    
    # 延迟指标
    latencies: List[float] = field(default_factory=list)
    
    # 成本指标
    total_tokens: int = 0
    total_cost_usd: float = 0
    
    # 工具调用指标
    tool_calls: int = 0
    tool_errors: int = 0
    
    # LLM 调用指标
    llm_calls: int = 0
    llm_errors: int = 0
    
    def add_request(self, success: bool, latency_ms: float, 
                    tokens: int, cost_usd: float):
        """记录一个请求"""
        self.request_count += 1
        if success:
            self.request_success += 1
        else:
            self.request_failed += 1
        
        self.latencies.append(latency_ms)
        self.total_tokens += tokens
        self.total_cost_usd += cost_usd
    
    def add_tool_call(self, success: bool):
        """记录一次工具调用"""
        self.tool_calls += 1
        if not success:
            self.tool_errors += 1
    
    def add_llm_call(self, success: bool):
        """记录一次 LLM 调用"""
        self.llm_calls += 1
        if not success:
            self.llm_errors += 1
    
    def get_summary(self) -> dict:
        """获取指标汇总"""
        avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0
        
        # P50、P95、P99 延迟
        sorted_latencies = sorted(self.latencies)
        p50 = sorted_latencies[len(sorted_latencies) // 2] if sorted_latencies else 0
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)] if sorted_latencies else 0
        
        return {
            "request": {
                "total": self.request_count,
                "success": self.request_success,
                "failed": self.request_failed,
                "success_rate": self.request_success / max(self.request_count, 1)
            },
            "latency_ms": {
                "avg": round(avg_latency, 2),
                "p50": round(p50, 2),
                "p95": round(p95, 2),
                "p99": round(p99, 2)
            },
            "cost": {
                "total_usd": round(self.total_cost_usd, 4),
                "avg_per_request": round(self.total_cost_usd / max(self.request_count, 1), 4),
                "total_tokens": self.total_tokens
            },
            "tools": {
                "calls": self.tool_calls,
                "errors": self.tool_errors,
                "error_rate": self.tool_errors / max(self.tool_calls, 1)
            },
            "llm": {
                "calls": self.llm_calls,
                "errors": self.llm_errors,
                "error_rate": self.llm_errors / max(self.llm_calls, 1)
            }
        }


class MetricsCollector:
    """指标收集器（支持 Prometheus 格式）"""
    
    def __init__(self):
        self.metrics = AgentMetrics()
        self.by_model: Dict[str, AgentMetrics] = defaultdict(AgentMetrics)
        self.by_tool: Dict[str, AgentMetrics] = defaultdict(AgentMetrics)
    
    def record_request(self, model: str, success: bool, latency_ms: float,
                       tokens: int, cost_usd: float):
        """记录请求指标"""
        self.metrics.add_request(success, latency_ms, tokens, cost_usd)
        self.by_model[model].add_request(success, latency_ms, tokens, cost_usd)
    
    def record_tool_call(self, tool_name: str, success: bool):
        """记录工具调用指标"""
        self.metrics.add_tool_call(success)
        self.by_tool[tool_name].add_tool_call(success)
    
    def export_prometheus(self) -> str:
        """导出 Prometheus 格式"""
        lines = []
        
        # 请求指标
        lines.append(f'agent_requests_total {self.metrics.request_count}')
        lines.append(f'agent_requests_success_total {self.metrics.request_success}')
        lines.append(f'agent_requests_failed_total {self.metrics.request_failed}')
        
        # 成本指标
        lines.append(f'agent_cost_total_usd {self.metrics.total_cost_usd}')
        lines.append(f'agent_tokens_total {self.metrics.total_tokens}')
        
        # 工具指标
        lines.append(f'agent_tool_calls_total {self.metrics.tool_calls}')
        lines.append(f'agent_tool_errors_total {self.metrics.tool_errors}')
        
        return "\n".join(lines)
```

### 3.2 告警规则设计

```python
ALERT_RULES = [
    {
        "name": "error_rate_high",
        "condition": "request_failed / request_total > 0.05",
        "severity": "warning",
        "message": "错误率超过 5%",
        "cooldown_minutes": 5
    },
    {
        "name": "latency_p99_high",
        "condition": "latency_p99 > 10000",  # 10秒
        "severity": "warning",
        "message": "P99 延迟超过 10 秒",
        "cooldown_minutes": 5
    },
    {
        "name": "cost_spike",
        "condition": "cost_last_hour > cost_avg_hour * 3",
        "severity": "critical",
        "message": "成本 hour over hour 增长 3 倍",
        "cooldown_minutes": 15
    },
    {
        "name": "tool_error_rate_high",
        "condition": "tool_errors / tool_calls > 0.1",
        "severity": "warning",
        "message": "工具错误率超过 10%",
        "cooldown_minutes": 5
    }
]

def check_alerts(metrics: AgentMetrics, previous_metrics: AgentMetrics) -> List[dict]:
    """检查告警"""
    alerts = []
    
    # 错误率告警
    error_rate = metrics.request_failed / max(metrics.request_count, 1)
    if error_rate > 0.05:
        alerts.append({
            "rule": "error_rate_high",
            "severity": "warning",
            "message": f"错误率 {error_rate:.1%} 超过 5%"
        })
    
    # 延迟告警
    if metrics.latencies:
        p99 = sorted(metrics.latencies)[int(len(metrics.latencies) * 0.99)]
        if p99 > 10000:
            alerts.append({
                "rule": "latency_p99_high",
                "severity": "warning",
                "message": f"P99 延迟 {p99/1000:.1f}s 超过 10s"
            })
    
    return alerts
```

---

## 四、链路追踪实战

### 4.1 为什么需要链路追踪？

在 Agent 系统中，一个请求可能经历：

```
用户请求
  ↓
[Agent] 思考 → 决定调用工具
  ↓
[Tool: 搜索] → 返回结果
  ↓
[Agent] 思考 → 决定再调用工具
  ↓
[Tool: 数据库] → 返回结果
  ↓
[Agent] 生成最终回答
```

这个链条中，哪一步慢了？哪一步出错了？

**没有链路追踪，你只能看到最终失败，不知道问题出在哪一步。**

### 4.2 用 OpenTelemetry 实现链路追踪

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# 初始化追踪
trace.set_tracer_provider(TracerProvider(
    resource=Resource.create({
        "service.name": "agent-service",
        "service.version": "2.1.0"
    })
))

# 导出到 Jaeger / Tempo / 其他 OTLP 兼容后端
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="localhost:4317"))
)

tracer = trace.get_tracer(__name__)


class TracingAgent:
    """带链路追踪的 Agent"""
    
    def __init__(self, agent, logger: AgentLogger):
        self.agent = agent
        self.logger = logger
    
    async def run(self, task: str, request_id: str) -> str:
        """执行请求，带完整链路追踪"""
        
        with tracer.start_as_current_span(request_id) as span:
            # 设置基础属性
            span.set_attribute("request.id", request_id)
            span.set_attribute("task.preview", task[:100])
            
            try:
                # Step 1: Agent 思考
                with tracer.start_as_current_span("agent_think") as think_span:
                    think_span.set_attribute("step", 1)
                    thought = await self.agent.think(task)
                    span.add_event("thought_completed", {"step": 1})
                
                # Step 2: 工具调用循环
                tool_calls = []
                max_tools = 10
                for i in range(max_tools):
                    # 决定是否需要调用工具
                    should_call, tool_name, params = await self.agent.decide_tool(thought)
                    
                    if not should_call:
                        break
                    
                    # 追踪工具调用
                    with tracer.start_as_current_span(f"tool.{tool_name}") as tool_span:
                        tool_span.set_attribute("tool.name", tool_name)
                        tool_span.set_attribute("tool.step", i + 1)
                        
                        start = time.time()
                        try:
                            result = await self.agent.call_tool(tool_name, params)
                            tool_span.set_attribute("tool.success", True)
                            tool_calls.append({"tool": tool_name, "success": True})
                        except Exception as e:
                            tool_span.set_attribute("tool.success", False)
                            tool_span.set_attribute("tool.error", str(e))
                            tool_calls.append({"tool": tool_name, "success": False, "error": str(e)})
                        
                        tool_span.set_attribute("tool.duration_ms", (time.time() - start) * 1000)
                    
                    # 记录到日志
                    self.logger.log_tool_call(request_id, tool_name, params, 
                                              result, (time.time() - start) * 1000)
                    
                    # 更新思考上下文
                    thought += f"\n[工具返回]: {result}"
                
                # Step 3: 生成回答
                with tracer.start_as_current_span("generate_answer") as gen_span:
                    answer = await self.agent.generate(thought)
                
                # 标记成功
                span.set_attribute("request.success", True)
                span.set_attribute("tool.call_count", len(tool_calls))
                
                return answer
                
            except Exception as e:
                # 标记失败
                span.set_attribute("request.success", False)
                span.set_attribute("request.error", str(e))
                span.record_exception(e)
                raise
```

### 4.3 链路可视化

链路追踪的数据可以导入 **Jaeger**、**Tempo**、**Zipkin** 等工具进行可视化：

- 每个请求的完整调用链
- 每一步的耗时（毫秒级）
- 哪里有错误（红色高亮）
- 工具调用的输入输出

---

## 五、实战：LangSmith / Helicone 使用

### 5.1 LangSmith（OpenAI 官方）

```python
from langsmith import Client

# 初始化
client = Client()

# 创建数据集
dataset = client.create_dataset(
    dataset_name="agent-eval-dataset",
    description="Agent 评估测试集"
)

# 添加示例
client.create_examples(
    dataset_id=dataset.id,
    inputs=[
        {"task": "帮我查一下北京明天天气"},
        {"task": "总结一下这个文档的主要内容"}
    ],
    outputs=[
        {"expected": "北京明天晴转多云，15-25度"},
        {"expected": "文档主要讨论了..."}
    ]
)

# 追踪运行
@client.traceable
def my_agent(task: str):
    # 你的 Agent 逻辑
    ...

# 运行评估
experiment = client.run_on_dataset(
    dataset_name="agent-eval-dataset",
    llm_or_chain_factory=my_agent,
    evaluation_metrics=["correctness", "helpfulness"]
)
```

### 5.2 Helicone（更轻量）

```python
import openai
from helicone import Helicone

# 初始化 Helicone
Helicone.configure(api_key="your-helicone-key")

# OpenAI 请求自动被追踪
openai.api_base = "https://oai.helicone.ai/v1"
openai.api_key = "your-openai-key"

# 请求自动记录到 Helicone 控制台
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

---

## 六、总结：可观测性建设路线图

```
阶段1：日志输出（现在）
  ↓   用结构化 JSON 日志记录关键事件
阶段2：指标收集（下周）
  ↓   统计请求量、延迟、成本、错误率
阶段3：链路追踪（下个月）
  ↓   用 OpenTelemetry 追踪完整调用链
阶段4：告警监控（3个月后）
  ↓   设置告警规则，及时发现问题
阶段5：自助分析（半年后）
  → 用日志/指标/追踪数据做根因分析
```

**核心思想**：可观测性是 Agent 系统从 Demo 走向生产的必备能力。

没有可观测性，Agent 就是一个黑盒——出了问题只能猜。
有了可观测性，你才能真正"看到"Agent 在做什么。

---

## 踩坑经验汇总

1. **每个请求必须有 request_id**——串联日志、指标、追踪的基石
2. **日志要结构化**——用 JSON，方便后续查询和分析
3. **敏感信息必须脱敏**——api_key、token 等绝对不能明文记录
4. **指标要算 P50/P95/P99**——平均值会掩盖问题
5. **告警要有冷却时间**——避免一条错误刷屏

---

**本篇代码**：https://github.com/dazhuang-zs/run_little_donkey/blob/master/docs/articles/ai-dev-advanced-02-observability.md

**篇③预告**：推理加速与成本控制——从 API 到自部署，讲 vLLM 部署、量化、KV Cache 复用、模型路由。