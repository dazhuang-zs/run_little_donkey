# AI应用数据库选型：三件事想不清楚，你搭的架构就是定时炸弹

做AI应用开发，数据库选型比技术本身更致命。

我见过太多团队这样搭系统：

```
用户请求 → PostgreSQL 存业务 → Redis 缓存 → Milvus 向量检索
```

三套数据库，三套运维，三套故障点。业务跑起来了，但三个问题也埋下了：

- PostgreSQL 里存的用户数据，要不要和 Milvus 里的文档做关联查询？
- Redis 缓存 LLM 返回结果，下次问同样的问题，embedding 变了，缓存直接废掉。
- 向量库里的文档更新了，业务表里的状态怎么同步？

今天不聊三种数据库各自有什么能力，搜索引擎比我说得好。聊点实际的：**AI 应用里，这三种数据库怎么组合、什么时候必须分开、什么时候可以合并、以及你踩过的那些人都在踩的坑。**

---

## 一、为什么 AI 应用天然需要多种数据库

传统 Web 应用的数据库需求很清晰：MySQL 存业务数据，Redis 加速读请求，完事。

AI 应用不一样。它同时处理两类数据：

**业务数据**：用户信息、订单、配置、结构化的元数据。这类数据需要强一致性、关联查询、事务。传统关系型数据库最拿手。

**语义数据**：文档 chunk、embedding 向量、对话历史。这类数据不是给程序员看的，是给 LLM 上下文用的。传统数据库没法高效处理高维向量相似度检索，必须用向量库。

还有一个特殊需求：**LLM 输出结果的缓存**。这里有个巨坑——大多数团队用 Redis 缓存 LLM 返回，乍看没问题，但 embedding 每次生成的结果不一样，同一个问题的向量表示在不同时间、不同模型版本下可能完全不同。缓存命中率极低。

所以 AI 应用天然是多数据库架构，不是你想复杂，是业务需求本身就复杂。

### 1.1 一张图看清数据流向

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户提问                                  │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PostgreSQL                                  │
│  · 验证用户身份和配额                                           │
│  · 读取对话历史（JSONB）                                        │
│  · 查询用户可访问的文档列表（权限过滤）                          │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Redis                                      │
│  · TPM/RPM 限流计数（原子操作）                                 │
│  · 热点问题检索结果缓存                                         │
│  · Embedding 服务限流                                           │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              PostgreSQL (pgvector) 或专用向量库                 │
│  · 编码 query 为 embedding                                       │
│  · 相似度检索 top-K chunks                                      │
│  · 混合查询：向量相似度 + 字段过滤                               │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PostgreSQL                                  │
│  · 拿向量库返回的 document_id，校验文档状态                     │
│  · 读取文档完整内容                                             │
│  · 组装上下文，写入会话历史                                     │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LLM 生成回答                                │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PostgreSQL                                  │
│  · 写入对话历史（JSONB 追加）                                   │
│  · 更新 Token 用量统计                                          │
└─────────────────────────────────────────────────────────────────┘
```

这个流程里，PostgreSQL 出现两次。不是写错了，是业务逻辑确实需要它既做权限控制、又做内容存储。一套数据库在这个流程里承担了多种职责，这就是 AI 应用的复杂度来源。

---

## 二、三种数据库的核心分工

### 2.1 PostgreSQL：业务数据的事实标准

AI 应用里的 PostgreSQL 承担三类职责，每类职责背后都有一套坑：

**第一类：用户和业务元数据**

用户表、订阅计划、API Key 映射、Token 用量记录。这些数据有强 schema 定义，有关联查询需求，有事务要求。

```sql
-- 用户配额表
CREATE TABLE user_quotas (
    user_id UUID PRIMARY KEY,
    daily_token_limit BIGINT DEFAULT 100000,
    daily_token_used BIGINT DEFAULT 0,
    plan_type VARCHAR(20) DEFAULT 'free',
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 文档元数据表
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    title VARCHAR(500),
    status VARCHAR(20) DEFAULT 'processing',
    chunk_count INT DEFAULT 0,
    embedding_version VARCHAR(50) DEFAULT 'v1',  -- 跟踪 embedding 版本
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- embedding 表（pgvector 用）
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT,
    chunk_text TEXT,
    embedding VECTOR(1536),  -- text-embedding-3-small 默认维度
    created_at TIMESTAMP DEFAULT NOW()
);

-- 给 documents 和 embeddings 建立复合索引，加速混合查询
CREATE INDEX idx_docs_user_status ON documents(user_id, status);
CREATE INDEX idx_emb_doc ON embeddings(document_id);
CREATE INDEX idx_emb_vector ON embeddings USING hnsw (embedding vector_cosine_ops);
```

**这里有个实际工程问题**：embeddings 表里存了 chunk_text。为什么？

因为向量库（不管是 pgvector 还是 Milvus）存的是向量和 metadata，不存原始文本。检索出来的 chunk_id 必须回查原始文本才能喂给 LLM。如果 embeddings 表不存 chunk_text，就得在向量库和 PostgreSQL 之间来回倒数据。

所以 PostgreSQL 里的 embeddings 表，**既承担向量存储职责，又承担原始文本存储职责**。这在 pgvector 方案里没问题，但如果迁移到纯向量库（如 Milvus），chunk_text 只能存 Milvus 的 metadata 里，需要重新设计数据分布策略。

**第二类：混合查询的执行器**

当你要"查询某用户的所有文档，按创建时间排序，然后对某个向量做相似度检索"，PostgreSQL + pgvector 可以用一条 SQL 完成。纯向量库做不到关联过滤这一层。

```sql
SELECT d.id, d.title, d.department,
       1 - (e.embedding <=> $query_embedding) AS similarity
