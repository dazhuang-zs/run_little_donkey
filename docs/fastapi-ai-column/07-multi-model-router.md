# FastAPI搭多模型路由：自动切换DeepSeek/Qwen/GPT

> **文章信息**
> - 标题：FastAPI搭多模型路由：自动切换DeepSeek/Qwen/GPT
> - 字数：4000字
> - 预估阅读时间：18分钟
> - 难度：⭐⭐⭐⭐☆

---

## 一、为什么需要多模型路由

2025年，大模型已经不是"选择一个"的问题。企业级AI应用通常需要同时接入多个模型，原因很实际：

1. **成本优化**：DeepSeek-V3输入$0.27/M tokens，GPT-4o输入$2.50/M tokens，日常对话用DeepSeek，复杂推理才切GPT-4o
2. **能力分层**：简单问答 → Qwen-Turbo，快要失败 → DeepSeek-R1，复杂推理 → GPT-4o
3. **容错兜底**：某个模型API临时不可用时自动降级到备选，不影响服务
4. **合规需求**：境内数据走通义/Qwen，出境数据走DeepSeek或GPT

本文用FastAPI构建一套完整的多模型路由系统，支持自动路由、成本控制、降级熔断、负载均衡。

## 二、多模型价格与能力对比

2025年5月各模型官方定价（来源：各厂商官网）：

| 模型 | 输入价格（$/M） | 输出价格（$/M） | 上下文 | 优势场景 | 延迟参考 |
|------|----------------|----------------|--------|----------|----------|
| DeepSeek-V3 | 0.27 | 1.10 | 64K | 日常对话、代码生成 | ~500ms |
| DeepSeek-R1 | 0.55 | 2.19 | 64K | 复杂推理、思维链 | ~1200ms |
| Qwen-Turbo | 0.50 | 2.00 | 128K | 国内合规、快速响应 | ~300ms |
| Qwen-Max | 2.00 | 6.00 | 32K | 复杂推理、高质量生成 | ~800ms |
| GPT-4o | 2.50 | 10.00 | 128K | 复杂推理、多模态 | ~1000ms |
| GPT-4o-mini | 0.15 | 0.60 | 128K | 简单任务、低成本 | ~400ms |

**路由策略建议**：
- **成本优先**：DeepSeek-V3（日常）→ GPT-4o-mini（降级）→ GPT-4o（兜底）
- **速度优先**：Qwen-Turbo（国内）→ DeepSeek-V3 → GPT-4o-mini
- **质量优先**：GPT-4o（复杂推理）→ DeepSeek-R1 → Claude-3.5

## 三、项目结构

```
fastapi-multi-model-router/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── model_registry.py      # 模型注册表
│   │   ├── router.py             # 路由核心逻辑
│   │   ├── fallback.py           # 降级熔断器
│   │   └── load_balancer.py      # 负载均衡
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py               # Provider基类
│   │   ├── deepseek.py           # DeepSeek Provider
│   │   ├── qwen.py               # 阿里通义 Provider
│   │   └── openai.py             # OpenAI/GPT Provider
│   ├── routes/
│   │   ├── __init__.py
│   │   └── chat.py               # 聊天路由
│   └── middleware/
│       ├── __init__.py
│       └── rate_limiter.py       # 模型级限流
├── config/
│   └── models.yaml               # 模型配置
├── tests/
│   └── test_router.py
├── .env
└── requirements.txt
```

## 四、模型配置（YAML）

