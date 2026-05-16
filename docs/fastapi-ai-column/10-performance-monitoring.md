# 高并发优化：异步、缓存、限流、监控

> **文章信息**：标题《高并发优化：异步、缓存、限流、监控》| 字数：约4000字 | 预估阅读时间：20分钟

---

## 1. 性能优化的核心思路

FastAPI应用性能瓶颈通常来自：
- **I/O阻塞**：同步数据库、HTTP调用阻塞事件循环
- **重复计算**：相同请求每次都计算
- **资源耗尽**：连接池、内存、CPU被打满

优化原则：
1. 异步优先：所有I/O操作用async
2. 缓存复用：减少重复计算和数据库查询
3. 限流保护：防止突发流量打垮服务
4. 监控定位：用数据驱动优化决策

---

## 2. 异步最佳实践

### 2.1 异步vs同步的差异

**同步写法**（阻塞）：
```python
# 同步：请求1等待3秒，请求2也等待3秒，总共6秒
@app.get("/sync")
async def sync_handler():
    result = requests.get("https://api.example.com/data")  # 3秒
    return result.json()
```

**异步写法**（非阻塞）：
```python
# 异步：请求1和请求2同时发起，总共3秒
@app.get("/async")
async def async_handler():
    async with httpx.AsyncClient() as client:
        result = await client.get("https://api.example.com/data")  # 3秒
        return result.json()
```

### 2.2 异步HTTP客户端

```python
# utils/http_client.py
import httpx
from contextlib import asynccontextmanager
from typing import Optional

class HTTPClient:
    """全局异步HTTP客户端"""
    
    _instance: Optional["HTTPClient"] = None
    _client: Optional[httpx.AsyncClient] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=5.0),
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                    keepalive_expiry=30.0
                ),
                follow_redirects=True,
            )
        return self._client
    
    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

# 全局实例
http_client = HTTPClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    yield
    # 关闭时
    await http_client.close()

app = FastAPI(lifespan=lifespan)

@app.get("/ai-proxy")
async def proxy_to_ai(prompt: str):
    client = await http_client.get_client()
    response = await client.post(
        "https://api.deepseek.com/v1/chat/completions",
        json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]}
    )
    return response.json()
```

### 2.3 异步数据库连接池

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

# 生产环境：有限连接池
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=10,           # 常规连接数
    max_overflow=20,        # 允许额外创建
    pool_timeout=30,        # 获取连接超时
    pool_pre_ping=True,     # 使用前检查连接
    pool_recycle=3600,      # 1小时后回收连接
)

# 开发环境：无连接池（方便调试）
dev_engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### 2.4 并发任务处理

```python
# 处理多个AI请求（并发）
async def process_multiple_queries(queries: List[str]) -> List[str]:
    async with httpx.AsyncClient() as client:
        tasks = [
            call_deepseek(client, q) for q in queries
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return [r if isinstance(r, str) else f"Error: {r}" for r in results]

async def call_deepseek(client: httpx.AsyncClient, query: str) -> str:
    response = await client.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": query}]
        }
    )
    return response.json()["choices"][0]["message"]["content"]

# 限流并发（控制并发数）
async def limited_gather(tasks: List, max_concurrent: int = 5) -> List:
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def with_semaphore(task):
        async with semaphore:
            return await task
    
    return await asyncio.gather(*[with_semaphore(t) for t in tasks])
```

---

## 3. Redis缓存

### 3.1 缓存层设计

```python
# utils/cache.py
import redis.asyncio as redis
import json
from typing import Optional, Any
import hashlib

class CacheManager:
    """Redis缓存管理器"""
    
    def __init__(self, url: str = "redis://localhost:6379/0"):
        self.redis = redis.from_url(url, decode_responses=True)
        self.default_ttl = 3600  # 1小时
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存"""
        ttl = ttl or self.default_ttl
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return await self.redis.setex(key, ttl, value)
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        return await self.redis.delete(key) > 0
    
    async def exists(self, key: str) -> bool:
        """检查key是否存在"""
        return await self.redis.exists(key) > 0
    
    def make_key(self, prefix: str, *args) -> str:
        """生成缓存key"""
        key_str = ":".join(str(a) for a in args)
        hash_key = hashlib.md5(key_str.encode()).hexdigest()[:12]
        return f"{prefix}:{hash_key}"

# 全局实例
cache = CacheManager()
```

### 3.2 缓存中间件