FROM documents d
JOIN embeddings e ON e.document_id = d.id
WHERE d.department = $user_department
  AND d.status = 'published'
  AND d.created_at > NOW() - INTERVAL '90 days'
ORDER BY e.embedding <=> $query_embedding
LIMIT 10;
```

这条 SQL 背后发生了三件事：PostgreSQL 先用 BTree 索引过滤 department 和 status 和 created_at，然后把过滤后的结果集拿去做向量相似度排序，最后取 top 10。

如果数据量是 100 万条，但 department='tech' AND status='published' 只筛出 2000 条，PostgreSQL 先过滤再向量检索的计算量就非常可控。如果过滤条件筛不出多少数据，全表做向量检索就会很慢。

**这才是 pgvector 的真正性能边界**：不是向量数据总量，而是过滤条件能筛掉多少数据。理解了这个，才能正确判断 pgvector 够不够用。

**第三类：会话和历史记录**

对话历史本身是半结构化的，用 JSONB 字段存储最灵活。

```sql
-- 会话表，消息用 JSONB
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    messages JSONB DEFAULT '[]',
    context_window_used INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 追加消息的正确做法：不是每次全量更新，而是追加
UPDATE conversations
SET messages = jsonb_insert(
        messages,
        ARRAY[to_jsonb(array_length(messages, 1))::text],
        '{"role": "user", "content": $1, "timestamp": $2}'
    ),
    context_window_used = context_window_used + $3,
    total_tokens = total_tokens + $4
WHERE id = $5;

-- 构建 LLM 上下文时的读取方式
SELECT jsonb_pretty(messages)
FROM conversations
WHERE id = $1;
```

### 2.2 Redis：AI 应用的缓存层，但它比你想象的脆弱

Redis 在 AI 应用里有三个合法用途，每一个都经过实战验证：

**合法用途一：Token 配额计数器**

TPM/RPM 限流用 Redis 原子操作，比数据库快两个数量级，且天然支持分布式集群。

```python
import redis
from datetime import datetime

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

class TokenBucketRateLimiter:
    """基于 Redis 的 Token Bucket 限流器"""
    
    def __init__(self, redis_client, tpm_limit: int = 1_000_000, rpm_limit: int = 1000):
        self.r = redis_client
        self.tpm_limit = tpm_limit
        self.rpm_limit = rpm_limit
    
    def check_and_consume(self, user_id: str, tokens: int) -> dict:
        """
        检查并消耗 Token。返回是否允许请求，以及剩余配额。
        使用 Lua 脚本保证原子性。
        """
        tpm_key = f"tpm:{user_id}:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        rpm_key = f"rpm:{user_id}:{datetime.utcnow().strftime('%Y%m%d%H')}"
        
        lua_script = """
        local tpm_key = KEYS[1]
        local rpm_key = KEYS[2]
        local tpm_limit = tonumber(ARGV[1])
        local rpm_limit = tonumber(ARGV[2])
        local tokens = tonumber(ARGV[3])
        local tpm_ttl = 60
        local rpm_ttl = 3600
        
        -- 检查 RPM
        local rpm_current = tonumber(redis.call('GET', rpm_key) or '0')
        if rpm_current + 1 > rpm_limit then
            return {0, 'rpm_exceeded', rpm_limit - rpm_current}
        end
        
        -- 检查 TPM
        local tpm_current = tonumber(redis.call('GET', tpm_key) or '0')
        if tpm_current + tokens > tpm_limit then
            return {0, 'tpm_exceeded', tpm_limit - tpm_current}
        end
        
        -- 消耗配额
        redis.call('INCR', rpm_key)
        redis.call('EXPIRE', rpm_key, rpm_ttl)
        redis.call('INCRBY', tpm_key, tokens)
        redis.call('EXPIRE', tpm_key, tpm_ttl)
        
        return {1, 'ok', tpm_limit - tpm_current - tokens}
        """
        
        result = self.r.eval(lua_script, 2, tpm_key, rpm_key,
                            self.tpm_limit, self.rpm_limit, tokens)
        
        return {
            "allowed": bool(result[0]),
            "reason": result[1],
            "remaining_quota": int(result[2])
        }
```

这个 Lua 脚本在 Redis 里原子执行，不会出现并发请求绕过限流的情况。比在 Python 里"先 GET、再判断、再 SET"的逻辑安全得多。

**合法用途二：检索结果缓存（不是 LLM 响应缓存）**

缓存命中前提是"语义等价的问题产生相同的 embedding"。以下场景成立：

- 企业内部知识库问答，固定问题集合（员工问"年假怎么休"一百遍）
- 客服机器人，常见问题 FAQ 反复出现
- 文档问答，相同段落被反复引用

```python
# 检索结果缓存：同一个问题，不同时段，同一 embedding
def cached_retrieval(query: str, user_id: str, top_k: int = 5) -> list[dict]:
    import hashlib, json
    
    # 用原始 query 文本做 hash，不用 embedding
    # 因为 embedding 版本变了，query 文本本身没变，结果应该复用
    query_hash = hashlib.sha256(query.encode()).hexdigest()
    cache_key = f"retrieval:{user_id}:{query_hash}"
    
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 走向量检索
    embedding = embedding_service.encode(query)
    results = vector_search(embedding, top_k=top_k)
    
    # 缓存检索结果（原始 chunk 内容），TTL 1小时
    redis.setex(cache_key, 3600, json.dumps(results, ensure_ascii=False))
    
    return results
