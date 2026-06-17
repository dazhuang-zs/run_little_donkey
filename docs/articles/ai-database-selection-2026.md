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

---

## 二、三种数据库的核心分工

### 2.1 PostgreSQL：业务数据的事实标准

AI 应用里的 PostgreSQL 承担三类职责：

**用户和业务元数据**：用户表、订阅计划、API Key 映射、Token 用量记录。这些数据有强 schema 定义，有关联查询需求，有事务要求。

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
    vector_ids UUID[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**混合查询的执行器**：当你要"查询某用户的所有文档，按创建时间排序，然后对某个向量做相似度检索"，PostgreSQL + pgvector 可以用一条 SQL 完成。但纯向量库做不到关联过滤这一层。

**会话和历史记录**：对话历史本身是半结构化的，用 JSONB 字段存储最灵活。

```sql
-- 会话表，消息用 JSONB
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    messages JSONB DEFAULT '[]',
    context_window_used INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 追加消息的正确做法（不是每次全量更新）
UPDATE conversations
SET messages = jsonb_insert(
        messages,
        ARRAY[to_jsonb(array_length(messages, 1))::text],
        '{"role": "user", "content": $1, "timestamp": $2}'
    ),
    context_window_used = context_window_used + $3
WHERE id = $4;
```

### 2.2 Redis：AI 应用的缓存层，但它比你想象的脆弱

Redis 在 AI 应用里有三个合法用途：

**Token 配额计数器**：这个最稳。TPM/RPM 限流用 Redis 原子操作，比数据库快两个数量级。

```python
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

def check_and_increment_tpm(user_id: str, tokens_used: int, window_seconds: int = 60) -> bool:
    key = f"tpm:{user_id}"
    current = r.get(key)
    
    if current is None:
        r.setex(key, window_seconds, tokens_used)
        return True
    
    if int(current) + tokens_used > 1_000_000:  # TPM 限制
        return False
    
    r.incrby(key, tokens_used)
    return True
```

**LLM 输出结果缓存（但有条件）**：缓存命中前提是"语义等价的问题产生相同的 embedding"。这在以下场景成立：

- 相同用户的相同问题短时间内重复提问（embedding 几乎相同）
- 企业内部知识库问答，固定问题集合

这个场景用 Redis 没问题，但别指望用它缓存所有 LLM 输出。

**Embedding 服务的连接池和速率控制**：embedding 生成通常是独立服务，Redis 可以做令牌桶限流，保护后端模型服务不被冲垮。

```python
# embedding 请求的分布式限流（保护 embedding 服务）
def embed_with_rate_limit(text: str, user_id: str) -> list[float]:
    rate_limit_key = f"embed_rate:{user_id}"
    
    # 每秒最多 60 个请求
    if not r.set(rate_limit_key, 1, nx=True, ex=1):
        count = r.incr(rate_limit_key)
        if count > 60:
            raise Exception("Embedding rate limit exceeded")
    
    return embedding_service.encode(text)
```

**Redis 在 AI 应用里的三个错误用法**：

第一，用 Redis 存会话历史全文。会话历史通常有几千 token，Redis String 存这个没有意义，内存开销大，还没法做语义检索。应该存 PostgreSQL JSONB。

第二，用 Redis 做向量存储。Redis 7.0 推出了 Vector Set，但性能、生态、运维工具都比不过专用向量库。中等规模以上（百万向量）就别考虑了。

第三，假设 Redis 缓存命中率很高。AI 场景的请求重复率远低于传统 Web 请求。用户不会问同一个问题两次，除非你是客服机器人。

### 2.3 向量数据库：RAG 的根基，但它只该管一件事

向量库的核心职责就一件：**给定一个 query embedding，返回最相似的 K 个文档 chunk。**

这是它唯一比 PostgreSQL + pgvector 强的地方。不是存储，不是元数据管理，不是权限控制——那些交给 PostgreSQL。

```
向量库里的数据模型：

{
  id: "uuid-of-chunk-1",
  vector: [0.123, -0.456, 0.789, ...],  # 1536 维
  document_id: "uuid-of-doc-1",           # 关联回 PG 的 document_id
  chunk_index: 0,
  content_preview: "第一段文本的预览..."
}
```

向量库不管内容怎么存储，只管检索。

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
- 查询里有大量结构化字段过滤条件（部门、时间、状态等）

**pgvector 的索引选择**：

```sql
-- 小数据量（<10万），追求查询速度：HNSW
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops);

-- 大数据量（>100万），资源有限：IVFFlat
CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

HNSW 查询快，但构建慢、吃内存。IVFFlat 构建快，但查询精度和速度略逊。按数据量选，别瞎选。

### 3.3 什么时候选专用向量库（Milvus / Qdrant）

**场景：数据量大（千万级以上），检索性能要求高，且业务过滤条件和向量查询相对独立。**

Milvus 的架构天然适合横向扩展。QueryNode、DataNode、IndexNode 分开，资源不够就加节点。pgvector 的扩展天花板是单台 PostgreSQL 的硬件上限。

```python
# Milvus 连接示例
from pymilvus import MilvusClient

client = MilvusClient(uri="http://localhost:19530")

# 搜索
results = client.search(
    collection_name="document_chunks",
    data=[query_embedding],
    filter='status == "published" and department == "tech"',
    limit=10,
    output_fields=["chunk_text", "document_id", "chunk_index"]
)
```

**Milvus 适合的场景**：

- 数据量预计快速增长（未来 6 个月到千万级）
- 需要 GPU 加速向量检索
- 多模态检索（文本 + 图像 + 音频）
- 团队有能力运维分布式系统

**Qdrant 是更好的折中**：如果你觉得 pgvector 太弱、Milvus 太重，Qdrant 是中大型规模下的首选。Rust 实现，性能稳定，运维比 Milvus 简单，生态（LangChain、LlamaIndex）支持完整。

### 3.4 一张决策表

| 维度 | pgvector | Milvus | Qdrant |
|------|---------|--------|--------|
| 数据量 | <1000万 | 任意规模 | <1亿 |
| 查询延迟 | 50-200ms | <50ms | <50ms |
| 混合查询（SQL过滤） | 原生支持 | 需额外实现 | 需额外实现 |
| 运维复杂度 | 低（共用 PG） | 高 | 中 |
| 横向扩展 | 受 PG 限制 | 原生分布式 | 一般 |
| GPU 加速 | 不支持 | 支持 | 不支持 |
| 推荐场景 | 中小 RAG、混合查询多 | 企业级大规模检索 | 中大型 RAG |

---

## 四、真正的架构选择：什么时候合、什么时候分

现在进入核心问题：PostgreSQL + Redis + 向量库三套组合，**什么时候该分开部署，什么时候可以合并。**

### 4.1 可以合并的情况

**PostgreSQL 单独扛住业务数据，向量库独立，向量库不需要感知业务表结构。**

这是最小可行架构：

```
PostgreSQL：用户表、文档元数据、会话历史、Token 用量
Redis：限流计数、embedding 服务限流、LLM 结果缓存（可选）
Milvus / Qdrant：文档 chunk 向量、只存向量和 chunk_id
```

文档 chunk 更新时，更新流程是：

```python
# 文档更新时的完整流程
def update_document(doc_id: str, new_content: str):
    # 1. 更新 PG 里的文档状态
    doc = db.query("UPDATE documents SET status='updating' WHERE id=$1", doc_id)
    
    # 2. 删除旧向量
    milvus_client.delete(collection_name="chunks", filter=f"document_id='{doc_id}'")
    
    # 3. 重新分 chunk 并插入向量
    chunks = chunker.split(new_content)
    for i, chunk in enumerate(chunks):
        vector = embedding_service.encode(chunk)
        milvus_client.insert(collection_name="chunks", data=[{
            "id": str(uuid4()),
            "document_id": doc_id,
            "chunk_index": i,
            "content_preview": chunk[:200],
            "embedding": vector
        }])
    
    # 4. 更新 PG 里的 chunk 计数和状态
    db.query("UPDATE documents SET chunk_count=$1, status='published' WHERE id=$2", 
             len(chunks), doc_id)
```

这个流程里，向量库只存向量和 document_id，业务语义全在 PostgreSQL。两边各司其职，不需要合。

### 4.2 不该合并的情况

**第一种：向量化数据量极小时，硬上独立向量库是过度设计。**

小于 10 万条向量的场景，用 pgvector 就够了。架一套 Milvus，运维成本翻倍，收益几乎为零。

**第二种：实时性要求极高的场景，向量库的检索延迟不可接受。**

比如在线客服，每次请求都要"先检索向量再生成"，端到端延迟至少 300ms起步。如果业务要求 < 100ms，向量检索这步就是瓶颈，应该用 Redis 缓存热点问题的答案，而不是每次都走向量库。

```python
# 热点问答缓存：向量库兜底，Redis 做热路径
def answer_question(user_question: str, user_id: str) -> str:
    # 先用精确 hash 查 Redis（O(1) 延迟）
    question_hash = hash_text(user_question)
    cache_key = f"qa:hot:{question_hash}"
    cached = redis.get(cache_key)
    if cached:
        return cached
    
    # 走向量检索（慢路径）
    embedding = embedding_service.encode(user_question)
    results = milvus_client.search(
        collection_name="knowledge_base",
        data=[embedding],
        limit=3
    )
    
    # 组装上下文，生成回答
    answer = llm.answer(user_question, results)
    
    # 热点问题写入缓存（TTL 1小时）
    if is_popular_question(user_question):
        redis.setex(cache_key, 3600, answer)
    
    return answer
```

### 4.3 什么时候 PostgreSQL 单独全搞定

pgvector 支持向量 + 关系型混合存储，如果你满足以下条件，一套 PostgreSQL 够了：

- 数据量 < 500 万条向量
- 不需要向量库的分布式扩展能力
- 查询里 50% 以上是带字段过滤的混合查询
- 团队 PostgreSQL 运维已经非常成熟

```python
# 单 PostgreSQL 搞定一切的示例
from pgvector.psycopg2 import register_vector
import psycopg2

conn = psycopg2.connect(database="aiapp", user="admin", password="", host="localhost")
register_vector(conn)

def hybrid_search(query_text: str, user_dept: str, top_k: int = 5):
    embedding = embedding_service.encode(query_text)
    
    cur = conn.cursor()
    cur.execute("""
        SELECT d.id, d.title, d.content,
               1 - (e.embedding <=> %s) AS similarity
        FROM documents d
        JOIN embeddings e ON e.document_id = d.id
        WHERE d.department = %s
          AND d.status = 'published'
        ORDER BY e.embedding <=> %s
        LIMIT %s
    """, (embedding, user_dept, embedding, top_k))
    
    return cur.fetchall()
```

一套数据库搞定，运维最简，事务一致性天然保证。**这是最被低估的方案**，太多团队还没试过就上了三套系统。

---

## 五、真实项目里的五个坑，每个都有人踩过

### 坑一：向量库和业务库的数据不同步

文档删了，但向量库里还有 chunk。查询结果返回了一个不存在的文档。

**根因**：两边独立更新，没有事务保证。

**解法**：把 document_id 作为唯一信任源。向量库查询结果里带上 document_id，查 PostgreSQL 做二次校验，双保险：

```python
def safe_retrieve_chunks(document_ids: list[str]) -> list[dict]:
    # 1. 从向量库拿到 chunk_id 和 document_id
    raw_chunks = milvus_client.query(collection_name="chunks", 
                                       ids=document_ids)
    
    # 2. 在 PostgreSQL 里验证 document 仍然有效
    valid_ids = db.query(
        "SELECT id FROM documents WHERE id = ANY($1) AND status = 'published'",
        document_ids
    )
    valid_ids_set = {row['id'] for row in valid_ids}
    
    # 3. 只返回经过验证的 chunk
    return [chunk for chunk in raw_chunks if chunk['document_id'] in valid_ids_set]
```

### 坑二：embedding 版本升级后，向量库里的旧向量全废

换了 embedding 模型（text-embedding-3-small → text-embedding-3-large），维度从 1536 变成 3072。向量库里有 500 万条旧向量，直接重建要 3 天。

**解法**：在文档元数据里记录 embedding_version，向量库只查同版本的文档：

```sql
ALTER TABLE documents ADD COLUMN embedding_version VARCHAR(50) DEFAULT 'v1';
```

```python
def search_with_version(query_text: str, user_id: str) -> list[dict]:
    user = db.get_user(user_id)
    embedding_version = user.get('embedding_version', 'v1')
    
    embedding = get_embedding_for_version(query_text, embedding_version)
    
    return milvus_client.search(
        collection_name="chunks",
        filter=f"embedding_version = '{embedding_version}'",
        data=[embedding]
    )
```

每次换 embedding 模型，不是全量重建，而是**渐进式迁移**：新文档用新版本，老文档在用户访问时触发重建。

### 坑三：Redis 缓存 LLM 响应，命中率低到怀疑人生

设了 1 小时 TTL，上线一周缓存命中率 3%。

**根因**：AI 应用的请求重复率天然低。同一用户短时间内问同样问题的概率极小。

**解法**：不要缓存 LLM 完整响应，改为缓存**检索结果**。向量库检索的结果是稳定的，同一文档 chunk 的 top-K 检索结果基本一致：

```python
# 缓存检索结果，而不是生成结果
def cached_vector_search(query: str, user_id: str) -> list[dict]:
    query_hash = hashlib.md5(query.encode()).hexdigest()
    cache_key = f"retrieve:{user_id}:{query_hash}"
    
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    embedding = embedding_service.encode(query)
    results = milvus_client.search(collection_name="chunks", data=[embedding], limit=10)
    
    # 缓存检索结果（1小时），不缓存生成结果
    redis.setex(cache_key, 3600, json.dumps(results))
    
    return results
```

这样即使 embedding 版本变了，下次请求会重新检索，缓存自动失效。不会有"文档更新了但缓存还是旧的"问题。

### 坑四：向量检索结果和 PostgreSQL 过滤条件不匹配

向量库检索出来的 top-10 文档，经过 PostgreSQL 权限过滤后，只剩 3 个。实际的召回质量远低于预期。

**解法**：不要先检索再过滤，而是**先过滤再检索**。

如果权限过滤后的候选集太大，在向量库里用 metadata filter 做预过滤，减少无效计算：

```python
# 错误做法：先检索再过滤
top_k_raw = milvus_client.search(data=[embedding], limit=50)
valid_ids = get_user_accessible_doc_ids(user_id)
filtered = [doc for doc in top_k_raw if doc['document_id'] in valid_ids]
# 可能最后只剩 3 个，实际 top-10 不够用

# 正确做法：先过滤 document_id 范围
accessible_docs = db.get_user_accessible_documents(user_id, limit=1000)
doc_ids = [doc['id'] for doc in accessible_docs]

if not doc_ids:
    return []

# 在向量库内用 IN filter 预过滤
results = milvus_client.search(
    collection_name="chunks",
    filter=f"document_id in {doc_ids[:500]}",  # PG 能批量查，Milvus 也能 IN
    data=[embedding],
    limit=10
)
```

### 坑五：上了三套数据库，运维扛不住

PostgreSQL 出问题了要排障，Redis 出问题了要排障，向量库也要看日志。三套系统的故障定位没有统一链路，全靠经验猜。

**解法**：给所有数据库操作加统一的 trace_id。向量库检索时记录 document_id，PostgreSQL 查询时记录 SQL 指纹，Redis 操作记录 key pattern。任何一次 AI 请求，从 trace_id 能串起三个系统的日志。

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def traced_search(query: str, user_id: str, trace_id: str):
    span = tracer.start_span("vector_search")
    span.set_attribute("trace_id", trace_id)
    span.set_attribute("user_id", user_id)
    
    try:
        embedding = embedding_service.encode(query)
        
        # 记录向量库检索
        results = milvus_client.search(
            collection_name="chunks",
            data=[embedding],
            limit=10
        )
        span.set_attribute("vector_result_count", len(results))
        
        # 记录 PG 校验
        doc_ids = [r['document_id'] for r in results]
        validated = pg_validate(doc_ids, user_id)
        span.set_attribute("pg_validated_count", len(validated))
        
        return validated
    finally:
        span.end()
```

---

## 六、一张图说清楚选型决策

```
问自己三个问题：

1. 向量数据量多大？
   ├── < 100万        → pgvector 就够了，别折腾
   ├── 100万 ~ 5000万  → Qdrant / pgvector 都可以
   └── 5000万以上      → Milvus
   （同时考虑：未来 6 个月增长到哪个量级？）

2. 查询里有多少是带字段过滤的混合查询？
   ├── > 30% 混合过滤  → pgvector 有明显优势
   ├── 纯向量检索      → 专用向量库更强
   └── 热点问题+向量检索 → Redis 缓存热路径 + 向量库兜底

3. 团队能运维几套数据库？
   ├── 只有 PG 经验    → pgvector + Redis 就够了
   ├── 有 K8s 经验     → Milvus / Qdrant 云原生部署
   └── 三套都能运维    → 可以按场景分，但必须有统一可观测性
```

**最终建议**：

- 起步阶段（向量 < 50万）：PostgreSQL + pgvector + Redis，三合一最稳
- 增长阶段（50万 ~ 500万）：PG 跑业务，Qdrant 跑向量，Redis 跑限流
- 规模化阶段（500万+）：Milvus 分布式接管向量，PG 专注业务，Redis 保留

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