```python
# middlewares/cache.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from utils.cache import cache
import json

class CacheMiddleware(BaseHTTPMiddleware):
    """自动缓存GET请求"""
    
    async def dispatch(self, request: Request, call_next):
        # 只缓存GET请求
        if request.method != "GET":
            return await call_next(request)
        
        # 生成缓存key
        cache_key = f"http:{request.url.path}:{request.url.query}"
        
        # 尝试获取缓存
        cached = await cache.get(cache_key)
        if cached:
            return Response(
                content=json.dumps(cached) if isinstance(cached, dict) else cached,
                media_type="application/json",
                headers={"X-Cache": "HIT"}
            )
        
        # 执行请求
        response = await call_next(request)
        
        # 缓存响应（如果成功）
        if response.status_code == 200:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            try:
                data = json.loads(body.decode())
                await cache.set(cache_key, data, ttl=300)  # 缓存5分钟
            except:
                pass
            
            return Response(
                content=body,
                status_code=response.status_code,
                headers={**dict(response.headers), "X-Cache": "MISS"}
            )
        
        return response
```

### 3.3 会话存储

```python
# utils/session.py
from typing import Optional, Dict, List
import json

class SessionManager:
    """基于Redis的会话管理"""
    
    def __init__(self, redis_client, prefix: str = "session"):
        self.redis = redis_client
        self.prefix = prefix
    
    def _key(self, session_id: str) -> str:
        return f"{self.prefix}:{session_id}"
    
    async def create(self, session_id: str, ttl: int = 86400) -> Dict:
        """创建会话"""
        session_data = {"created_at": self._now()}
        await self.redis.setex(
            self._key(session_id),
            ttl,
            json.dumps(session_data)
        )
        return session_data
    
    async def get(self, session_id: str) -> Optional[Dict]:
        """获取会话"""
        data = await self.redis.get(self._key(session_id))
        if data:
            return json.loads(data)
        return None
    
    async def update(self, session_id: str, data: Dict) -> bool:
        """更新会话"""
        existing = await self.get(session_id)
        if existing is None:
            return False
        existing.update(data)
        await self.redis.set(self._key(session_id), json.dumps(existing))
        return True
    
    async def delete(self, session_id: str) -> bool:
        """删除会话"""
        return await self.redis.delete(self._key(session_id)) > 0
    
    @staticmethod
    def _now() -> str:
        from datetime import datetime
        return datetime.utcnow().isoformat()
```

---

## 4. 限流策略

### 4.1 使用slowapi

```python
# main.py
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# 初始化限流器（基于IP地址）
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 全局限流
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # 某些路径不限流
    if request.url.path in ["/health", "/docs", "/openapi.json"]:
        return await call_next(request)
    return await call_next(request)

# 端点限流装饰器
@app.get("/ai/chat")
@limiter.limit("10/minute")  # 每分钟10次
async def ai_chat(request: Request, prompt: str):
    # AI处理逻辑
    pass

@app.get("/search")
@limiter.limit("30/minute")  # 每分钟30次
async def search(request: Request, q: str):
    # 搜索逻辑
    pass

# 自定义限流规则（基于用户）
from slowapi import Limiter
from slowapi.util import get_remote_address

def get_user_identifier(request: Request) -> str:
    """基于API Key的限流"""
    api_key = request.headers.get("Authorization", "").replace("Bearer ", "")
    if api_key:
        return api_key
    return get_remote_address(request)

user_limiter = Limiter(key_func=get_user_identifier)

@app.post("/ai/completion")
@user_limiter.limit("60/minute")  # 每分钟60次
async def ai_completion(request: Request):
    pass
```

### 4.2 令牌桶算法实现

```python
# utils/ratelimit.py
import time
import asyncio
from typing import Dict

class TokenBucket:
    """令牌桶限流器"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # 每秒补充令牌数
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """尝试获取令牌，返回是否成功"""
        async with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

class MultiTierLimiter:
    """多层级限流器（支持用户/租户/全局）"""
    
    def __init__(self):
        self.user_limiters: Dict[str, TokenBucket] = {}
        self.global_limiter = TokenBucket(capacity=1000, refill_rate=100)  # 全局每秒1000请求
    
    def get_user_bucket(self, user_id: str, tier: str = "free") -> TokenBucket:
        """获取用户的限流桶"""
        if user_id not in self.user_limiters:
            limits = {
                "free": (10, 1),      # 10个令牌，每秒补充1个
                "pro": (100, 10),     # 100个令牌，每秒补充10个
                "enterprise": (1000, 100)  # 1000个令牌，每秒补充100个
            }
            capacity, refill = limits.get(tier, limits["free"])
            self.user_limiters[user_id] = TokenBucket(capacity, refill)
        return self.user_limiters[user_id]
    
    async def check(self, user_id: str, tier: str = "free") -> tuple[bool, str]:
        """检查是否允许请求"""
        global_bucket = self.global_limiter
        user_bucket = self.get_user_bucket(user_id, tier)
        
        # 先检查全局
        if not await global_bucket.acquire():
            return False, "系统限流，请稍后再试"
        
        # 再检查用户级
        if not await user_bucket.acquire():
            return False, f"您的{tier}套餐已达限流阈值"
        
        return True, "允许"
```