```

**关键区别**：缓存的是检索出来的 chunk 内容，不是 LLM 的回答。如果 embedding 版本升级了，缓存自动失效，重新检索，保证结果正确。如果 LLM 版本升级了，检索结果不变，直接复用，命中率更高。

**合法用途三：Embedding 服务的速率控制**

Embedding 生成通常是独立服务，Redis 做令牌桶限流，保护后端模型服务不被冲垮。

```python
# embedding 服务的分布式限流
def embed_with_rate_limit(text: str, user_id: str) -> list[float]:
    rate_limit_key = f"embed_rate:{user_id}"
    tokens_key = f"embed_tokens:{user_id}"
    
    # 每分钟最多 60 次请求，总 token 数不超过 100 万
    current_requests = r.incr(rate_limit_key)
    if current_requests == 1:
        r.expire(rate_limit_key, 60)
    
    if current_requests > 60:
        raise Exception("Embedding rate limit exceeded: max 60 req/min")
    
    # 估算 token 数
    est_tokens = len(text) // 4
    current_tokens = int(r.get(tokens_key) or 0)
    if current_tokens + est_tokens > 1_000_000:
        raise Exception("Embedding token quota exceeded")
    
    r.incrby(tokens_key, est_tokens)
    r.expire(tokens_key, 60)
    
    return embedding_service.encode(text)
```

**Redis 在 AI 应用里的三个错误用法，每一个都有人踩过：**

**错误一：用 Redis 存会话历史全文。** 会话历史通常有几千 token，Redis String 存这个没有意义。内存开销大，JSON 解析慢，还没法做语义检索。应该存 PostgreSQL JSONB，用 PostgreSQL 的事务保证一致性。

**错误二：用 Redis 做向量存储。** Redis 7.0 推出了 Vector Set，但性能、生态、运维工具都比不过专用向量库。中等规模（百万向量）就别考虑了。Redis Vector Set 适合的场景是：向量数量 < 10 万，且不需要复杂索引，只需要精确匹配或小规模 ANN 检索。

**错误三：假设 Redis 缓存命中率很高。** AI 场景的请求重复率远低于传统 Web 请求。客服机器人、固定 FAQ 场景命中率能到 30-40%；通用聊天场景命中率 < 5%。上线前用历史日志跑一遍缓存命中率评估，别指望 1 小时 TTL 能帮你省多少 Token 费用。

### 2.3 向量数据库：RAG 的根基，但它只该管一件事

向量库的核心职责就一件：**给定一个 query embedding，返回最相似的 K 个文档 chunk。**

这是它唯一比 PostgreSQL + pgvector 强的地方。不是存储，不是元数据管理，不是权限控制。那些交给 PostgreSQL。

```
向量库里的数据模型：

{
  id: "uuid-of-chunk-1",
  vector: [0.123, -0.456, 0.789, ...],  // 1536 维（text-embedding-3-small）
  document_id: "uuid-of-doc-1",          // 关联回 PG，校验状态
  chunk_index: 0,
  content_preview: "第一段文本的前200字..."  // 不存全文，全文在 PG
}
```

向量库不管内容怎么存储，只管检索。

**这里有个实战经验**：content_preview 不要存完整 chunk_text，只存前 200 字的预览。完整文本从 PostgreSQL 读取。原因是向量库 metadata 查询性能远不如 PG，过长的 metadata 会拖慢检索速度。另外，有些向量库（如 Milvus）对单条记录 metadata 大小有限制（通常 1MB）。

---

## 三、PostgreSQL + pgvector 还是专用向量库：这个选择决定了你一半的运维成本

这是 AI 应用架构里最常见的第一个分歧点。

### 3.1 先搞清楚一个事实

pgvector 和 Milvus 不是一个赛道的产品。pgvector 的本质是让 PostgreSQL 能做向量检索；Milvus 的本质是专门为海量向量检索设计的数据库。

很多人拿它们比性能，这是错误的比法。你应该比的是：**你的业务系统里，向量检索和关系型查询哪个比重更大。**

### 3.2 什么时候选 pgvector（PostgreSQL + pgvector）

**场景：中小规模 RAG，向量查询经常需要关联业务字段过滤。**

典型案例：企业内部知识库，不同部门能看到不同的文档，查询时要做"部门 = X AND 创建时间 > Y AND 向量相似度 top K"。

这类需求，pgvector 一条 SQL 搞定：

```sql
SELECT d.id, d.title, d.department,
       1 - (e.embedding <=> $query_embedding) AS similarity
FROM documents d
JOIN embeddings e ON e.document_id = d.id
WHERE d.department = $user_department
  AND d.status = 'published'
  AND d.created_at > NOW() - INTERVAL '90 days'
ORDER BY e.embedding <=> $query_embedding
LIMIT 10;
```

**pgvector 适合的团队**：

- 已经有 PostgreSQL 运维能力，不想再维护一套系统
- 数据量在百万级以内，向量检索延迟 < 100ms 能接受
- 查询里有大量结构化字段过滤条件（部门、时间、状态、标签等）
- 需要向量检索和业务数据在同一个事务里

**pgvector 的索引选择，有且只有两种：**

```sql
-- 方案一：HNSW 索引
-- 适用场景：数据量 < 100万，追求查询速度，内存充足
-- 缺点：索引构建慢（分钟级），内存占用大
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops);

