# TBase vs Redis：不是选谁，是选谁干什么

一个分布式HTAP数据库，一个内存键值存储。拿它们对比，不是谁更好，是谁干什么的边界在哪。

太多人把Redis当数据库用，结果踩坑踩到怀疑人生。也有人以为TBase能替代Redis做缓存，结果性能达不到预期。这篇文章把两者的定位、架构、事务模型、适用场景、踩坑案例全部拆开，帮你彻底搞清楚：**什么时候用TBase，什么时候用Redis，什么时候两个都要。**

---

## 一、根本定位：完全不同的两个物种

先看本质区别：

| 维度 | TBase（TDSQL PG版） | Redis |
|------|---------------------|-------|
| 数据库类型 | 分布式关系型HTAP数据库 | 内存键值存储/NoSQL |
| 存储介质 | 磁盘（SSD/HDD），数据持久化 | 内存为主，可选RDB/AOF持久化 |
| 事务模型 | 完整ACID，分布式2PC+全局时钟 | MULTI/EXEC批处理，不支持回滚 |
| 数据模型 | 关系型表，SQL标准 | 键值对+5种基础数据结构 |
| 查询能力 | 完整SQL，多表JOIN、聚合、子查询 | 仅KEY查找，无JOIN无聚合 |
| 扩展方式 | 水平分片，CN/DN/GTM分布式架构 | 主从复制+Cluster分片 |
| 设计目标 | 数据安全+强一致性+复杂查询 | 极低延迟+极高吞吐 |

一句话总结：**TBase是"存数据的地方"，Redis是"加速数据的地方"。**

这就像仓库和快递站的区别。仓库（TBase）要保证货物不丢、账目准确、能查能算。快递站（Redis）要保证取货快、响应迅速、随时能补货。你不会把快递站当仓库用，也不会用仓库做快递站的事。

---

## 二、架构拆解：各自怎么运转

### 2.1 TBase架构：Shared Nothing MPP

TBase基于PostgreSQL，采用Shared Nothing MPP架构，由三个核心组件组成：

- **Coordinator（CN）**：协调节点，接收客户端SQL请求，生成分布式执行计划，下发到DN执行，汇总结果返回。CN不存业务数据。
- **Datanode（DN）**：数据节点，存储分片数据，执行本地查询计划。数据按分片规则分布在多个DN上。
- **GTM（Global Transaction Manager）**：全局事务管理器，分配全局时间戳（GTS），保证分布式事务的全局一致性。

架构图：

```
客户端 → CN（协调节点，SQL解析+计划生成）
           ↓
    DN1    DN2    DN3    DN4（数据节点，分片存储+本地执行）
           ↓
         GTM（全局时钟，事务时间戳分配）
```

关键设计：

- **MVCC+全局时钟+2PC+SSI**：实现全局一致性分布式事务。这是TBase的核心创新点，避免了Percolator模型的提交开销问题。
- **双KEY均匀分布**：解决大商户数据倾斜问题（微信支付商户平台实战验证）。
- **Index Only Scan优化**：传统Web分页查询不再需要回表。
- **在线线性扩容**：不停业务，新增DN节点自动加入集群。

性能数据（TPCC测试）：
- 小规模集群超过300万 TPMTotal
- 单笔交易毫秒级完成
- 支撑微信支付50倍交易增长

### 2.2 Redis架构：单线程内存引擎

Redis的核心设计极其简洁：

- **单线程模型**：所有命令串行执行，避免锁竞争，保证原子性。
- **内存存储**：数据全部在内存，读写延迟微秒级。
- **多路复用I/O**：epoll/kqueue实现高并发网络处理。
- **可选持久化**：RDB（定时快照）或AOF（追加日志），两者都不是强持久化。

架构图：

```
客户端 → Redis单线程主进程（命令解析+执行+网络I/O）
           ↓
    RDB快照（定时） / AOF追加日志（可选）
           ↓
         磁盘（非实时，有数据丢失窗口）
```

