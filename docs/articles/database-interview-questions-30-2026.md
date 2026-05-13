# 数据库面试题（30题）- 2026年版

> 适用于：初级（10题）、中级（12题）、高级（8题）
> 每题含答案和解析，覆盖MySQL/PostgreSQL核心知识点和高频考点

---

## 初级（1-10题）

### Q1: 数据库中的内连接、左连接、右连接有什么区别？

**答案：**
- **内连接（INNER JOIN）**：只返回两表匹配的行
- **左连接（LEFT JOIN）**：返回左表所有行 + 右表匹配的行（无匹配则为NULL）
- **右连接（RIGHT JOIN）**：返回右表所有行 + 左表匹配的行（无匹配则为NULL）

**代码示例：**
```sql
-- 内连接
SELECT * FROM users INNER JOIN orders ON users.id = orders.user_id;

-- 左连接
SELECT * FROM users LEFT JOIN orders ON users.id = orders.user_id;

-- 右连接
SELECT * FROM users RIGHT JOIN orders ON users.id = orders.user_id;
```

**实际应用场景：**
- 查询所有用户及其订单（包括没有订单的用户）→ 左连接
- 查询有订单的用户 → 内连接

---

### Q2: 数据库索引的作用是什么？有什么缺点？

**答案：**
- **作用**：加速查询（B+树结构，O(log n)复杂度）
- **缺点**：
  - 占用磁盘空间
  - 降低写入性能（INSERT/UPDATE/DELETE需要更新索引）

**实际应用场景：**
- 经常在WHERE、JOIN、ORDER BY中使用的列 → 创建索引
- 写多读少的表 → 谨慎创建索引

---

### Q3: 数据库事务的ACID是什么？

**答案：**
- **A（Atomicity）原子性**：事务要么全部成功，要么全部失败
- **C（Consistency）一致性**：事务前后数据保持一致状态
- **I（Isolation）隔离性**：并发事务互不干扰
- **D（Durability）持久性**：事务提交后数据永久保存

**实际应用场景：**
- 转账操作（扣除A账户，增加B账户）必须在一个事务中

---

### Q4: SQL中的GROUP BY和HAVING有什么区别？

**答案：**
- **GROUP BY**：分组聚合
- **HAVING**：过滤分组（类似WHERE，但用于分组后的过滤）
- **WHERE**：过滤行（在GROUP BY之前执行）

**代码示例：**
```sql
-- 查询订单数大于10的用户
SELECT user_id, COUNT(*) as order_count
FROM orders
GROUP BY user_id
HAVING COUNT(*) > 10;
```

**实际应用场景：**
- 分组后过滤 → HAVING
- 分组前过滤 → WHERE

---

### Q5: SQL中的索引类型有哪些？

**答案：**
- **B+树索引**：默认索引类型，适合范围查询
- **哈希索引**：适合等值查询，不支持范围查询
- **全文索引（FULLTEXT）**：适合文本搜索
- **组合索引（复合索引）**：多个列组成的索引，遵循最左前缀原则

**实际应用场景：**
- 经常一起查询的列 → 组合索引
- 文本搜索 → 全文索引

---

### Q6: SQL中的视图（VIEW）是什么？

**答案：**
- 虚拟表，基于SQL查询结果
- 不存储数据，查询时动态生成

**代码示例：**
```sql
CREATE VIEW active_users AS
SELECT * FROM users WHERE status = 'active';

-- 使用视图
SELECT * FROM active_users;
```

**实际应用场景：**
- 简化复杂查询
- 权限控制（只暴露部分列）

---

### Q7: SQL中的主键和唯一索引有什么区别？

**答案：**
| 特性 | 主键（PRIMARY KEY） | 唯一索引（UNIQUE INDEX） |
|------|---------------------|--------------------------|
| 唯一性 | 必须唯一 | 必须唯一 |
| 空值 | 不允许NULL | 允许NULL（但只能有一个NULL） |
| 数量 | 只能一个 | 可以有多个 |
| 索引类型 | 聚簇索引（InnoDB） | 非聚簇索引 |

**实际应用场景：**
- 唯一标识一行数据 → 主键
- 保证列唯一但允许NULL → 唯一索引

---

### Q8: SQL中的CHAR和VARCHAR有什么区别？