```yaml
# config/models.yaml

models:
  # DeepSeek系列
  deepseek-chat:
    provider: deepseek
    model_name: deepseek-chat
    display_name: "DeepSeek V3"
    api_base: "https://api.deepseek.com"
    api_key_env: DEEPSEEK_API_KEY
    input_price: 0.27    # $/M tokens
    output_price: 1.10
    max_tokens: 4096
    context_window: 64000
    latency_p50: 500     # ms
    capabilities:
      - chat
      - function_call
      - vision
    tier: cheap
    region: auto

  deepseek-reasoner:
    provider: deepseek
    model_name: deepseek-reasoner
    display_name: "DeepSeek R1"
    api_base: "https://api.deepseek.com"
    api_key_env: DEEPSEEK_API_KEY
    input_price: 0.55
    output_price: 2.19
    max_tokens: 8192
    context_window: 64000
    latency_p50: 1200
    capabilities:
      - chat
      - reasoning
      - chain_of_thought
    tier: reasoning
    region: auto

  # 阿里通义系列
  qwen-turbo:
    provider: qwen
    model_name: qwen-turbo
    display_name: "通义千问 Turbo"
    api_base: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    api_key_env: DASHSCOPE_API_KEY
    input_price: 0.50
    output_price: 2.00
    max_tokens: 8192
    context_window: 128000
    latency_p50: 300
    capabilities:
      - chat
      - function_call
    tier: fast
    region: cn

  qwen-max:
    provider: qwen
    model_name: qwen-max
    display_name: "通义千问 Max"
    api_base: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    api_key_env: DASHSCOPE_API_KEY
    input_price: 2.00
    output_price: 6.00
    max_tokens: 8192
    context_window: 32000
    latency_p50: 800
    capabilities:
      - chat
      - advanced_reasoning
    tier: premium
    region: cn

  # OpenAI系列
  gpt-4o-mini:
    provider: openai
    model_name: gpt-4o-mini
    display_name: "GPT-4o Mini"
    api_base: "https://api.openai.com/v1"
    api_key_env: OPENAI_API_KEY
    input_price: 0.15
    output_price: 0.60
    max_tokens: 16384
    context_window: 128000
    latency_p50: 400
    capabilities:
      - chat
      - function_call
      - vision
    tier: cheap
    region: us

  gpt-4o:
    provider: openai
    model_name: gpt-4o
    display_name: "GPT-4o"
    api_base: "https://api.openai.com/v1"
    api_key_env: OPENAI_API_KEY
    input_price: 2.50
    output_price: 10.00
    max_tokens: 16384
    context_window: 128000
    latency_p50: 1000
    capabilities:
      - chat
      - function_call
      - vision
      - advanced_reasoning
    tier: premium
    region: us

# 路由策略配置
routing:
  default_strategy: cost_optimized
  strategies:
    cost_optimized:
      order:
        - deepseek-chat      # 首选，便宜
        - gpt-4o-mini        # 降级1
        - qwen-turbo         # 降级2
        - gpt-4o             # 兜底
      fallback_cooldown: 300   # 模型失败后5分钟不再路由
    
    speed_priority:
      order:
        - qwen-turbo
        - deepseek-chat
        - gpt-4o-mini
    
    quality_priority:
      order:
        - gpt-4o
        - deepseek-reasoner
        - qwen-max

# 限流配置（每分钟请求数）
rate_limits:
  deepseek-chat: 60
  deepseek-reasoner: 30
  qwen-turbo: 60
  gpt-4o-mini: 60
  gpt-4o: 20
```

## 五、配置加载

```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
import yaml

class ModelConfig(BaseSettings):
    model_name: str
    display_name: str
    provider: str
    api_base: str
    api_key_env: str
    input_price: float
    output_price: float
    max_tokens: int
    context_window: int
    latency_p50: int
    capabilities: list[str]
    tier: str
    region: str

class RoutingConfig(BaseSettings):
    default_strategy: str
    fallback_cooldown: int

class Settings(BaseSettings):
    class Config:
        env_file = ".env"

def load_model_configs() -> dict[str, ModelConfig]:
    """加载YAML模型配置"""
    config_path = Path(__file__).parent.parent / "config" / "models.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    
    models = {}
    for name, cfg in raw["models"].items():
        models[name] = ModelConfig(model_name=name, **cfg)
    
    return models, RoutingConfig(**raw["routing"])

@lru_cache
def get_model_configs() -> tuple[dict[str, ModelConfig], RoutingConfig]:
    return load_model_configs()
```

## 六、Provider基类与实现

```python
# app/providers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

@dataclass
class ModelResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    finish_reason: str = "stop"
    error: str | None = None

@dataclass
class ChatMessage:
    role: Literal["system", "user", "assistant"]
    content: str

class BaseModelProvider(ABC):
    """模型Provider基类"""
    
    def __init__(self, api_key: str, api_base: str, model_name: str):
        self.api_key = api_key
        self.api_base = api_base
        self.model_name = model_name
    
    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ModelResponse:
        """发送聊天请求"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
```

```python
# app/providers/deepseek.py
import httpx
import os
import time
from app.providers.base import BaseModelProvider, ModelResponse, ChatMessage

class DeepSeekProvider(BaseModelProvider):
    """DeepSeek模型Provider"""
    
    def __init__(self, model_name: str = "deepseek-chat"):
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        super().__init__(
            api_key=api_key,
            api_base="https://api.deepseek.com",
            model_name=model_name,
        )
    
    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ModelResponse:
        start = time.perf_counter()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens or 2048,
                    **kwargs,
                },
            )
            
            data = response.json()
            latency_ms = int((time.perf_counter() - start) * 1000)
            
            if response.status_code != 200:
                return ModelResponse(
                    content="",
                    model=self.model_name,
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=latency_ms,
                    error=data.get("error", {}).get("message", "Unknown error"),
                )
            
            usage = data.get("usage", {})
            return ModelResponse(
                content=data["choices"][0]["message"]["content"],
                model=self.model_name,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                latency_ms=latency_ms,
                finish_reason=data["choices"][0].get("finish_reason", "stop"),
            )
    
    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model_name,
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 5,
                    },
                )
                return r.status_code == 200
        except Exception:
            return False
```