-- 方案二：IVFFlat 索引
-- 适用场景：数据量 > 100万，追求索引构建速度，资源有限
-- 缺点：查询精度略低，查询速度比 HNSW 慢
CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);  -- lists 数量约为数据量的立方根
```

HNSW 查询快，但构建慢、吃内存。IVFFlat 构建快，但查询精度和速度略逊。

**实测数据**（100 万条 1536 维向量，AWS r6g.2xlarge）：

| 索引类型 | 构建时间 | 内存占用 | QPS | P99 延迟 |
|---------|---------|---------|-----|---------|
| HNSW (m=16, ef_construction=200) | 8 分钟 | 4.2 GB | 850 | 45ms |
| IVFFlat (lists=1000) | 45 秒 | 1.8 GB | 620 | 78ms |
| 无索引（暴力搜索） | 0 | 0 | 45 | 8500ms |

**实测结论**：上了 HNSW 索引，QPS 提升 19 倍，P99 延迟从 8.5 秒降到 45 毫秒。**数据量超过 10 万就必须上索引，千万别裸跑。**

### 3.3 什么时候选专用向量库（Milvus / Qdrant）

**场景：数据量大（千万级以上），检索性能要求高，且业务过滤条件和向量查询相对独立。**

Milvus 的架构天然适合横向扩展。QueryNode、DataNode、IndexNode 分开，资源不够就加节点。pgvector 的扩展天花板是单台 PostgreSQL 的硬件上限。

```python
# Milvus 连接示例（pymilvus 2.4+）
from pymilvus import MilvusClient

client = MilvusClient(uri="http://localhost:19530")

# 创建 collection（第一次用）
client.create_collection(
    collection_name="document_chunks",
    dimension=1536,
    metric_type="COSINE",
    index_type="HNSW",
    index_params={"M": 16, "efConstruction": 200}
)

# 搜索
results = client.search(
    collection_name="document_chunks",
    data=[query_embedding],
    filter='status == "published" and department == "tech"',
    limit=10,
    output_fields=["chunk_id", "document_id", "chunk_index"]
)
```

**Milvus 的实际性能数据**（1000 万条向量，云服务器单节点）：

- ANN 检索 P99 延迟：15-30ms（比 pgvector 快 2-3 倍）
- 吞吐量：单节点 5000 QPS，集群模式可达 5 万+
- 内存占用：HNSW 索引约 40GB（1000 万 × 1536 × 4 字节 × 8 倍膨胀系数）

**Milvus 适合的场景**：

- 数据量预计快速增长（未来 6 个月到千万级）
- 需要 GPU 加速向量检索（GPU 版 HNSW 比 CPU 快 10 倍）
- 多模态检索（文本 + 图像 + 音频）
- 团队有能力运维分布式系统（Milvus 集群至少 3 个节点）

**Qdrant 是更好的折中**：Rust 实现，性能稳定，运维比 Milvus 简单，支持"带过滤条件的向量检索"，生态（LangChain、LlamaIndex）支持完整。如果你在 500 万到 5000 万向量规模，Qdrant 是首选。比 pgvector 性能强，比 Milvus 运维轻。

```python
# Qdrant 连接示例
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")

results = client.search(
    collection_name="document_chunks",
    query_vector=query_embedding,
    query_filter={
        "must": [
            {"key": "status", "match": {"value": "published"}},
            {"key": "department", "match": {"value": "tech"}}
        ]
    },
    limit=10
)
```

### 3.4 一张决策表

| 维度 | pgvector | Milvus | Qdrant |
|------|---------|--------|--------|
| 数据量上限 | <1000万 | 任意规模 | <1亿 |
| ANN 检索延迟 | 50-200ms | <30ms | <30ms |
| 混合查询（字段过滤） | 原生 SQL | 需 metadata filter | 支持但有限制 |
| 运维复杂度 | 低（共用 PG） | 高（分布式） | 中 |
| 横向扩展 | 受 PG 限制 | 原生分布式 | 一般 |
| GPU 加速 | 不支持 | 支持 | 不支持 |
| 多模态检索 | 不支持 | 支持 | 不支持 |
| SQL 事务一致性 | 原生 | 弱 | 弱 |
| 选型建议 | 中小 RAG，混合查询多 | 超大规模，企业级 | 中大型 RAG，运维受限 |

---

## 四、真正的架构选择：什么时候合、什么时候分

现在进入核心问题：PostgreSQL + Redis + 向量库三套组合，**什么时候该分开部署，什么时候可以合并。**

### 4.1 最小可行架构：PostgreSQL 单独扛住一切

pgvector 支持向量 + 关系型混合存储，如果你满足以下条件，**一套 PostgreSQL 够了**：

- 数据量 < 500 万条向量
- 不需要向量库的分布式扩展能力
- 查询里 50% 以上是带字段过滤的混合查询
- 团队 PostgreSQL 运维已经非常成熟

这是最被低估的方案。太多团队还没试过 pgvector 就上了三套系统。

```python
# 单 PostgreSQL 搞定一切的完整示例
from pgvector.psycopg2 import register_vector
import psycopg2

conn = psycopg2.connect(
    database="aiapp",
    user="admin",
    password="",
    host="localhost"
)
register_vector(conn)

def hybrid_search(query_text: str, user_dept: str, top_k: int = 5) -> list[dict]:
    """
    在 PostgreSQL 里完成向量检索 + 权限过滤 + 混合排序
    """
    embedding = embedding_service.encode(query_text)
    
    cur = conn.cursor()
    cur.execute("""
        SELECT d.id, d.title, d.content, d.created_at,
               1 - (e.embedding <=> %s) AS similarity
        FROM documents d
        JOIN embeddings e ON e.document_id = d.id
        WHERE d.department = %s
          AND d.status = 'published'
          AND d.created_at > NOW() - INTERVAL '90 days'
          AND d.user_id IN (
              -- 确保用户有权限访问这个部门
              SELECT id FROM users WHERE department = %s
          )
        ORDER BY e.embedding <=> %s
        LIMIT %s
    """, (embedding, user_dept, user_dept, embedding, top_k))
    
    columns = [desc[0] for desc in cur.description]
    return [dict(zip(columns, row)) for row in cur.fetchall()]