Redis Cluster模式：
- 16384个哈希槽，分到多个节点
- 每个节点负责一部分槽
- 跨槽请求需要MOVED重定向
- 不支持跨槽事务（MULTI/EXEC只在本槽有效）

**关键认知**：Redis的单线程不是缺陷，是设计选择。内存操作速度极快，单线程反而避免了锁和上下文切换开销。瓶颈不在CPU，在网络I/O和内存容量。

---

## 三、事务模型：TBase完整ACID vs Redis"伪事务"

这是两者最本质的差异，也是最多人踩坑的地方。

### 3.1 TBase：完整ACID分布式事务

TBase的事务模型继承PostgreSQL，并扩展到分布式场景：

**原子性（Atomicity）**：2PC协议保证。Prepare阶段所有DN就绪，Commit阶段统一提交。任一DN失败，全局回滚。

**一致性（Consistency）**：全局时钟GTS保证时间戳单调递增，所有事务按GTS排序，保证全局一致性读。

**隔离性（Isolation）**：SSI（Serializable Snapshot Isolation）实现可串行化隔离级别，防止写偏序（write skew）异常。

**持久性（Durability）**：WAL日志+同步复制，保证已提交事务不丢失。

分布式事务流程：

```python
# TBase分布式事务伪代码
BEGIN TRANSACTION;

# 1. CN生成执行计划，下发到DN1和DN2
# 2. DN1执行本地操作，进入Prepare状态
# 3. DN2执行本地操作，进入Prepare状态
# 4. GTM分配全局时间戳GTS
# 5. 所有DN Prepare成功 → CN发送Commit
# 6. 任一DN Prepare失败 → CN发送Rollback

UPDATE accounts SET balance = balance - 100 WHERE id = 1;  # DN1
UPDATE accounts SET balance = balance + 100 WHERE id = 2;  # DN2

COMMIT;  # 全局2PC保证要么全部成功要么全部回滚
```

### 3.2 Redis：不是真正的事务

Redis的MULTI/EXEC本质是**命令批处理**，不是ACID事务：

| ACID特性 | Redis是否满足 | 原因 |
|----------|--------------|------|
| 原子性 | ❌ 不满足 | 命令失败不回滚，后续命令继续执行 |
| 一致性 | ⚠️ 部分满足 | 入队阶段语法错误会拒绝整个事务，但运行时错误不回滚 |
| 隔离性 | ⚠️ 部分满足 | 单线程保证事务执行期间不被打断，但WATCH只是乐观锁 |
| 持久性 | ❌ 不满足 | RDB/AOF都不是实时持久化，崩溃会丢数据 |

实测Redis事务的行为：

```bash
# 场景1：命令类型错误（语法级），整个事务拒绝
MULTI
SET key1 "value1"
LPUSH key1 "list_element"  # key1已经是string，LPUSH是list操作
EXEC
# 结果：整个事务被拒绝，key1保持原值

# 场景2：命令运行时错误，失败命令不回滚，后续命令继续执行
MULTI
SET key1 "value1"
INCR key1  # 对string做INCR会报错，但不会回滚SET
SET key2 "value2"  # 这条命令正常执行
EXEC
# 结果：key1 = "value1"（SET成功），key2 = "value2"（SET成功）
# INCR的错误被忽略，SET的结果没有被回滚！
```

**核心结论：Redis事务不支持回滚。失败了前面的操作不会撤销。这就是为什么Redis不适合做需要原子性的业务逻辑。**

有人会说"Redis有Lua脚本，Lua脚本保证原子性"。确实，Lua脚本在Redis中是原子执行的。但：

- Lua脚本只是"单次执行不被打断"，不是"失败自动回滚"
- Lua脚本中某个命令失败，后续命令继续执行
- Lua脚本超时（默认5秒）会被强制终止
- Lua脚本不能跨Redis Cluster节点