```python
# app/providers/qwen.py
import httpx
import os
import time
from app.providers.base import BaseModelProvider, ModelResponse, ChatMessage

class QwenProvider(BaseModelProvider):
    """阿里通义千问Provider"""
    
    def __init__(self, model_name: str = "qwen-turbo"):
        api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        super().__init__(
            api_key=api_key,
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model_name=model_name,
        )
    
    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ModelResponse:
        start = time.perf_counter()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens or 2048,
                },
            )
            
            data = response.json()
            latency_ms = int((time.perf_counter() - start) * 1000)
            
            if response.status_code != 200:
                return ModelResponse(
                    content="",
                    model=self.model_name,
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=latency_ms,
                    error=str(data),
                )
            
            usage = data.get("usage", {})
            return ModelResponse(
                content=data["choices"][0]["message"]["content"],
                model=self.model_name,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                latency_ms=latency_ms,
                finish_reason=data["choices"][0].get("finish_reason", "stop"),
            )
    
    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model_name,
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 5,
                    },
                )
                return r.status_code == 200
        except Exception:
            return False
```

```python
# app/providers/openai.py
import httpx
import os
import time
from app.providers.base import BaseModelProvider, ModelResponse, ChatMessage

class OpenAIProvider(BaseModelProvider):
    """OpenAI/GPT Provider"""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        api_key = os.environ.get("OPENAI_API_KEY", "")
        super().__init__(
            api_key=api_key,
            api_base="https://api.openai.com/v1",
            model_name=model_name,
        )
    
    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ModelResponse:
        start = time.perf_counter()
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens or 2048,
                },
            )
            
            data = response.json()
            latency_ms = int((time.perf_counter() - start) * 1000)
            
            if response.status_code != 200:
                return ModelResponse(
                    content="",
                    model=self.model_name,
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=latency_ms,
                    error=data.get("error", {}).get("message", "Unknown error"),
                )
            
            usage = data.get("usage", {})
            return ModelResponse(
                content=data["choices"][0]["message"]["content"],
                model=self.model_name,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                latency_ms=latency_ms,
                finish_reason=data["choices"][0].get("finish_reason", "stop"),
            )
    
    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model_name,
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 5,
                    },
                )
                return r.status_code == 200
        except Exception:
            return False
```

## 七、模型注册表与路由核心

```python
# app/core/model_registry.py
from app.providers.base import BaseModelProvider, ModelResponse, ChatMessage
from app.providers.deepseek import DeepSeekProvider
from app.providers.qwen import QwenProvider
from app.providers.openai import OpenAIProvider
from app.config import get_model_configs
from functools import lru_cache
from typing import Literal

class ModelRegistry:
    """全局模型注册表"""
    
    _providers: dict[str, BaseModelProvider] = {}
    _configs: dict = {}
    
    @classmethod
    def init(cls):
        """初始化所有Provider"""
        cls._configs, routing_cfg = get_model_configs()
        
        cls._providers["deepseek-chat"] = DeepSeekProvider("deepseek-chat")
        cls._providers["deepseek-reasoner"] = DeepSeekProvider("deepseek-reasoner")
        cls._providers["qwen-turbo"] = QwenProvider("qwen-turbo")
        cls._providers["qwen-max"] = QwenProvider("qwen-max")
        cls._providers["gpt-4o-mini"] = OpenAIProvider("gpt-4o-mini")
        cls._providers["gpt-4o"] = OpenAIProvider("gpt-4o")
    
    @classmethod
    def get_provider(cls, model_name: str) -> BaseModelProvider | None:
        return cls._providers.get(model_name)
    
    @classmethod
    def list_models(cls) -> list[dict]:
        return [
            {
                "name": name,
                "display_name": cfg.display_name,
                "tier": cfg.tier,
                "region": cfg.region,
                "latency_p50": cfg.latency_p50,
            }
            for name, cfg in cls._configs.items()
        ]

# 全局初始化
ModelRegistry.init()
```

## 八、路由核心逻辑