**答案：**
| 特性 | CHAR | VARCHAR |
|------|------|----------|
| 存储方式 | 固定长度 | 可变长度 |
| 存储空间 | 浪费（不足补空格） | 节省 |
| 性能 | 高（固定长度） | 低（需要额外字节记录长度） |
| 适用场景 | 长度固定的数据（如MD5） | 长度不固定的数据（如用户名） |

**实际应用场景：**
- 存储密码哈希（固定长度） → CHAR
- 存储用户名（长度不一） → VARCHAR

---

### Q9: SQL中的DROP、TRUNCATE、DELETE有什么区别？

**答案：**
| 特性 | DROP | TRUNCATE | DELETE |
|------|------|----------|--------|
| 作用 | 删除表结构和数据 | 删除数据（保留表结构） | 删除数据（保留表结构） |
| 回滚 | 不可回滚 | 不可回滚 | 可回滚 |
| 性能 | 快 | 快 | 慢（逐行删除） |
| 自增ID | - | 重置 | 不重置 |

**实际应用场景：**
- 删除整张表 → DROP
- 清空数据且不需要回滚 → TRUNCATE
- 删除部分数据或需要回滚 → DELETE

---

### Q10: SQL中的UNION和UNION ALL有什么区别？

**答案：**
- **UNION**：合并结果并去重
- **UNION ALL**：合并结果不去重（性能更高）

**代码示例：**
```sql
SELECT city FROM customers
UNION
SELECT city FROM suppliers;
-- 去重

SELECT city FROM customers
UNION ALL
SELECT city FROM suppliers;
-- 不去重，性能更高
```

**实际应用场景：**
- 需要去重 → UNION
- 确定无重复或不需要去重 → UNION ALL

---

## 中级（11-22题）

### Q11: SQL中的索引失效场景有哪些？

**答案：**
- 使用函数：`WHERE YEAR(create_time) = 2026`（索引失效）
- 类型转换：`WHERE phone = 13800138000`（phone是字符串，索引失效）
- 模糊查询：`WHERE name LIKE '%三'`（最左匹配失效）
- OR条件：`WHERE name = 'Alice' OR age = 30`（如果age没有索引，name索引也失效）
- 不等于：`WHERE age != 30`（可能不走索引）
- IS NULL / IS NOT NULL：取决于数据分布

**实际应用场景：**
- 避免在索引列上使用函数
- 避免使用`LIKE '%xxx'`

---

### Q12: SQL中的EXPLAIN有什么用？

**答案：**
- 分析SQL执行计划
- 查看是否使用索引、扫描行数、执行顺序

**关键字段：**
- **type**：ALL（全表扫描）、range（范围扫描）、ref（索引查找）、eq_ref（主键/唯一索引）、const（常量）
- **key**：实际使用的索引
- **rows**：扫描行数（越少越好）
- **Extra**：Using index（覆盖索引）、Using where（回表）、Using temporary（临时表）、Using filesort（文件排序）

**实际应用场景：**
- SQL调优时必用
- 判断索引是否有效

---

### Q13: SQL中的乐观锁和悲观锁是什么？

**答案：**
- **悲观锁**：假设会发生并发冲突，先加锁（如`SELECT ... FOR UPDATE`）
- **乐观锁**：假设不会发生冲突，提交时检查版本号（如`UPDATE ... WHERE version = old_version`）

**代码示例：**
```sql
-- 悲观锁
BEGIN;
SELECT * FROM orders WHERE id = 1 FOR UPDATE;
UPDATE orders SET status = 'paid' WHERE id = 1;
COMMIT;

-- 乐观锁
UPDATE orders SET status = 'paid', version = version + 1
WHERE id = 1 AND version = 5;
```

**实际应用场景：**
- 并发冲突多 → 悲观锁
- 并发冲突少 → 乐观锁

---

### Q14: SQL中的分库分表是什么？

**答案：**
- **分库**：将不同业务表分散到不同数据库
- **分表**：
  - 垂直分表：按列拆分（如用户表拆分为用户基础信息和用户扩展信息）
  - 水平分表：按行拆分（如按用户ID取模或按时间分表）

**分表策略：**
- 范围分片：`user_id 1-1000000 → table_1`
- 哈希分片：`user_id % 10 → table_user_id_mod_10`
- 时间分片：`orders_202601`、`orders_202602`