```lua
-- Lua脚本中的"伪原子性"
-- 如果第二行失败，第一行的结果不会被回滚
redis.call('SET', 'key1', 'value1')
redis.call('INCR', 'key1')  -- 失败了，但key1已经是value1了
redis.call('SET', 'key2', 'value2')  -- 继续执行
```

---

## 四、适用场景：谁干什么最合适

### 4.1 TBase适合的场景

**场景一：需要强一致性的核心业务数据**

订单、支付、账务、库存。这些数据丢了就是事故，不一致就是纠纷。必须用关系型数据库，必须ACID。

微信支付商户服务平台用TBase的例子：
- 千万级商户账单明细下载
- 复杂条件查询+统计分析
- 大商户数据倾斜（京东等单个商户数据量巨大）
- 单表TB级数据，需要在线扩容

**场景二：HTAP混合负载**

既要实时交易（OLTP），又要实时分析（OLAP）。比如：
- 交易系统需要实时写入订单
- 运营需要实时看GMV、转化率、地域分布
- 不想搭建单独的Hadoop/Spark分析集群

TBase的HTAP能力：同一套数据，同一个SQL引擎，同一套事务保证。交易和分析不再需要ETL同步。

**场景三：复杂SQL查询**

多表JOIN、子查询、窗口函数、聚合分析。Redis做不了这些。

```sql
-- TBase的复杂SQL能力：微信支付商户平台真实场景
SELECT 
    m.merchant_name,
    SUM(t.amount) AS total_amount,
    COUNT(*) AS transaction_count,
    AVG(t.amount) AS avg_amount,
    ROW_NUMBER() OVER (PARTITION BY m.region ORDER BY SUM(t.amount) DESC) AS rank
FROM merchants m
JOIN transactions t ON m.id = t.merchant_id
WHERE t.created_at >= '2024-01-01'
  AND t.status = 'completed'
GROUP BY m.merchant_name, m.region
HAVING SUM(t.amount) > 100000
ORDER BY total_amount DESC
LIMIT 20;

-- 这种查询在Redis里根本无法实现
```

### 4.2 Redis适合的场景

**场景一：缓存加速**

最经典的用法。业务数据在TBase/MySQL/PostgreSQL，热点数据在Redis加速读取。

```python
# 标准Cache Aside模式
def get_user(user_id):
    # 1. 先查Redis
    cached = redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    
    # 2. Redis没有，查TBase
    user = tbase.query("SELECT * FROM users WHERE id = ?", user_id)
    
    # 3. 写入Redis，设置过期时间+随机偏移防雪崩
    expire = 3600 + random.randint(0, 300)  # 1小时+0~5分钟随机
    redis.setex(f"user:{user_id}", expire, json.dumps(user))
    
    return user
```

**场景二：会话/Token存储**

短期、高频读写、允许丢失的数据。比如：
- 用户登录Session
- JWT Token缓存
- 临时验证码（5分钟过期）

这些数据丢了用户重新登录就好，不需要持久化。

**场景三：计数器和排行榜**

Redis的INCR命令原子递增，ZSET天然排序。做实时计数、排行榜极方便。

```python
# 文章阅读计数器
redis.incr(f"article:views:{article_id}")

# 实时排行榜
redis.zadd("leaderboard:daily", {user_id: score})
top10 = redis.zrevrange("leaderboard:daily", 0, 9, withscores=True)
```

**场景四：限流/配额**

令牌桶、滑动窗口限流，Redis+Lua实现极简。

```lua
-- Token Bucket限流器（Lua脚本保证原子执行）
local key = KEYS[1]           -- 限流key
local max_tokens = tonumber(ARGV[1])  -- 最大令牌数
local refill_rate = tonumber(ARGV[2]) -- 令牌填充速率（每秒）
local now = tonumber(ARGV[3])         -- 当前时间戳
local requested = tonumber(ARGV[4])   -- 本次请求令牌数

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or max_tokens
local last_refill = tonumber(bucket[2]) or now

-- 计算补充的令牌数
local elapsed = now - last_refill
local refill = elapsed * refill_rate
tokens = math.min(max_tokens, tokens + refill)

if tokens < requested then
    return 0  -- 拒绝请求
end

tokens = tokens - requested
redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
redis.call('EXPIRE', key, math.ceil(max_tokens / refill_rate) * 2)
return 1  -- 允许请求
```