### 4.3 AI API特殊限流

```python
# utils/ai_ratelimit.py
import asyncio
from collections import defaultdict

class AIAPIRateLimiter:
    """AI API特殊限流器（按模型和Token数）"""
    
    def __init__(self):
        self.limits = {
            "deepseek-chat": {"requests": 60, "tokens": 1_000_000},  # RPM和TPM
            "deepseek-coder": {"requests": 30, "tokens": 500_000},
            "gpt-4o-mini": {"requests": 500, "tokens": 1_000_000},
        }
        self.request_times = defaultdict(list)
        self.token_counts = defaultdict(list)
    
    async def acquire(self, model: str, estimated_tokens: int = 0) -> bool:
        """检查是否可以调用AI API"""
        now = asyncio.get_event_loop().time()
        limit_config = self.limits.get(model, {"requests": 100, "tokens": 500_000})
        
        # 清理过期记录（1分钟内）
        self.request_times[model] = [t for t in self.request_times[model] if now - t < 60]
        self.token_counts[model] = [t for t in self.token_counts[model] if now - t < 60]
        
        # 检查请求数
        if len(self.request_times[model]) >= limit_config["requests"]:
            return False
        
        # 检查Token数
        if estimated_tokens > 0:
            recent_tokens = sum(self.token_counts[model])
            if recent_tokens + estimated_tokens > limit_config["tokens"]:
                return False
        
        # 记录
        self.request_times[model].append(now)
        if estimated_tokens > 0:
            self.token_counts[model].append(estimated_tokens)
        
        return True
    
    async def wait_and_acquire(self, model: str, estimated_tokens: int = 0, max_wait: int = 60) -> bool:
        """等待直到可以调用"""
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < max_wait:
            if await self.acquire(model, estimated_tokens):
                return True
            await asyncio.sleep(1)
        return False
```

---

## 5. Prometheus + Grafana监控

### 5.1 Prometheus指标

```python
# utils/metrics.py
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from prometheus_client.openmetrics.exposition import generate_latest
import time

# 创建自定义注册表
REGISTRY = CollectorRegistry()

# 请求计数
REQUEST_COUNT = Counter(
    "fastapi_requests_total",
    "Total requests",
    ["method", "endpoint", "status"],
    registry=REGISTRY
)

# 请求延迟
REQUEST_LATENCY = Histogram(
    "fastapi_request_duration_seconds",
    "Request latency",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=REGISTRY
)

# AI API调用计数
AI_API_CALLS = Counter(
    "ai_api_calls_total",
    "AI API calls",
    ["model", "status"],
    registry=REGISTRY
)

# AI API延迟
AI_API_LATENCY = Histogram(
    "ai_api_duration_seconds",
    "AI API call duration",
    ["model"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=REGISTRY
)

# 当前连接数
ACTIVE_CONNECTIONS = Gauge(
    "fastapi_active_connections",
    "Active connections",
    registry=REGISTRY
)

# 缓存命中率
CACHE_HITS = Counter(
    "cache_hits_total",
    "Cache hits",
    ["cache_type"],
    registry=REGISTRY
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Cache misses",
    ["cache_type"],
    registry=REGISTRY
)
```

### 5.2 FastAPI中间件集成

```python
# middlewares/metrics.py
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from utils.metrics import (
    REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_CONNECTIONS
)

class MetricsMiddleware(BaseHTTPMiddleware):
    """指标收集中间件"""
    
    async def dispatch(self, request: Request, call_next):
        ACTIVE_CONNECTIONS.inc()
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as e:
            status = 500
            raise
        finally:
            ACTIVE_CONNECTIONS.dec()
            duration = time.time() - start_time
            
            # 记录指标
            endpoint = request.url.path
            method = request.method
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=str(status)
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
        
        return response
```

### 5.3 指标端点

```python
# routers/metrics.py
from fastapi import APIRouter, Response
from prometheus_client import REGISTRY

router = APIRouter(prefix="/metrics", tags=["监控"])

@router.get("")
async def metrics():
    """Prometheus指标端点"""
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain"
    )

@router.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}
```

### 5.4 Grafana仪表板配置

