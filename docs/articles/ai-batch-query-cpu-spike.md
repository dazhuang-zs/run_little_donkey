# AI编程的隐藏陷阱：批量查询无限制打爆下游数据库CPU

> 一个用Claude Code写的"批量查询"功能，让数据库CPU从20%飙升到98%。排查了3小时，发现问题竟然出在AI生成的代码逻辑里。

---

## 引言：AI帮你写了代码，也帮你埋了雷

用AI编程半年，有一个感受越来越强烈：**AI生成的代码，跑起来没问题，但一上量就出事。**

原因很简单：AI写代码时，默认假设数据规模很小。它不会主动问你"这个查询会返回多少条数据"、"你的数据库能承受多少并发"。

今天要说的这个坑，是我最近踩过的真实案例。

---

## 问题背景：批量查询功能上线，数据库CPU爆炸

### 场景描述

业务方需要一个"批量查询用户信息"的功能：
- 输入：1000个用户ID列表
- 输出：每个用户的信息（姓名、手机、订单数等）
- 要求：毫秒级响应

我让Claude Code写了一个Python异步函数，代码看起来很优雅：

```python
async def batch_query_users(user_ids: list[int]) -> list[dict]:
    """批量查询用户信息"""
    async with httpx.AsyncClient() as client:
        tasks = [query_single_user(client, uid) for uid in user_ids]
        results = await asyncio.gather(*tasks)
    return results

async def query_single_user(client: httpx.AsyncClient, user_id: int) -> dict:
    """查询单个用户信息"""
    response = await client.get(f"/api/users/{user_id}")
    return response.json()
```

看起来没问题。测试10个用户，响应正常。部署上线。

**然后灾难开始了。**

### 实际表现

上线后监控系统报警：
- 数据库CPU：从20% → 98%
- 响应时间：从50ms → 3s+
- 数据库连接数：直接打满
- 下游服务开始超时

排查发现：代码里隐藏了一个COUNT(*)查询。

### 根本原因

代码实际上是这么写的（AI帮我"优化"过）：

```python
async def query_single_user(client: httpx.AsyncClient, user_id: int) -> dict:
    """查询单个用户信息"""
    # AI生成的代码：每个用户都要查这些
    user_info = await client.get(f"/api/users/{user_id}")
    order_count = await client.get(f"/api/users/{user_id}/orders/count")  # 隐藏的COUNT查询！
    return {**user_info, "order_count": order_count}
```

当用户传入1000个ID时：
- 并发请求数：1000 × 2（user_info + order_count）= 2000个并发请求
- 每个请求都可能触发数据库查询
- 单库完全扛不住

---

## 问题分析：AI批量查询的三大雷区

### 雷区1：asyncio.gather 无限制并发

```python
# AI最爱写的代码
tasks = [query_single_user(client, uid) for uid in user_ids]
results = await asyncio.gather(*tasks)  # 1000个任务同时跑！
```

问题：输入多少，瞬时并发就是多少。没有上限。

### 雷区2：循环里的"隐藏查询"

AI经常会在循环里插入额外查询，比如：

```python
# AI生成的代码
for order in orders:
    order["item_count"] = await db.execute(
        "SELECT COUNT(*) FROM order_items WHERE order_id = ?", order["id"]
    )
```

这就是经典的**N+1查询问题**。1000个订单 = 1001次数据库查询。

### 雷区3：以为"批量接口"就是批量

有时候AI会这样写：

```python
# AI建议的"批量接口"用法
for user_id in user_ids:
    response = await batch_user_api(user_id)  # 其实是一个一个查
```

把"批量接口"当成了循环调用的对象，完全没有利用批量优势。

---

## 解决方案：三层防护策略

### 第一层：Semaphore限流

用信号量控制最大并发数：

```python
import asyncio
from asyncio import Semaphore

MAX_CONCURRENCY = 50  # 根据数据库承受能力调整

async def batch_query_users(user_ids: list[int]) -> list[dict]:
    semaphore = Semaphore(MAX_CONCURRENCY)
    
    async def limited_query(uid: int) -> dict:
        async with semaphore:
            return await query_single_user(uid)
    
    tasks = [limited_query(uid) for uid in user_ids]
    results = await asyncio.gather(*tasks)
    return results
```

效果：
- 最大并发从2000降到50
- 数据库CPU从98%降到40%
- 响应时间从3s降到500ms

### 第二层：批量接口优先

如果后端提供批量接口，一定要用：

```python
# 改用批量接口
async def batch_query_users(user_ids: list[int]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        # 一次请求查完
        response = await client.post(
            "/api/users/batch",
            json={"user_ids": user_ids}
        )
        return response.json()["users"]
```

如果后端没有批量接口，考虑自己封装一个本地缓存层：