### 4.3 不适合的场景（踩坑最多的地方）

**Redis不适合做的事：**

1. **核心业务数据的主存储** — 丢了就是事故，Redis持久化有丢失窗口
2. **需要ACID的事务逻辑** — Redis事务不支持回滚
3. **复杂关联查询** — 无JOIN、无子查询、无聚合
4. **大规模数据长期存储** — 内存成本是磁盘的10倍以上
5. **多维度权限过滤** — Redis没有WHERE条件，无法按角色/部门/状态过滤

**TBase不适合做的事：**

1. **微秒级延迟缓存** — 磁盘I/O+SQL解析，延迟在毫秒级而非微秒级
2. **超高频简单读写** — 单KEY读写Redis比TBase快10倍以上
3. **临时性短命数据** — Token、验证码等5分钟就过期，不值得入库
4. **实时排行榜/计数器** — SQL能做但性能远不如Redis ZSET/INCR

---

## 五、生产踩坑实录

### 5.1 Redis踩坑：5个真实事故复盘

**坑1：KEYS命令阻塞全集群**

事故现场：凌晨2点运营反馈后台慢，运维敲了`KEYS *`，Redis卡死10分钟，整个应用超时。

原因：KEYS是O(N)操作，遍历全量数据。百万级数据量下单次执行超过10秒。

正确做法：
```bash
SCAN 0 MATCH user:* COUNT 1000  # 渐进式遍历，不阻塞
rename-command KEYS ""           # 生产环境直接禁用KEYS命令
```

**坑2：内存无上限导致OOM雪崩**

事故现场：Redis突然极慢，排查发现内存打满触发OOM Killer，进程被系统强杀，缓存全丢，请求直击数据库，数据库扛不住也挂了。

原因：Redis默认不限制内存。不配maxmemory就用到物理上限为止。

正确做法：
```bash
maxmemory 2gb                # 必须设上限
maxmemory-policy allkeys-lru # 淘汰策略：最近最少使用
```

**坑3：缓存雪崩——大批KEY同时过期**

事故现场：秒杀活动QPS 5000，所有KEY在同一秒过期，5000请求瞬间打到数据库，数据库直接宕机，重启都没用（重启速度跟不上用户刷新速度）。

原因：KEY过期时间设成一样，失效时间点集中。

正确做法：
```python
expire = base_expire + random.randint(0, 600)  # 基础过期+随机偏移
redis.setex(key, expire, value)
```

**坑4：Redis主从切换数据丢失**

事故现场：Redis主从集群切换后，客户端发现部分数据丢失。排查发现脑裂——同时有两个主节点，不同客户端写不同主节点，切换后部分数据丢失。

原因：Sentinel判断主库故障的条件太松（min-slaves-to-write未配置），主库短暂网络抖动被误判为宕机，从库升主后原主库恢复，形成双主。

正确做法：
```bash
min-slaves-to-write 1        # 至少1个从库同步成功才允许写
min-slaves-max-lag 10        # 从库延迟超过10秒视为失联
```

**坑5：Redis事务不回滚导致业务异常**

事故现场：客服系统每天早上创建事件失败，重启后恢复，第二天又失败。排查发现Redis事务中increment返回null。

原因：Service层加了Spring @Transactional注解，Redis操作被包装进Spring事务（实际是MULTI/EXEC），increment在事务中返回null而非实际值。

教训：**不要把Redis事务和Spring数据库事务混用。Redis的MULTI/EXEC和数据库的ACID事务是两个完全不同的东西。**

### 5.2 TBase踩坑：真实案例

**坑1：大商户数据倾斜**

微信支付商户平台接入京东等大商户后，单个商户数据量巨大，传统MySQL分库分表后数据严重倾斜，大商户所在的分片负载远超其他分片。