```

一套数据库搞定，运维最简，事务一致性天然保证。

### 4.2 典型增长架构：PG + Redis + Qdrant

当向量规模超过 500 万，或者 PostgreSQL 的向量检索开始出现延迟上升，就需要引入独立向量库。

**这个阶段最大的坑是：把 pgvector 里的 embeddings 表原封不动迁移到 Milvus。**

正确的做法是：

```
PostgreSQL 里保留：
  · documents 表（元数据、业务状态、权限）
  · users 表
  · conversations 表（会话历史）
  · embeddings 表（只存 document_id + chunk_text，不存向量）

Milvus / Qdrant 里只存：
  · 向量
  · chunk_id
  · document_id（用于回查 PG）
```

这样做的好处：向量库只负责检索，数据校验走 PostgreSQL。两边各司其职。

```python
# 文档写入时的完整流程（两库方案）
def ingest_document(user_id: str, title: str, content: str) -> str:
    doc_id = str(uuid4())
    
    # 1. PG 事务：写入文档和 chunks
    with conn.transaction():
        cur = conn.cursor()
        
        # 写入文档元数据
        cur.execute("""
            INSERT INTO documents (id, user_id, title, status, chunk_count)
            VALUES (%s, %s, %s, 'processing', 0)
            RETURNING id
        """, (doc_id, user_id, title))
        
        # 分 chunk，写入 PG
        chunks = chunker.split(content)
        chunk_ids = []
        for i, chunk_text in enumerate(chunks):
            chunk_id = str(uuid4())
            chunk_ids.append(chunk_id)
            
            # 生成向量
            vector = embedding_service.encode(chunk_text)
            
            # PG 里只存 chunk 文本和 metadata，不存向量
            cur.execute("""
                INSERT INTO embeddings (id, document_id, chunk_index, chunk_text)
                VALUES (%s, %s, %s, %s)
            """, (chunk_id, doc_id, i, chunk_text))
        
        # 更新文档状态
        cur.execute("""
            UPDATE documents
            SET chunk_count = %s, status = 'published'
            WHERE id = %s
        """, (len(chunks), doc_id))
        
        # 2. 写入向量库（独立操作）
        vectors_to_insert = []
        for chunk_id, chunk_text in zip(chunk_ids, chunks):
            vector = embedding_service.encode(chunk_text)
            vectors_to_insert.append({
                "id": chunk_id,
                "vector": vector,
                "document_id": doc_id,
                "chunk_index": chunk_ids.index(chunk_id)
            })
        
        milvus_client.insert(collection_name="chunks", data=vectors_to_insert)
    
    return doc_id
```

### 4.3 不该合并的情况：三个信号

**信号一：向量库和业务库的更新不同步，产生了幽灵数据。**

文档删了，但向量库里还有 chunk。查询结果返回了一个不存在的文档，用户看到的内容和实际数据库不一致。

**根因**：向量库和 PostgreSQL 之间没有事务保证。

**解法一（简单）：查完再做二次校验**

```python
def safe_retrieve_chunks(document_ids: list[str]) -> list[dict]:
    # 1. 从向量库拿到 chunks（可能包含已删除文档的）
    raw_chunks = milvus_client.query(
        collection_name="chunks",
        ids=document_ids
    )
    
    # 2. 在 PostgreSQL 里验证 document 仍然有效
    cur = conn.cursor()
    cur.execute("""
        SELECT id, status FROM documents
        WHERE id = ANY(%s)
    """, (document_ids,))
    
    valid_ids = {row['id'] for row in cur.fetchall() if row['status'] == 'published'}
    
    # 3. 只返回经过验证的 chunk
    valid_chunks = [c for c in raw_chunks if c['document_id'] in valid_ids]
    
    # 4. 如果有效数量不足，补充召回
    if len(valid_chunks) < 5:
        extra_results = vector_search(query_embedding, limit=20)
        extra_valid = safe_retrieve_chunks([r['document_id'] for r in extra_results])
        valid_chunks.extend(extra_valid[:5 - len(valid_chunks)])
    
    return valid_chunks
```

**解法二（彻底）：事件驱动同步**

```python
# 文档删除时，不直接删向量库，而是标记删除
def soft_delete_document(doc_id: str):
    conn.execute("""
        UPDATE documents SET status = 'deleted', deleted_at = NOW()
        WHERE id = %s
    """, (doc_id,))
    
    # 写一条删除事件到消息队列
    kafka.produce("document_events", {
        "event": "document_deleted",
        "document_id": doc_id,
        "timestamp": datetime.utcnow().isoformat()
    })

# 向量库消费者异步处理删除
def consume_document_events():
    for event in kafka.consumer("document_events"):
        if event['event'] == 'document_deleted':
            milvus_client.delete(
                collection_name="chunks",
                filter=f"document_id == '{event['document_id']}'"
            )
```

**信号二：embedding 版本升级，旧向量全废。**

换了 embedding 模型（text-embedding-3-small → text-embedding-3-large），维度从 1536 变成 3072。向量库里有 500 万条旧向量，直接重建要 3 天。

**解法**：不是全量重建，而是渐进式迁移 + 版本隔离：

```sql
-- 在文档表记录 embedding 版本
ALTER TABLE documents ADD COLUMN embedding_version VARCHAR(50) DEFAULT 'v1';