```python
# app/core/router.py
from app.core.model_registry import ModelRegistry
from app.providers.base import ModelResponse, ChatMessage
from app.config import get_model_configs
from dataclasses import dataclass, field
import asyncio
import time
from typing import Literal

@dataclass
class RoutingDecision:
    selected_model: str
    strategy: str
    fallback_chain: list[str]
    cost_estimate: float | None = None

class FallbackState:
    """熔断状态记录"""
    def __init__(self, cooldown: int = 300):
        self._failed_models: dict[str, float] = {}
        self._cooldown = cooldown
    
    def mark_failed(self, model: str) -> None:
        self._failed_models[model] = time.time()
    
    def is_cooling(self, model: str) -> bool:
        if model not in self._failed_models:
            return False
        elapsed = time.time() - self._failed_models[model]
        return elapsed < self._cooldown
    
    def clear_model(self, model: str) -> None:
        self._failed_models.pop(model, None)

class MultiModelRouter:
    """多模型路由核心"""
    
    def __init__(self, strategy: str = "cost_optimized"):
        self._configs, routing_cfg = get_model_configs()
        self._fallback_state = FallbackState(
            cooldown=routing_cfg.fallback_cooldown
        )
        self._strategy = strategy
        self._strategy_order = routing_cfg.strategies[strategy].order
    
    async def route_and_chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        force_model: str | None = None,
    ) -> tuple[ModelResponse, RoutingDecision]:
        """
        路由选择并执行chat，自动降级
        返回：(响应, 路由决策)
        """
        if force_model:
            chain = [force_model]
        else:
            # 过滤掉正在冷却的模型
            chain = [
                m for m in self._strategy_order
                if not self._fallback_state.is_cooling(m)
            ]
        
        if not chain:
            # 所有模型都在冷却，强制使用第一个
            chain = [self._strategy_order[0]]
        
        last_error = None
        for model_name in chain:
            provider = ModelRegistry.get_provider(model_name)
            if not provider:
                continue
            
            try:
                # 先健康检查
                if not await provider.health_check():
                    self._fallback_state.mark_failed(model_name)
                    continue
                
                response = await provider.chat(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                
                if response.error:
                    self._fallback_state.mark_failed(model_name)
                    last_error = response.error
                    continue
                
                decision = RoutingDecision(
                    selected_model=model_name,
                    strategy=self._strategy,
                    fallback_chain=chain,
                    cost_estimate=self._estimate_cost(response, model_name),
                )
                return response, decision
            
            except Exception as e:
                self._fallback_state.mark_failed(model_name)
                last_error = str(e)
                continue
        
        # 所有模型都失败了
        return ModelResponse(
            content="",
            model="",
            input_tokens=0,
            output_tokens=0,
            latency_ms=0,
            error=f"All models failed. Last error: {last_error}",
        ), RoutingDecision(
            selected_model="none",
            strategy=self._strategy,
            fallback_chain=chain,
        )
    
    def _estimate_cost(self, response: ModelResponse, model_name: str) -> float:
        cfg = self._configs.get(model_name)
        if not cfg:
            return 0.0
        input_cost = response.input_tokens / 1_000_000 * cfg.input_price
        output_cost = response.output_tokens / 1_000_000 * cfg.output_price
        return round(input_cost + output_cost, 6)
```

## 九、FastAPI路由

```python
# app/models.py
from pydantic import BaseModel, Field
from typing import Literal, Optional

class MessageInput(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    messages: list[MessageInput] = Field(min_length=1)
    model: Optional[str] = Field(default=None, description="指定模型，为空则自动路由")
    strategy: Literal["cost_optimized", "speed_priority", "quality_priority"] = "cost_optimized"
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=100, le=16384)

class RoutingInfo(BaseModel):
    selected_model: str
    strategy: str
    fallback_chain: list[str]
    cost_estimate_usd: Optional[float]

class UsageInfo(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: int
    cost_usd: Optional[float]

class ChatResponse(BaseModel):
    content: str
    finish_reason: str
    model: str
    routing: RoutingInfo
    usage: UsageInfo
    error: Optional[str] = None

class ModelListResponse(BaseModel):
    models: list[dict]
```