TBase解决：双KEY分布机制，保证数据均匀分布到所有DN节点。同一商户的不同类型数据分散存储。

**坑2：分页查询性能瓶颈**

商户账单列表的分页查询在传统MySQL上需要回表扫描，深分页（offset大）性能急剧下降。

TBase解决：Index Only Scan优化，分页查询不再需要回表，直接从索引获取结果。百万级数据分页查询保持毫秒级响应。

**坑3：在线扩容不停业务**

业务增长后需要增加DN节点。传统方案需要停机迁移数据。

TBase解决：在线线性扩容，新增DN节点自动加入集群，数据自动再平衡，业务不停。

---

## 六、选型决策树：什么时候用谁

### 6.1 逐层判断

```
第一步：看数据性质
├── 丢了不可接受（订单/支付/账务） → TBase（强持久化+ACID）
├── 丢了可恢复（缓存/会话/排行榜） → Redis（内存加速）
└── 需要长期存+复杂查询 → TBase（SQL+JOIN+聚合）

第二步：看延迟要求
├── 微秒级（<1ms） → Redis（内存读写）
├── 毫秒级（1-50ms） → TBase或Redis都行
└── 秒级可接受 → TBase（复杂分析查询）

第三步：看查询复杂度
├── 单KEY读写 → Redis
├── 多表关联+条件过滤 → TBase
└── 向量相似性检索 → 专用向量库（pgvector/Milvus）

第四步：看数据量
├── <10GB → 单机PG+Redis就够了，TBase不需要
├── 10GB~1TB → TBase 3节点集群
└── >1TB → TBase多节点+水平扩展

第五步：看运维能力
├── 只有PG运维经验 → 单机PG+Redis，暂时不需要TBase
├── 有分布式数据库经验 → TBase集群
└── 有K8s运维能力 → 可以考虑云原生方案（TDSQL-C）
```

### 6.2 AI应用的具体选型

AI应用通常需要三套存储：

| 存储需求 | 推荐 | 理由 |
|----------|------|------|
| 业务数据（用户/订单/配置） | PostgreSQL或TBase | ACID+SQL+复杂查询 |
| 热点缓存/会话/限流 | Redis | 微秒级延迟+原子计数 |
| 向量检索（RAG） | pgvector起步 | 与PG生态一体，小规模够用 |

**起步阶段（<100万向量，<10GB业务数据）：**

一套PostgreSQL+Redis就够了。pgvector处理向量检索，Redis做缓存和限流。TBase在这个阶段用不上。

**中等规模（100万~5000万向量，10GB~1TB业务数据）：**

PostgreSQL换成TBase（业务数据需要水平扩展），Redis继续做缓存，向量检索看规模选pgvector或Qdrant。

**大规模（>5000万向量，>1TB业务数据）：**

TBase集群+Redis集群+Milvus集群。三套系统各司其职。

---

## 七、常见误区澄清

### 误区1："Redis也能持久化，所以可以当数据库用"

**真相：Redis持久化不是强持久化。**

- RDB：定时快照，两次快照之间的数据写入会丢失。配置`save 60 10000`意味着60秒内有10000次写才触发快照，如果第50秒崩溃，最近50秒的数据全丢。
- AOF：追加日志，fsync策略决定丢失窗口。`appendfsync everysec`每秒刷盘，最多丢1秒数据。`appendfsync no`交给操作系统，崩溃可能丢30秒数据。
- Redis官方文档明确说："Redis持久化设计的目标是尽量减少数据丢失，而不是保证零丢失。"

对比TBase：
- WAL日志同步写入，已提交事务零丢失
- RPO=0（Recovery Point Objective，恢复点目标为零）
- 分布式多副本，任一节点崩溃数据不丢

**结论：需要零丢失的场景，Redis不行，必须用关系型数据库。**

### 误区2："Redis事务够用了，MULTI/EXEC能保证原子性"

**真相：Redis事务不支持回滚。**