-- 迁移过程中的临时索引
CREATE INDEX ON documents_embedding_v2 USING hnsw (embedding vector(3072));
```

```python
class VersionedVectorStore:
    """支持多版本 embedding 的向量存储"""
    
    def __init__(self, milvus_client, current_version: str = "v1"):
        self.client = milvus_client
        self.current_version = current_version
    
    def insert(self, chunks: list[dict], doc_id: str, version: str):
        """写入时使用当前版本"""
        version_col = f"embedding_{version}"
        
        vectors = [{
            "id": chunk["id"],
            "document_id": doc_id,
            "chunk_index": chunk["index"],
            version_col: embedding_service.encode(chunk["text"], version=version)
        } for chunk in chunks]
        
        self.client.insert(collection_name="chunks", data=vectors)
    
    def search(self, query: str, version: str, top_k: int = 10) -> list[dict]:
        """检索时只查同版本的向量"""
        embedding = embedding_service.encode(query, version=version)
        version_col = f"embedding_{version}"
        
        return self.client.search(
            collection_name="chunks",
            data=[embedding],
            output_fields=["document_id", "chunk_id", "chunk_index"],
            limit=top_k
        )
    
    def migrate_doc(self, doc_id: str, target_version: str) -> bool:
        """
        渐进式迁移：用户访问时触发重建
        不是一次性全量迁移，而是按需迁移
        """
        chunks = db.fetch_chunks(doc_id)
        for chunk in chunks:
            new_vector = embedding_service.encode(chunk["text"], version=target_version)
            self.client.upsert(collection_name="chunks", data=[{
                "id": chunk["id"],
                "document_id": doc_id,
                "embedding_v2": new_vector  # v2 是新版本
            }])
        
        db.update_doc_embedding_version(doc_id, target_version)
        return True
```

**信号三：上了三套数据库，排障全靠经验猜。**

PostgreSQL 出问题了要排障，Redis 出问题了要排障，向量库也要看日志。三套系统的故障定位没有统一链路，全靠经验猜。

**解法**：给所有数据库操作加统一的 trace_id，用 OpenTelemetry 串起来：

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
import logging

# 配置 OpenTelemetry
provider = TracerProvider()
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)
logger = logging.getLogger("ai_app")

def traced_search(query: str, user_id: str, trace_id: str = None):
    """所有数据库操作绑定同一个 trace_id"""
    if trace_id:
        span = tracer.start_span("vector_search", context=trace.set_span_in_context(trace_id))
    else:
        span = tracer.start_span("vector_search")
    
    span.set_attribute("user_id", user_id)
    span.set_attribute("query_length", len(query))
    
    try:
        # PG：验证用户权限
        pg_start = time.time()
        user = db.query("SELECT * FROM users WHERE id = %s", user_id)
        span.set_attribute("pg_user_lookup_ms", (time.time() - pg_start) * 1000)
        
        # Redis：检查限流
        redis_start = time.time()
        rate_check = rate_limiter.check_and_consume(user_id, est_tokens=1000)
        span.set_attribute("redis_rate_check_ms", (time.time() - redis_start) * 1000)
        
        if not rate_check["allowed"]:
            span.set_attribute("error", "rate_limit_exceeded")
            span.end()
            return {"error": "rate_limit", "detail": rate_check["reason"]}
        
        # Redis：查检索缓存
        cache_start = time.time()
        cache_key = f"retrieval:{user_id}:{hash(query)}"
        cached = redis.get(cache_key)
        span.set_attribute("redis_cache_ms", (time.time() - cache_start) * 1000)
        span.set_attribute("cache_hit", cached is not None)
        
        if cached:
            results = json.loads(cached)
            span.set_attribute("result_count", len(results))
            span.end()
            return results
        
        # 向量库：检索
        vec_start = time.time()
        embedding = embedding_service.encode(query)
        vector_results = milvus_client.search(
            collection_name="chunks",
            data=[embedding],
            limit=10
        )
        span.set_attribute("vector_search_ms", (time.time() - vec_start) * 1000)
        span.set_attribute("vector_result_count", len(vector_results))
        
        # PG：校验文档有效性
        pg_start = time.time()
        doc_ids = [r['document_id'] for r in vector_results]
        valid_docs = db.query("""
            SELECT id, title, content FROM documents
            WHERE id = ANY(%s) AND status = 'published'
        """, doc_ids)
        span.set_attribute("pg_validate_ms", (time.time() - pg_start) * 1000)
        
        valid_ids = {d['id'] for d in valid_docs}
        results = [r for r in vector_results if r['document_id'] in valid_ids]
        
        # Redis：写入缓存
        redis.setex(cache_key, 3600, json.dumps(results))
        
        span.set_attribute("final_result_count", len(results))
        span.end()
        return results
        
    except Exception as e:
        span.set_attribute("error", str(e))
        span.record_exception(e)
        span.end()
        raise
```

这条 trace 可以串起：用户权限查询（PG） → 限流检查（Redis） → 缓存查询（Redis） → 向量检索（Milvus） → 文档校验（PG） → 缓存写入（Redis）。任何一个环节出问题，都能从 trace_id 定位。

---

## 五、真实项目里的坑：从五个扩到八个

### 5.1 坑一：向量库和业务库的数据不同步（幽灵数据）

详见 4.1 节。

### 5.2 坑二：embedding 版本升级后，向量库里的旧向量全废

详见 4.2 节。

### 5.3 坑三：Redis 缓存 LLM 响应，命中率低到怀疑人生

详见 2.2 节。补充一个实战数据：

一家做企业知识库的团队，上线初期缓存命中率 3%，每天 LLM 调用费用 800 元。优化为检索结果缓存 + 热点问题预热后，命中率提升到 28%，每天 LLM 费用降到 380 元。**三个月省下的 LLM 费用够买两台向量检索服务器。**

### 5.4 坑四：向量检索结果和 PostgreSQL 过滤条件不匹配

向量库检索出来的 top-10 文档，经过 PostgreSQL 权限过滤后，只剩 3 个。用户实际看到的回答质量远低于预期。

**根因**：向量相似度和业务相关性是两回事。高相似度不代表用户有权限看，也不代表这段话真的回答了用户的问题。

**解法**：不要先检索再过滤，而是**先过滤再检索**：