```python
# app/routes/chat.py
from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse, RoutingInfo, UsageInfo, ModelListResponse
from app.core.router import MultiModelRouter
from app.core.model_registry import ModelRegistry
from app.providers.base import ChatMessage
from app.config import get_model_configs

router = APIRouter(prefix="/chat", tags=["多模型路由"])

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """多模型路由聊天，支持自动降级"""
    try:
        router_instance = MultiModelRouter(strategy=request.strategy)
        
        # 转换为Provider格式
        messages = [
            ChatMessage(role=m.role, content=m.content)
            for m in request.messages
        ]
        
        response, decision = await router_instance.route_and_chat(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            force_model=request.model,
        )
        
        if response.error and not response.content:
            raise HTTPException(status_code=502, detail=f"所有模型均不可用: {response.error}")
        
        # 计算费用
        configs, _ = get_model_configs()
        cfg = configs.get(response.model)
        cost_usd = None
        if cfg and response.input_tokens > 0:
            input_cost = response.input_tokens / 1_000_000 * cfg.input_price
            output_cost = response.output_tokens / 1_000_000 * cfg.output_price
            cost_usd = round(input_cost + output_cost, 6)
        
        return ChatResponse(
            content=response.content,
            finish_reason=response.finish_reason,
            model=response.model,
            routing=RoutingInfo(
                selected_model=decision.selected_model,
                strategy=decision.strategy,
                fallback_chain=decision.fallback_chain,
                cost_estimate_usd=decision.cost_estimate,
            ),
            usage=UsageInfo(
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                total_tokens=response.input_tokens + response.output_tokens,
                latency_ms=response.latency_ms,
                cost_usd=cost_usd,
            ),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models", response_model=ModelListResponse)
async def list_models():
    """列出所有可用模型"""
    return ModelListResponse(models=ModelRegistry.list_models())
```

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat

app = FastAPI(title="多模型路由API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

## 十、负载均衡（轮询+加权）

```python
# app/core/load_balancer.py
from collections import deque
from dataclasses import dataclass
import threading

@dataclass
class LoadStats:
    requests: int = 0
    errors: int = 0
    avg_latency_ms: float = 0.0
    total_latency_ms: float = 0.0

class LoadBalancer:
    """带权重的轮询负载均衡"""
    
    def __init__(self, models: list[str]):
        self._models = models
        self._index = 0
        self._lock = threading.Lock()
        self._stats: dict[str, LoadStats] = {
            m: LoadStats() for m in models
        }
    
    def select(self) -> str:
        """选择一个模型（轮询）"""
        with self._lock:
            model = self._models[self._index]
            self._index = (self._index + 1) % len(self._models)
            return model
    
    def record_request(self, model: str, latency_ms: int, error: bool = False) -> None:
        """记录请求结果"""
        with self._lock:
            stat = self._stats[model]
            stat.requests += 1
            stat.total_latency_ms += latency_ms
            if error:
                stat.errors += 1
            stat.avg_latency_ms = stat.total_latency_ms / stat.requests
    
    def get_stats(self) -> dict:
        return {
            model: {
                "requests": stat.requests,
                "errors": stat.errors,
                "avg_latency_ms": round(stat.avg_latency_ms, 1),
                "error_rate": round(stat.errors / stat.requests, 3) if stat.requests else 0,
            }
            for model, stat in self._stats.items()
        }
```

## 十一、踩坑记录总结

| 坑 | 现象 | 解决方案 |
|----|------|----------|
| API Key为空导致静默失败 | 模型返回空content但error字段也为空 | 在Provider中先检查API Key是否为空 |
| 降级循环 | 模型A失败→B，B失败→A来回切换 | 加fallback_cooldown冷却时间 |
| DeepSeek和Qwen的Message格式不同 | 格式不兼容时返回400 | 用统一的ChatMessage dataclass做转换 |
| 费用估算不准确 | 账单金额与估算差太多 | 用实际usage字段，不依赖max_tokens估算 |
| 国内访问OpenAI超时 | GPT请求超时 | 设置合理的timeout（60-120s），超时则降级 |
| 路由决策无记录 | 不知道哪个模型回答了问题 | 返回RoutingInfo，包含selected_model和fallback_chain |
| 限流未区分模型 | 共享限流导致某个模型频繁被拒 | 模型级限流（rate_limits配置），每个模型独立计数 |

## 十二、总结

本文构建了一套完整的FastAPI多模型路由系统：

1. **YAML配置驱动**：模型列表、定价、能力、限流全在config/models.yaml中管理，改配置不改代码
2. **Provider模式**：DeepSeek/Qwen/OpenAI各自封装，互不耦合，新加Claude/其他模型只加一个类
3. **路由策略**：成本优先/速度优先/质量优先三种策略可切换
4. **自动降级**：模型失败自动切下一级，带冷却时间防止震荡
5. **费用追踪**：每次请求返回cost_usd，方便做成本监控
6. **健康检查**：每次请求前检查模型可用性，不浪费请求

关键是**配置即策略**：改models.yaml里的order就能改变路由优先级，无需改代码。