前面第三节已经实测证明。再强调一次：

```bash
# Redis事务：失败不回滚
MULTI
SET account:A 900    # 执行成功
SET account:B 1100   # 执行成功  
INCR account:A       # 对string做INCR会报错
EXEC
# 结果：A=900, B=1100。INCR的错误被忽略，SET没有被回滚。
# 这不是原子性！这只是"批处理"。
```

对比TBase的2PC分布式事务：

```sql
-- TBase事务：失败全部回滚
BEGIN;
UPDATE account SET balance = balance - 100 WHERE id = 'A';  -- A=900
UPDATE account SET balance = balance + 100 WHERE id = 'B';  -- B=1100
-- 如果第二条UPDATE失败（比如B不存在），第一条UPDATE也会回滚
-- A恢复为1000，B不变。这才是真正的原子性。
COMMIT;
```

### 误区3："TBase能替代Redis做缓存"

**真相：TBase的延迟在毫秒级，Redis在微秒级。差10倍以上。**

实测数据：
- Redis GET操作：0.1~0.5ms（微秒级，取决于网络）
- TBase简单SELECT：2~10ms（毫秒级，SQL解析+磁盘I/O）

缓存的核心价值是快。用TBase做缓存，比直接从磁盘查快不了多少（TBase本身就在磁盘上）。

### 误区4："Redis Cluster分布式等于TBase分布式"

**真相：Redis Cluster和TBase的分布式是两个概念。**

| 特性 | Redis Cluster | TBase |
|------|--------------|-------|
| 分布式目标 | 数据分片+高可用 | 分布式事务+水平扩展+HTAP |
| 跨分片事务 | ❌ 不支持 | ✅ 2PC全局事务 |
| 跨分片查询 | ❌ 需要在客户端聚合 | ✅ CN自动下发+汇总 |
| 数据一致性 | 最终一致 | 强一致（GTS+MVCC） |
| 扩容方式 | 手动迁移槽 | 自动再平衡 |

Redis Cluster的分布式是把数据切到不同节点，查询需要在客户端做聚合。TBase的分布式是CN自动协调，对应用层透明。

---

## 八、两者协同：最佳实践架构

大多数生产系统需要**两者配合**，而不是选一个替代另一个。

### 8.1 标准Cache Aside模式

```
写入流程：
应用 → TBase（持久化存储）→ 异步通知 → Redis（更新缓存）

读取流程：
应用 → Redis（查缓存）
  ├── 周中 → 返回数据（微秒级）
  └── 未中 → TBase（查数据库）→ 写入Redis → 返回数据（毫秒级）
```

关键细节：
- Redis过期时间加随机偏移，防雪崩
- TBase写入后不立即更新Redis（避免写放大），而是等下次读取时惰性填充
- 需要强一致性的场景不用Redis缓存（直接查TBase）

### 8.2 AI应用的标准架构组合

```
┌─────────────────────────────────────────────────────┐
│                    应用层                              │
│         Agent / API / 业务逻辑                        │
└──────────────┬──────────┬──────────┬─────────────────┘
               │          │          │
        ┌──────▼──┐ ┌─────▼───┐ ┌───▼────────┐
        │  Redis  │ │  TBase  │ │  pgvector   │
        │         │ │ (PG版)  │ │ /Milvus     │
        │ ·缓存   │ │         │ │             │
        │ ·会话   │ │ ·用户   │ │ ·向量检索   │
        │ ·限流   │ │ ·订单   │ │ ·语义搜索   │
        │ ·计数   │ │ ·配置   │ │ ·RAG召回    │
        │ ·排行   │ │ ·账务   │ │             │
        └─────────┘ │ ·日志   │ └─────────────┘
                    │ ·分析   │
                    └─────────┘

Redis负责加速，TBase负责存储和查询，向量库负责检索。
三者数据通过document_id关联，不重复存储。
```

数据不重复原则：
- 向量库只存chunk_id+embedding+document_id，不存完整文本
- Redis只存热点数据摘要，不存全量
- 完整数据全在TBase，其他两个只存必要索引/加速片段