```python
def permission_aware_search(query: str, user_id: str, top_k: int = 10) -> list[dict]:
    """
    正确的检索顺序：
    1. 先查用户能访问哪些文档（PG 权限过滤）
    2. 把可访问的 doc_id 作为候选集
    3. 在候选集内做向量检索
    """
    # 1. PG：获取用户可访问的文档范围（可能 5000 条）
    accessible_docs = db.query("""
        SELECT d.id, d.title, d.department
        FROM documents d
        JOIN user_doc_access uda ON uda.doc_id = d.id
        WHERE uda.user_id = %s
          AND d.status = 'published'
          AND d.created_at > NOW() - INTERVAL '1 year'
    """, user_id)
    
    if not accessible_docs:
        return []
    
    accessible_ids = [doc['id'] for doc in accessible_docs]
    
    # 2. 向量库：限制在可访问范围内检索
    embedding = embedding_service.encode(query)
    
    # 如果可访问文档数量适中（< 5000），用 IN filter
    if len(accessible_ids) <= 5000:
        results = milvus_client.search(
            collection_name="chunks",
            data=[embedding],
            filter=f"document_id in {accessible_ids}",
            limit=top_k
        )
    else:
        # 如果可访问文档很多，先用向量库粗筛，再 PG 二次过滤
        raw_results = milvus_client.search(
            collection_name="chunks",
            data=[embedding],
            limit=top_k * 5  # 多召回一些
        )
        
        doc_ids = [r['document_id'] for r in raw_results]
        valid_ids_set = set(doc_ids) & set(accessible_ids)
        
        results = [r for r in raw_results if r['document_id'] in valid_ids_set][:top_k]
    
    return results
```

### 5.5 坑五：上了三套数据库，运维扛不住

详见 2.2 节 trace 方案。

### 5.6 坑六：向量库 metadata 膨胀，查询越来越慢

向量库里存了太多 metadata（完整文本、超大 JSON），每次查询都要返回这些数据，网络传输和解析耗时远超向量检索本身。

**解法**：向量库只存向量和必要 ID，完整数据全部从 PostgreSQL 读取。

```python
# Milvus 的 output_fields 只返回必要的字段
results = milvus_client.search(
    collection_name="chunks",
    data=[embedding],
    limit=10,
    output_fields=["chunk_id", "document_id", "chunk_index"]
    # 不返回 chunk_text，让 PG 来提供
)

# 然后在 PG 里批量拿完整内容
doc_ids = list({r['document_id'] for r in results})
chunks_map = {
    row['id']: row['chunk_text']
    for row in db.query("SELECT id, chunk_text FROM embeddings WHERE id = ANY(%s)", doc_ids)
}
```

### 5.7 坑七：pgvector 的 HNSW 索引在更新后变慢

pgvector 不支持 HNSW 在线更新。文档更新后，向量库里对应的 embedding 更新了，但索引不会自动重建。随着时间推移，索引和实际数据越来越不一致，查询精度下降。

**解法**：文档更新时，用 `DELETE + INSERT` 而不是 `UPDATE`：

```python
# 错误的做法：UPDATE 向量（索引不会更新）
cur.execute("""
    UPDATE embeddings
    SET embedding = %s, chunk_text = %s
    WHERE id = %s
""", (new_vector, new_text, chunk_id))

# 正确的做法：删掉重建
cur.execute("DELETE FROM embeddings WHERE id = %s", (chunk_id,))
cur.execute("""
    INSERT INTO embeddings (id, document_id, chunk_index, chunk_text, embedding)
    VALUES (%s, %s, %s, %s, %s)
""", (chunk_id, doc_id, chunk_index, new_text, new_vector))
# HNSW 索引会自动包含新数据
```

**如果向量数据量大，更新频繁**，用 pgvector 的 concurrent index 构建方式：

```sql
-- 创建索引时加 CONCURRENTLY，避免锁表
CREATE INDEX CONCURRENTLY idx_emb_hnsw ON embeddings
USING hnsw (embedding vector_cosine_ops);
```

### 5.8 坑八：PostgreSQL 连接池被打满

向量检索和业务查询共用 PostgreSQL 连接池。embedding 服务突发流量时，连接池被打满，业务查询全部超时。

**解法**：分离连接池，向量相关操作和业务操作分开：

```python
from psycopg2 import pool

# 业务连接池（小，高优先级）
business_pool = pool.ThreadedConnectionPool(
    minconn=5, maxconn=20,
    database="aiapp", user="admin", host="localhost"
)

# 向量/embedding 连接池（大，低优先级）
vector_pool = pool.ThreadedConnectionPool(
    minconn=2, maxconn=50,
    database="aiapp", user="admin", host="localhost"
)

# 业务查询用 business_pool
with business_pool.getconn() as conn:
    user = conn.execute("SELECT * FROM users WHERE id = %s", user_id)

# 向量写入用 vector_pool（可降级）
try:
    with vector_pool.getconn() as conn:
        conn.execute("INSERT INTO embeddings ...", chunk)
except pool.too-many-connections:
    logger.warning("向量写入降级，等待重试")
    time.sleep(1)
    # 重试或写入消息队列异步处理
```

---

## 六、数据迁移：从 pgvector 迁到 Milvus 实战

什么时候该迁移？数据量接近 500 万，或者 PostgreSQL 的查询延迟开始明显上升（> 150ms）。

迁移策略不是停机全量迁移，而是**双写 + 灰度切换**：