**实际应用场景：**
- 单表数据量超过1000万 → 考虑分表
- 读写压力过大 → 分库 + 读写分离

---

### Q15: SQL中的主从复制是什么？

**答案：**
- 主库（Master）负责写，从库（Slave）负责读
- 主库将binlog同步到从库，从库重放binlog

**复制模式：**
- 异步复制（默认）：主库写完立即返回，不等待从库确认
- 半同步复制：主库等待至少一个从库确认
- 全同步复制：主库等待所有从库确认

**实际应用场景：**
- 读写分离（写主库，读从库）
- 数据备份

---

### Q16: SQL中的MVCC是什么？

**答案：**
- 多版本并发控制（Multi-Version Concurrency Control）
- 读不加锁，读写不冲突
- 实现：每行数据有隐藏的`trx_id`（事务ID）和`roll_pointer`（回滚指针）

**实际应用场景：**
- 提高并发性能
- 实现可重复读（Repeatable Read）隔离级别

---

### Q17: SQL中的隔离级别有哪些？

**答案：**
| 隔离级别 | 脏读 | 不可重复读 | 幻读 |
|----------|------|------------|------|
| READ UNCOMMITTED | ✗ | ✗ | ✗ |
| READ COMMITTED | ✓ | ✗ | ✗ |
| REPEATABLE READ（MySQL默认） | ✓ | ✓ | ✗ |
| SERIALIZABLE | ✓ | ✓ | ✓ |

**实际应用场景：**
- 大多数场景 → REPEATABLE READ
- 需要最高一致性 → SERIALIZABLE（但性能低）

---

### Q18: SQL中的慢查询如何优化？

**答案：**
1. 使用`EXPLAIN`分析SQL
2. 添加合适的索引
3. 避免`SELECT *`，只查需要的列
4. 避免子查询，改用JOIN
5. 分页优化（大偏移量时使用`WHERE id > ? LIMIT ?`）
6. 使用覆盖索引（不需要回表）

**实际应用场景：**
- 慢查询日志分析
- 定期优化索引

---

### Q19: SQL中的存储引擎InnoDB和MyISAM有什么区别？

**答案：**
| 特性 | InnoDB | MyISAM |
|------|--------|---------|
| 事务 | 支持 | 不支持 |
| 外键 | 支持 | 不支持 |
| 锁粒度 | 行锁 | 表锁 |
| 崩溃恢复 | 支持 | 不支持 |
| 全文索引 | 支持（MySQL 5.6+） | 支持 |

**实际应用场景：**
- 大多数场景 → InnoDB
- 只读、不需要事务 → MyISAM

---

### Q20: SQL中的binlog、redolog、undolog有什么区别？

**答案：**
- **binlog（归档日志）**：记录所有修改操作，用于主从复制和数据恢复
- **redolog（重做日志）**：保证事务持久性，崩溃恢复
- **undolog（回滚日志）**：保证事务原子性，支持回滚和MVCC

**实际应用场景：**
- 数据恢复 → binlog
- 事务持久性 → redolog
- 回滚和MVCC → undolog

---

### Q21: SQL中的数据库连接池有什么用？

**答案：**
- 复用数据库连接，避免频繁创建/销毁连接
- 控制连接数，防止数据库被冲垮

**常用连接池：**
- HikariCP（性能最高）
- Druid（阿里，监控功能强）
- C3P0（老牌，但性能一般）

**实际应用场景：**
- 高并发系统必须使用连接池
- 合理配置连接池大小（通常设置为CPU核心数 * 2）

---

### Q22: SQL中的分布式事务如何解决？

**答案：**
- **2PC（两阶段提交）**：协调者先询问所有参与者，再提交（同步阻塞、单点故障）
- **3PC（三阶段提交）**：在2PC基础上增加canCommit阶段（减少阻塞）
- **TCC（Try-Confirm-Cancel）**：业务层面的分布式事务
- **消息队列**：最终一致性（如RocketMQ事务消息）

**实际应用场景：**
- 跨库操作 → 2PC / 3PC
- 业务操作 → TCC
- 异步场景 → 消息队列

---

## 高级（23-30题）

### Q23: SQL中的分库分表后如何查询？