```python
from functools import lru_cache
from typing import Optional

class UserCache:
    def __init__(self, ttl: int = 300):
        self.cache = {}
        self.ttl = ttl
    
    async def get_user(self, user_id: int) -> Optional[dict]:
        """带缓存的查询，自动去重"""
        if user_id not in self.cache:
            self.cache[user_id] = await self._fetch_user(user_id)
        return self.cache[user_id]
    
    async def batch_get(self, user_ids: list[int]) -> dict[int, dict]:
        """批量获取，自动去重"""
        unique_ids = list(set(user_ids))
        await asyncio.gather(*[self.get_user(uid) for uid in unique_ids])
        return {uid: self.cache[uid] for uid in user_ids if uid in self.cache}
```

### 第三层：数据库连接池配置

确保数据库连接池有合理的上限：

```python
from databases import Database

# 设置连接池大小
database = Database(
    "postgresql://user:pass@localhost/db",
    min_size=5,      # 最小保持连接数
    max_size=20,     # 最大连接数（关键！）
)
```

连接池过小会限死并发，连接池过大会打爆数据库。需要根据实际压测结果调整。

---

## 完整优化代码

### 优化前（AI生成的原始代码）

```python
import asyncio
import httpx

async def batch_query_users(user_ids: list[int]) -> list[dict]:
    """AI生成的原始代码 - 有性能问题"""
    async with httpx.AsyncClient() as client:
        tasks = [query_single_user(client, uid) for uid in user_ids]
        return await asyncio.gather(*tasks)

async def query_single_user(client: httpx.AsyncClient, user_id: int) -> dict:
    user = await client.get(f"/api/users/{user_id}")
    # AI"优化"后加的：查询订单数
    order_count = await client.get(f"/api/users/{user_id}/orders/count")
    return {**user.json(), "order_count": order_count.json()["count"]}
```

### 优化后（加了三层防护）

```python
import asyncio
from asyncio import Semaphore
from typing import Optional
from dataclasses import dataclass
import httpx
import time

@dataclass
class RateLimitedClient:
    """带限流和缓存的HTTP客户端"""
    client: httpx.AsyncClient
    semaphore: Semaphore
    cache: dict
    cache_ttl: int = 300
    
    async def get(self, url: str, **kwargs) -> dict:
        # 检查缓存
        cache_key = f"{url}:{kwargs.get('params', {})}"
        if cache_key in self.cache:
            cached, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached
        
        # 限流控制
        async with self.semaphore:
            response = await self.client.get(url, **kwargs)
            result = response.json()
            
            # 写入缓存
            self.cache[cache_key] = (result, time.time())
            return result

async def batch_query_users(user_ids: list[int]) -> list[dict]:
    """优化后的批量查询"""
    MAX_CONCURRENCY = 50
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        rate_limited_client = RateLimitedClient(
            client=client,
            semaphore=Semaphore(MAX_CONCURRENCY),
            cache={}
        )
        
        async def limited_query(uid: int) -> dict:
            return await rate_limited_client.get(f"/api/users/{uid}")
        
        tasks = [limited_query(uid) for uid in user_ids]
        return await asyncio.gather(*tasks)
```

---

## 性能对比

| 指标 | 优化前 | 优化后 | 改善 |
|------|--------|--------|------|
| 最大并发数 | 2000 | 50 | -97.5% |
| 数据库CPU | 98% | 40% | -59% |
| 响应时间(P99) | 3000ms | 500ms | -83% |
| 数据库连接数 | 500+ | 20 | -96% |

---

## 经验总结：AI编程必查清单

用AI写批量处理代码时，一定要检查：

1. **并发数控制**
   - 有没有Semaphore/BoundedExecutor？
   - 最大并发数是否合理？

2. **隐藏查询**
   - for循环里有没有额外查询？
   - 每次查询是不是必要的？

3. **批量接口**
   - 有没有现成的批量API？
   - 能否用IN查询替代循环？

4. **缓存策略**
   - 重复数据有没有去重？
   - 热点数据有没有缓存？

5. **数据库连接池**
   - 连接池上限是多少？
   - 会不会打满？

---

## 附：常见限流方案对比

### Python

```python
# 方案1：asyncio.Semaphore（推荐）
semaphore = asyncio.Semaphore(50)

# 方案2：aiolimit
import aiolimit
async with aiolimit(max_concurrent=50):
    await do_something()
```

### Java

```java
// 方案1：Semaphore
ExecutorService executor = Executors.newFixedThreadPool(50);
Semaphore semaphore = new Semaphore(50);

// 方案2：RateLimiter（Guava）
RateLimiter limiter = RateLimiter.create(1000.0); // 每秒1000次
```

### Go

```go
// 方案1：Worker Pool
sem := make(chan struct{}, 50)
for _, task := range tasks {
    sem <- struct{}{}
    go func(t Task) {
        defer func() { <-sem }()
        doSomething(t)
    }(task)
}
```

---

## 结语

AI编程提高了效率，但也带来了隐患。它帮你写代码，但不会帮你想清楚"这个代码能扛多少量"。

**教训：AI写的代码，上线前一定要review这三个问题：**
1. 并发数上限是多少？
2. 循环里有没有隐藏查询？
3. 数据库连接数够不够？

如果这三个问题回答不上来，建议先压测再上线。

---

**你踩过AI编程的哪些坑？欢迎评论区分享。**

> 本文基于真实踩坑经历编写，代码已脱敏处理。