```json
{
  "dashboard": {
    "title": "FastAPI应用监控",
    "panels": [
      {
        "title": "QPS（每秒请求数）",
        "targets": [
          {
            "expr": "rate(fastapi_requests_total[1m])",
            "legendFormat": "{{endpoint}}"
          }
        ]
      },
      {
        "title": "P99延迟",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, rate(fastapi_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P99"
          }
        ]
      },
      {
        "title": "错误率",
        "targets": [
          {
            "expr": "rate(fastapi_requests_total{status=~'5..'}[5m]) / rate(fastapi_requests_total[5m])",
            "legendFormat": "错误率"
          }
        ]
      },
      {
        "title": "AI API调用延迟",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(ai_api_duration_seconds_bucket[5m]))",
            "legendFormat": "P95 - {{model}}"
          }
        ]
      }
    ]
  }
}
```

---

## 6. 结构化日志

```python
# utils/logging.py
import structlog
import logging
from typing import Any

# 配置structlog
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

# 请求日志中间件
async def log_request(request: Request, call_next):
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown",
    )
    
    response = await call_next(request)
    
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
    )
    
    return response
```

---

## 7. Locust性能测试

```python
# tests/load_test.py
from locust import HttpUser, task, between, events
import random

class FastAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def chat_with_ai(self):
        """AI聊天接口（高频）"""
        self.client.post(
            "/ai/chat",
            json={"prompt": f"什么是Python #{random.randint(1,100)}"},
        )
    
    @task(1)
    def health_check(self):
        """健康检查（低频）"""
        self.client.get("/health")
    
    @task(2)
    def search(self):
        """搜索接口（中频）"""
        self.client.get(f"/search?q=python&limit=10")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("性能测试开始")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("性能测试结束")

# 运行：locust -f tests/load_test.py --host=http://localhost:8000
```

---

## 8. 踩坑记录

### 坑1：async函数中使用同步库

**问题**：在async函数中用了`requests`（同步库），阻塞了整个事件循环。

**解决**：替换为`httpx.AsyncClient`或`aiohttp`。如果必须用同步库，用`run_in_executor`包装：
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def sync_to_async():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, blocking_function)
    return result
```

### 坑2：连接池配置导致"Too many connections"

**问题**：PostgreSQL默认`max_connections=100`，但4个FastAPI实例各开20个连接池就超标了。

**解决**：计算总连接数，合理分配：
```python
# 每个实例
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,      # 常规连接
    max_overflow=5,    # 额外连接
)
# 4个实例 = 10*4 + 5*4 = 60 连接，加上其他服务还有余量
```

### 坑3：Redis缓存雪崩

**问题**：大量缓存同时过期，瞬间大量请求打到数据库。

**解决**：添加随机延迟：
```python
async def set_with_jitter(self, key: str, value: Any, base_ttl: int):
    # 基础TTL + 随机0-10%延迟
    import random
    jitter = base_ttl * random.uniform(0, 0.1)
    await self.set(key, value, ttl=int(base_ttl + jitter))
```

### 坑4：限流器在高并发下失效

**问题**：多个协程同时检查限流，都通过，导致超过限制。

**解决**：使用`asyncio.Lock`保证原子性：
```python
self._lock = asyncio.Lock()

async def acquire(self, tokens: int = 1) -> bool:
    async with self._lock:
        # 检查和扣减必须是原子操作
        ...
```

### 坑5：Prometheus指标影响性能

**问题**：每个请求都更新指标，高并发下反而成为瓶颈。

**解决**：使用`multiprocessing`模式或减少指标维度：
```python
# 不要给每个请求的每个参数都打标签
# 坏：endpoint=具体路径, method=具体方法, status=具体码
# 好：endpoint=/api/*, status=2xx/4xx/5xx
```

### 坑6：热重载时连接池泄漏

**问题**：用`uvicorn --reload`开发时，代码重载但连接池没清理。

**解决**：正确使用lifespan管理生命周期：
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化
    yield
    # 清理
    await engine.dispose()
```

---

## 9. 总结

本文覆盖了FastAPI生产环境性能优化的完整方案：

1. **异步优化**：httpx异步客户端、异步数据库连接池、并发任务处理
2. **缓存策略**：Redis缓存层、自动缓存中间件、会话存储
3. **限流保护**：slowapi限流、令牌桶算法、AI API特殊限流
4. **监控体系**：Prometheus指标、Grafana仪表板、结构化日志
5. **性能测试**：Locust负载测试

**关键指标**：
- P99延迟 < 500ms
- 错误率 < 0.1%
- 缓存命中率 > 80%

**监控关键指标**：
- QPS（每秒请求数）
- P50/P95/P99延迟
- 错误率
- CPU/内存使用率
- AI API延迟和Token消耗