**答案：**
- **中间件**：
  - ShardingSphere（开源，支持分库分表、读写分离）
  - MyCAT（基于Cobar，老牌）
  - ProxySQL（MySQL代理）
- **问题**：
  - 跨分片查询性能低
  - 分页、排序、聚合函数需要合并结果
  - 分布式ID生成（雪花算法）

**实际应用场景：**
- 大数据量 → 使用ShardingSphere
- 尽量避免跨分片查询

---

### Q24: SQL中的索引覆盖是什么？

**答案：**
- 查询的列都在索引中，不需要回表
- `EXPLAIN`的`Extra`字段显示`Using index`

**代码示例：**
```sql
-- 有索引：idx_age_name (age, name)
-- 覆盖索引（不需要回表）
SELECT age, name FROM users WHERE age = 30;

-- 非覆盖索引（需要回表）
SELECT age, name, email FROM users WHERE age = 30;
-- email不在索引中，需要回表查询
```

**实际应用场景：**
- 避免`SELECT *`
- 设计组合索引时考虑覆盖查询

---

### Q25: SQL中的死锁如何排查和解决？

**答案：**
- **排查**：`SHOW ENGINE INNODB STATUS;`查看最近死锁信息
- **解决**：
  - 按相同顺序获取锁
  - 缩小事务范围（尽快提交/回滚）
  - 设置锁等待超时：`innodb_lock_wait_timeout`
  - 使用`SELECT ... FOR UPDATE NOWAIT`（不等待，立即报错）

**实际应用场景：**
- 并发更新多行数据时注意顺序
- 批量更新时分批提交

---

### Q26: SQL中的读写分离如何实现？

**答案：**
- **中间件**：
  - ShardingSphere：支持读写分离、分库分表
  - MyCAT：老牌中间件
  - ProxySQL：MySQL代理
- **应用层实现**：
  - Spring Boot + MyBatis：配置多个数据源，写走主库，读走从库

**实际应用场景：**
- 读多写少场景 → 读写分离
- 主从延迟问题：写完主库后立即读 → 强制读主库

---

### Q27: SQL中的分布式ID生成方案有哪些？

**答案：**
- **UUID**：简单，但无序、字符串长、索引性能差
- **雪花算法（Snowflake）**：趋势递增、性能好、适合分布式
- **数据库自增**：简单，但单点故障、性能瓶颈
- **号段模式**：批量获取ID区间（如每次从数据库获取1000个ID）

**实际应用场景：**
- 分布式系统 → 雪花算法
- 高并发 → 号段模式

---

### Q28: SQL中的海量数据归档怎么做？

**答案：**
- **分区表**：按时间分区，旧分区可以单独归档
- **冷热数据分离**：热数据存MySQL，冷数据存HDFS/对象存储
- **定期归档**：定时任务将旧数据迁移到归档表

**实际应用场景：**
- 订单表数据量过大 → 按时间分区 + 归档
- 日志表 → 定期清理或归档

---

### Q29: SQL中的数据库中间件有哪些？

**答案：**
- **ShardingSphere**：分库分表、读写分离、分布式事务
- **MyCAT**：基于Cobar，老牌
- **ProxySQL**：MySQL代理，支持读写分离、负载均衡
- **Vitess**：YouTube开源，支持水平扩展

**实际应用场景：**
- 需要分库分表 → ShardingSphere
- 只需要读写分离 → ProxySQL

---

### Q30: SQL中的NewSQL数据库有哪些？

**答案：**
- **TiDB**：兼容MySQL协议，分布式、强一致性、高可用
- **CockroachDB**：兼容PostgreSQL，分布式、强一致性
- **OceanBase**：阿里开源，分布式、高可用

**实际应用场景：**
- 需要水平扩展但又不想分库分表 → TiDB
- 需要强一致性 → CockroachDB

---

## 总结

| 级别 | 题号 | 核心知识点 |
|------|------|-----------|
| 初级 | 1-10 | 基础SQL、索引、事务、连接 |
| 中级 | 11-22 | 索引优化、锁、分库分表、主从复制 |
| 高级 | 23-30 | 分布式事务、读写分离、NewSQL |

**下一步：**
- 结合项目经验理解每个知识点
- 重点掌握索引优化、事务隔离级别、分库分表

---

**文件版本：** 2026-05-13  
**作者：** 智能行程规划器项目  
**许可：** MIT License