### 8.3 数据一致性保障

当Redis和TBase并存时，核心问题是数据一致性。

```python
# 三种一致性策略，按业务需求选择

# 策略1：最终一致性（最常用，性能最好）
def write_with_cache(key, value):
    tbase.update(key, value)                     # 先写TBase
    redis.delete(key)                            # 删除Redis缓存（下次读取时惰性填充）
    # 不直接更新Redis，避免并发写导致旧值覆盖新值

# 策略2：强一致性（金融场景，放弃缓存加速）
def write_strong_consistency(key, value):
    tbase.update(key, value)                     # 只写TBase
    # 不缓存到Redis，所有读走TBase
    # 性能下降但保证零不一致

# 策略3：读后写一致性（大多数场景够用）
def read_after_write(key, value):
    tbase.update(key, value)                     # 先写TBase
    redis.setex(key, expire_with_random, value)  # 立即更新Redis
    # 短窗口可能不一致（TBase写入成功但Redis还没更新）
    # 但比策略1的"下次读取才更新"更快
```

选择建议：
- 90%场景用策略1（最终一致性+惰性填充）
- 金融/支付场景用策略2（不缓存，直接查TBase）
- 用户体验敏感的场景用策略3（写后立即更新Redis）

---

## 九、5年TCO成本对比

假设一个中等规模AI应用（日均10万用户，500万向量，100GB业务数据）：

| 项目 | 方案A：PG+Redis | 方案B：TBase+Redis | 方案C：TBase+Redis+Milvus |
|------|-----------------|-------------------|--------------------------|
| 服务器成本/年 | 2万（1台PG+1台Redis） | 5万（3节点TBase+1台Redis） | 8万（3节点TBase+1台Redis+3节点Milvus） |
| 运维人力/年 | 0.5万（PG运维成熟） | 1万（分布式运维门槛更高） | 2万（三套系统运维） |
| 内存成本/年 | 0.5万（Redis 16GB） | 0.5万（Redis 16GB） | 1万（Redis+Milvus内存） |
| 5年总成本 | **~3万** | **~8万** | **~16万** |
| 扩容上限 | 单机瓶颈（~200GB） | 水平扩展（无上限） | 水平扩展（无上限） |

**结论：**
- 起步阶段（<100GB业务数据）：PG+Redis，3万搞定
- 中等规模（100GB~1TB）：TBase+Redis，8万够用
- 大规模（>1TB+5000万向量）：TBase+Redis+Milvus，16万起

**不要提前过度投资。** 数据量不到瓶颈时，单机PG+Redis是最省的方案。TBase的水平扩展能力只在数据量真的到TB级时才有价值。

---

## 十、总结：一句话决策

**TBase vs Redis 不是选择题，是分工题。**

| 需求 | 用什么 |
|------|--------|
| 数据不能丢，查询要复杂 | TBase（或单机PG） |
| 读得要快，写得要快，丢了能恢复 | Redis |
| 两者都要 | TBase+Redis，Cache Aside模式 |
| 只有一个，选谁 | 选TBase（数据安全优先，缓存可以后补） |

最后一条建议很现实：如果你预算有限只能部署一套系统，先部署关系型数据库。缓存可以后加，数据丢了无法后补。

Redis是锦上添花。TBase（或PostgreSQL）是雪中送炭。先解决"存得住"，再解决"读得快"。

---

**数据来源：**
- TBase/TDSQL PG版架构与微信支付案例：腾讯云官方博客、知乎专栏、InfoQ（2021-2022）
- Redis生产事故复盘：CSDN、博客园、企鹅号多篇真实事故记录（2022-2026）
- Redis事务ACID分析：CSDN多篇对比文章、Redis官方文档
- 分布式数据库选型对比：OceanBase官方博客、腾讯云开发者社区、CSDN（2024-2025）
- TPC性能数据：腾讯云TDSQL PG版官方发布（300万 TPMTotal）