```python
class DualWriteVectorStore:
    """
    双写方案：pgvector 和 Milvus 同时写入
    灰度切换：先用 Milvus 查询，fallback 到 pgvector
    """
    
    def __init__(self, pg_conn, milvus_client):
        self.pg = pg_conn
        self.milvus = milvus_client
        self.use_milvus = False
    
    def insert(self, doc_id: str, chunks: list[dict]):
        vectors = []
        for chunk in chunks:
            vector = embedding_service.encode(chunk["text"])
            
            # 写 pgvector（永久保留，作为 fallback）
            cur = self.pg.cursor()
            cur.execute("""
                INSERT INTO embeddings (id, document_id, chunk_index, chunk_text, embedding)
                VALUES (%s, %s, %s, %s, %s)
            """, (chunk["id"], doc_id, chunk["index"], chunk["text"], vector))
            
            # 双写 Milvus（灰度阶段）
            if self.use_milvus:
                vectors.append({
                    "id": chunk["id"],
                    "document_id": doc_id,
                    "vector": vector
                })
        
        if vectors and self.use_milvus:
            self.milvus.insert(collection_name="chunks", data=vectors)
    
    def search(self, query: str, top_k: int = 10) -> list[dict]:
        embedding = embedding_service.encode(query)
        
        if self.use_milvus:
            try:
                # 优先走 Milvus
                results = self.milvus.search(
                    collection_name="chunks",
                    data=[embedding],
                    limit=top_k
                )
                return results
            except Exception as e:
                logger.warning(f"Milvus 查询失败，fallback pgvector: {e}")
                # Milvus 故障时自动降级到 pgvector
        
        # pgvector fallback
        cur = self.pg.cursor()
        cur.execute("""
            SELECT e.id, e.document_id, e.chunk_text,
                   1 - (embedding <=> %s) AS similarity
            FROM embeddings e
            JOIN documents d ON d.id = e.document_id
            WHERE d.status = 'published'
            ORDER BY embedding <=> %s
            LIMIT %s
        """, (embedding, embedding, top_k))
        
        return cur.fetchall()
    
    def enable_milvus(self):
        """灰度开启：迁移历史数据后开启"""
        self.use_milvus = True
        logger.info("Milvus 查询已启用")

# 灰度迁移步骤：
# 1. 部署 DualWriteVectorStore，业务不感知
# 2. 后台跑历史数据迁移脚本（不影响线上）
# 3. 观察 Milvus 稳定性，确认无误
# 4. 调用 enable_milvus()，完全切换到 Milvus
```

---

## 七、成本对比：三个方案的5年TCO

不考虑成本只谈架构是耍流氓。三个方案的5年TCO（Total Cost of Ownership）：

**方案一：一套 PostgreSQL（pgvector）**

- 服务器：AWS r6g.2xlarge（32GB RAM，8 vCPU），月费用约 500 元
- 数据量上限：约 500 万向量（单服务器）
- 5 年费用：约 3 万元
- 适合：初创项目，预算有限，数据量可控

**方案二：PostgreSQL + Redis + Qdrant**

- PG 服务器：AWS r6g.xlarge（16GB RAM），月费用 250 元
- Redis：AWS ElastiCache 2GB，月费用 100 元
- Qdrant：AWS r6g.2xlarge（32GB RAM），月费用 500 元
- 5 年费用：约 10 万元
- 适合：中等规模，数据量 500 万 - 5000 万

**方案三：PostgreSQL + Redis + Milvus 集群**

- PG 服务器：AWS r6g.2xlarge，月费用 500 元
- Redis：AWS ElastiCache 4GB，月费用 200 元
- Milvus 集群（3 节点）：AWS r6g.4xlarge × 3，月费用 3000 元
- 运维人力：需要专职 DBA，约 3 万元/年
- 5 年费用：约 40 万元
- 适合：大规模企业用户，数据量 5000 万以上

**结论**：能用一套解决的不要上三套。方案一和方案二的差距不只是服务器费用，还有运维复杂度和故障排查时间。选方案三的唯一理由是数据量真的到了那个规模。

---

## 八、一张图说清楚选型决策

```
第一步：向量数据量多大？
├── < 100万        → pgvector 就够了，别折腾
├── 100万 ~ 5000万  → Qdrant / pgvector 都可以，看团队能力
└── 5000万以上      → Milvus（集群方案准备好预算）

第二步：查询里有多少是带字段过滤的混合查询？
├── > 30% 混合过滤  → pgvector 有明显优势（一条 SQL 搞定）
├── 纯向量检索      → 专用向量库更强（性能优势明显）
└── 热点问题+向量检索 → Redis 热路径 + 向量库兜底

第三步：团队能运维几套数据库？
├── 只有 PG 经验    → pgvector + Redis 就够了，够稳
├── 有 K8s + 分布式经验 → Qdrant 可以上
└── 有专业 DBA + 运维团队 → 可以分库分服按场景选型
```

**最终建议**：

- 起步阶段（向量 < 50万）：PostgreSQL + pgvector + Redis，三合一最稳
- 增长阶段（50万 ~ 500万）：PostgreSQL 做业务，Qdrant 做向量，Redis 跑限流
- 规模化阶段（500万+）：Milvus 分布式接管向量，PostgreSQL 专注业务，Redis 保留

数据库选型没有银弹，但**能一套解决的问题不要用两套**。AI 应用的复杂度已经够高了，数据库层每多一套系统，就是多一个故障点和运维负担。先把事情做对，再考虑做复杂。

---

## 附：快速对比表

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| 原型 / 小规模 RAG | PostgreSQL + pgvector | 一套解决，够用 |
| 中型 RAG + 混合查询多 | PostgreSQL + Redis + Qdrant | PG 做业务，Qdrant 做检索 |
| 大规模企业知识库 | PostgreSQL + Redis + Milvus | Milvus 分布式扩展，PG 做元数据 |
| 在线客服（低延迟要求） | PostgreSQL + Redis | 热点问题走 Redis，向量库可省略 |
| 多模态检索 | PostgreSQL + Milvus | pgvector 不支持多模态 |
| 预算有限 + 数据量中等 | PostgreSQL（pgvector）+ Redis | 成本最低，运维最简 |
