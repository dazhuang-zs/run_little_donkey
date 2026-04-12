# FastGPT 架构深度分析

> 项目地址：https://github.com/labring/FastGPT
> 本文档目标：深度理解架构设计，面试能讲、设计能用的参考素材

---

## 一、项目整体架构

### 1.1 Monorepo 结构

FastGPT 采用 **pnpm workspace** 管理 monorepo，项目分为四大类：

```
FastGPT/
├── packages/          ← 核心共享包（被其他所有模块引用）
│   ├── global/        ← 全局类型定义、枚举、常量（纯 TS，无业务逻辑）
│   ├── service/       ← 核心业务逻辑层（Node.js/TypeScript）
│   └── web/           ← 国际化（i18n）相关
│
├── projects/          ← 具体应用层
│   ├── app/           ← Next.js 前端应用（pages 路由）
│   ├── agent-sandbox/ ← Agent 安全沙箱
│   ├── code-sandbox/  ← 代码执行沙箱
│   ├── marketplace/   ← 插件/模板市场
│   ├── mcp_server/   ← MCP 协议服务端
│   └── volume-manager/# 文件卷管理
│
├── sdk/              ← 对外 SDK（供第三方调用）
├── scripts/          ← 工具脚本（图标生成等）
└── deploy/           ← 部署配置（Docker/K8s/Helm）
```

**packages/global 和 packages/service 的关系**：

```
packages/global/          packages/service/
─────────────────         ────────────────────────
纯类型 + 枚举 + 常量         业务逻辑实现
无运行时依赖                 依赖 global 的类型
所有模块共享                 特定业务域

例子:
global/core/workflow/constants.ts  →  定义 NodeTypeEnum
service/core/workflow/dispatch/   →  实现工作流调度逻辑
```

**设计思想**：这是大型 TypeScript 项目的经典分层模式 —— **类型层与实现层分离**。好处是：
- 前端和后端共享同一套类型定义，保证接口一致
- 改类型只改 global，改逻辑只改 service
- VSCode 的 Go to Definition 可以直接跳转

### 1.2 技术栈总览

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 前端 | Next.js 16 + Chakra UI + React 18 | App Router, i18n 国际化 |
| 后端 | Node.js + TypeScript + Express-like | 跑在 Next.js API routes |
| 数据库 | MongoDB | 主要数据存储 |
| 向量库 | PostgreSQL + pgvector | RAG 向量检索 |
| 缓存 | Redis | 会话、限流、指标缓存 |
| 文件存储 | S3 兼容（MinIO/AWS） | 图片、文档、音视频 |
| 链路追踪 | OpenTelemetry | 分布式追踪 |
| 部署 | Docker + K8s + Helm | 云原生支持 |

---

## 二、前端架构（projects/app）

### 2.1 目录结构

```
projects/app/src/
├── pages/              ← Next.js Pages Router（旧版）
│   ├── chat/           ← 对话页面
│   ├── app/            ← 应用管理
│   ├── dataset/         ← 知识库管理
│   ├── account/        ← 账户设置
│   └── api/            ← API 路由（SSR 入口）
├── components/         ← 通用组件
├── web/               ← Web 通用组件
├── service/           ← API 调用层（axios 封装）
└── global/            ← 全局配置、主题
```

**FastGPT 前端是 Pages Router 而不是 App Router**，这点需要注意。

### 2.2 前端与服务端的数据流

```
用户操作
  ↓
pages/chat/  ← React 页面组件
  ↓
service/    ← API 调用封装（fetch 包装）
  ↓
pages/api/  ← Next.js API Route（服务端入口）
  ↓
packages/service/  ← 核心业务逻辑
  ↓
MongoDB / Redis / S3 / Vector DB
```

FastGPT 的 API 路由层很薄，主要是 **权限校验 + 参数验证 + 调用 service**。真正逻辑在 packages/service 里。

**这种设计的好处**：同一个 service 包可以被多个入口调用：
- 前端 Next.js API Routes
- CLI 工具
- Webhook
- 其他微服务

---

## 三、核心业务层（packages/service）

### 3.1 服务层目录划分

```
service/
├── common/            ← 通用基础设施
│   ├── mongo/         ← MongoDB 连接与 Schema 封装
│   ├── redis/         ← Redis 操作封装
│   ├── s3/            ← S3 文件操作封装
│   ├── vectorDB/      ← 向量数据库统一抽象层
│   ├── cache/         ← Redis 缓存工具
│   ├── logger/        ← 日志（OpenTelemetry 集成）
│   ├── tracing/       ← 链路追踪工具
│   ├── metrics/       ← 指标采集
│   ├── security/      ← 安全工具（文件 URL 校验等）
│   └── response/      ← 统一响应格式
│
├── core/              ← 核心业务域
│   ├── workflow/      ← 工作流引擎 ⭐
│   ├── chat/          ← 对话管理
│   ├── dataset/       ← 知识库（RAG 核心）⭐
│   ├── ai/            ← AI 能力抽象层（LLM/Embedding）⭐
│   ├── app/           ← 应用管理
│   ├── agentSkills/  ← Agent 技能沙箱
│   └── plugin/        ← 插件系统
│
└── support/           ← 支撑系统
    ├── user/          ← 用户与认证
    ├── permission/    ← 权限控制
    ├── openapi/       ← 开放 API
    └── wallet/        ← 账户与计费
```

**架构设计思想：Domain-Driven Design（DDD）简化版**

- `core/*` = 核心业务域，彼此边界清晰
- `common/*` = 跨域通用能力
- `support/*` = 支撑服务（用户、权限、计费）

---

## 四、工作流引擎（Workflow Engine）⭐

这是 FastGPT 最核心、最复杂的模块，代码集中在 `packages/service/core/workflow/dispatch/`。

### 4.1 工作流模型

FastGPT 的工作流是一个 **有向无环图（DAG）**，但支持通过特殊节点形成**循环**：

```
节点 (Node)                    边 (Edge)
─────────────────────────      ───────────────────────────
+ 每个节点是一个「功能模块」    + 有向边：source → target
+ 有输入和输出定义             + 每条边有 sourceHandle/targetHandle
+ 输入可以从变量引用            + 边的 status: active | waiting | skipped
+ 支持条件分支（if/else）       + 支持循环（通过回边 back edge）
```

**内置节点类型**（定义在 `packages/global/core/workflow/template/system/`）：

| 节点类型 | 功能 | 文件 |
|---------|------|------|
| workflowStart | 入口节点，接收用户输入 | workflowStart.tsx |
| aiChat | AI 对话节点（LLM 调用）| aiChat.ts |
| datasetSearch | 知识库检索（RAG） | datasetSearch.ts |
| classifyQuestion | 问题分类（LLM 决策路由）| classifyQuestion.ts |
| contextExtract | 从上下文中提取信息 | contextExtract.ts |
| httpRequest468 | HTTP 请求 | http468.ts |
| ifElse | 条件分支 | ifElse.ts |
| loop | 循环节点 | loop.ts |
| toolCall | 工具调用 | toolCall.ts |
| runPlugin | 运行插件 | runPlugin.ts |
| readFiles | 读取文件 | readFiles.ts |
| runApp | 运行子应用 | runApp.ts |
| variableUpdate | 修改变量 | variableUpdate.ts |
| queryExtension | 查询扩展 | queryExtension.ts |

### 4.2 工作流调度核心：WorkflowQueue 类

**文件**：`packages/service/core/workflow/dispatch/index.ts`（1677 行）

这是整个引擎的核心。FastGPT 实现了自己的**异步任务队列调度器**，而不是用现成的 BullMQ。

**核心设计哲学**（代码注释原文）：

```
工作流队列控制
特点：
  1. 可以控制一个 team 下，并发 run 的节点数量
  2. 每个节点，同时只会执行一个。一个节点不可能同时运行多次
  3. 都会返回 resolve，不存在 reject 状态

方案：
  - 采用回调的方式，避免深度递归
  - 使用 activeRunQueue 记录待运行检查的节点
  - 每次添加新节点，以及节点运行结束后，均会执行一次 processActiveNode
  - processActiveNode 如果没触发跳出条件，则必定会取一个 activeRunQueue 继续检查处理
```

**关键数据结构**：

```typescript
class WorkflowQueue {
  // 节点 Map，用于快速查找节点
  runtimeNodesMap: Map<string, RuntimeNodeItemType>

  // 边索引（按 source 和 target 分别建索引）
  // 一次性构建，后续 O(1) 查找
  edgeIndex: {
    bySource: Map<string, RuntimeEdgeItemType[]>
    byTarget: Map<string, RuntimeEdgeItemType[]>
  }

  // 预构建的节点边分组 Map
  // 包含 DFS 边分类 + Tarjan SCC 计算结果
  nodeEdgeGroupsMap: NodeEdgeGroupsMap

  // 待运行的节点队列
  activeRunQueue: Set<string>

  // 跳过的节点队列（缓存，避免重复计算）
  skipNodeQueue: Map<string, { node, skippedNodeIdList }>

  // 并发控制
  maxConcurrency: number = 10
}
```

### 4.3 循环检测：Tarjan SCC 算法

FastGPT 在构建节点边分组时，会**检测工作流中是否存在循环**。这是通过 **Tarjan 算法求强连通分量（SCC）** 实现的。

**为什么需要检测循环？**

工作流支持节点 A → B → A 这样的循环结构（例如循环读取知识库直到找到满意答案）。但循环需要特殊处理：
- 循环内的边称为 **回边（back edge）**
- 非循环的边称为 **树边（tree edge）**

**Tarjan 算法核心思路**：

```typescript
// findSCCs - 找强连通分量
function tarjan(nodeId: string) {
  discoveryTime[nodeId] = time
  lowLink[nodeId] = time
  time++
  stack.push(nodeId)

  for (const edge of outEdges) {
    if (!visited[edge.target]) {
      tarjin(edge.target)
      lowLink[nodeId] = min(lowLink[nodeId], lowLink[edge.target])
    } else if (inStack(edge.target)) {
      // 回边
      lowLink[nodeId] = min(lowLink[nodeId], discoveryTime[edge.target])
    }
  }

  if (lowLink[nodeId] === discoveryTime[nodeId]) {
    // 找到一个 SCC
    // pop 直到回到当前节点
  }
}
```

**分组策略**：

```typescript
// 预构建节点边分组 Map
// 核心逻辑：
for (targetNode of runtimeNodes) {
  if (targetInCycle) {
    // 循环中节点 → 按 branchHandle 分组（每条边单独处理）
    edgesGroup = groupByBranchHandle(nonBackEdges)
  } else {
    // 非循环节点 → 所有非回边放同一组
    edgesGroup = [nonBackEdges]
  }
}
```

**面试可以说的点**：
- "Tarjan 算法是 O(V+E) 的图遍历，比朴素的多次 DFS 快"
- "强连通分量大小 > 1 才算循环，区分了自环和真正循环"
- "分组策略的核心洞察：循环内节点需要逐条边处理，非循环节点可以批量处理"

### 4.4 边分类：DFS 识别回边

```typescript
// classifyEdgesByDFS - 标记每条边的类型
function dfs(nodeId: string) {
  for (const edge of outEdges) {
    if (!visited[edge.target]) {
      edgeTypes.set(edgeKey, 'tree')   // 树边
      dfs(edge.target)
    } else if (inStack(edge.target)) {
      edgeTypes.set(edgeKey, 'back')    // 回边 → 循环
    } else if (discoveryTime[source] < discoveryTime[target]) {
      edgeTypes.set(edgeKey, 'forward') // 前向边
    } else {
      edgeTypes.set(edgeKey, 'cross')   // 跨边
    }
  }
}
```

### 4.5 节点运行状态机

每个节点有三种运行状态：

```
wait   → 等待触发（前置节点还没运行完）
  ↓
run    → 正在运行（至少一条输入边 active，无 waiting 边）
  ↓
skip   → 跳过执行（所有输入边都是 skipped）
```

**状态判断核心逻辑**（从 `getNodeRunStatus` 提炼）：

```typescript
if (没有输入边) → return 'run'  // 入口节点，直接运行

// 任意一组边满足条件即可运行
if (任意组: 至少一条 active 边 AND 没有 waiting 边) → return 'run'

// 所有组的边都是 skipped 才跳过
if (所有组的边都是 skipped) → return 'skip'

return 'wait'  // 否则继续等待
```

### 4.6 SSE 流式响应机制

FastGPT 的工作流支持 **Server-Sent Events（SSE）** 实时推送节点输出：

```typescript
// 设置 SSE 响应头
res.setHeader('Content-Type', 'text/event-stream;charset=utf-8')
res.setHeader('X-Accel-Buffering', 'no')
res.setHeader('Cache-Control', 'no-cache, no-transform')

// 每 10 秒发送心跳，防止连接断开
setInterval(() => {
  data?.workflowStreamResponse({
    event: SseResponseEventEnum.answer,
    data: { text: '' }
  })
}, 10000)

// 节点运行结果实时推送
await node.dispatch(params, {
  onStreaming: (text) => streamResponse({ event: 'answer', data: text }),
  onToolCall: (call) => streamResponse({ event: 'tool_call', data: call }),
})
```

### 4.7 工作流中断机制

通过 Redis 实现工作流随时终止：

```typescript
// 开始时删除停止标记
delAgentRuntimeStopSign({ appId, chatId })

// 定时轮询检查是否需要停止（v2 模式）
setInterval(async () => {
  if (await shouldWorkflowStop({ appId, chatId })) {
    stopping = true  // 触发停止
  }
}, 100)

// 节点内部也会检查 checkIsStopping()
if (checkIsStopping()) {
  throw new Error('WORKFLOW_STOP')
}
```

---

## 五、知识库与 RAG 系统 ⭐

### 5.1 整体 RAG 流程

```
用户 Query
  ↓
1. Query 扩展（可选）
  ↓
2. Embedding 模型 → 向量
  ↓
3. 向量检索（向量数据库）
  ↓
4. 重排序（ReRank 模型，可选）
  ↓
5. 过滤（collection/tag/时间范围）
  ↓
6. 拼接为上下文
  ↓
7. LLM 生成答案
```

### 5.2 检索模式

FastGPT 支持三种检索模式（`DatasetSearchModeEnum`）：

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| `embedding` | 纯向量语义检索 | 语义相关但关键词不明确的查询 |
| `fullTextRecall` | 纯全文检索（jieba 分词） | 关键词明确、需要精确匹配 |
| `mixedRecall` | 向量 + 全文混合 | 通用场景，平衡精确与语义 |

**混合检索实现思路**：
- 分别用向量和全文检索
- 按相似度 + 相关性综合排序
- 可配置权重比例

### 5.3 向量数据库抽象层

FastGPT 支持多种向量数据库，通过统一抽象层切换：

```typescript
// packages/service/common/vectorDB/controller.ts
const getVectorObj = () => {
  if (SEEKDB_ADDRESS)   return new SeekVectorCtrl()
  if (OCEANBASE_ADDRESS) return new ObVectorCtrl()
  if (PG_ADDRESS)       return new PgVectorCtrl()
  if (MILVUS_ADDRESS)    return new MilvusCtrl()
  return new PgVectorCtrl()  // 默认 PostgreSQL
}
```

**PostgreSQL + pgvector 实现**（最常用的方案）：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS modeldata (
  id BIGSERIAL PRIMARY KEY,
  vector VECTOR(1536) NOT NULL,
  team_id VARCHAR(50) NOT NULL,
  dataset_id VARCHAR(50) NOT NULL,
  collection_id VARCHAR(50) NOT NULL,
  createtime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HNSW 索引（高维向量近似最近邻检索）
CREATE INDEX ON modeldata USING hnsw (vector vector_ip_ops)
  WITH (m = 32, ef_construction = 128);
```

**HNSW 索引参数说明**（面试亮点）：
- `m=32`：每个节点最多连接 32 个近邻（空间换时间，召回率高）
- `ef_construction=128`：构建时动态列表大小（越大越精确但越慢）

### 5.4 ReRank 重排序

向量检索后，通过 ReRank 模型对结果重新排序：

```typescript
const reRankResults = await reRankRecall({
  query: reRankQuery,
  documents: searchResults,
  model: rerankModel,
  weight: rerankWeight  // 配置 ReRank 在最终得分中的权重
})

// 最终得分 = 向量相似度 * (1 - rerankWeight) + ReRank得分 * rerankWeight
```

### 5.5 数据导入与切分

```
文档上传
  ↓
文件解析（PDF/Word/TXT/Markdown/HTML）
  ↓
智能切分（按段落/句子/ token 数切分）
  ↓
Embedding（每段生成向量）
  ↓
存储到向量库 + MongoDB（原始文本）
```

### 5.6 多租户隔离

向量数据通过 `team_id + dataset_id + collection_id` 三级隔离：

```typescript
WHERE team_id = ? AND dataset_id = ? AND collection_id = ?
```

Redis 缓存团队向量计数，避免频繁查库：

```typescript
teamVectorCache: {
  get: async (teamId) => getRedisCache(`team_vector_count:${teamId}`)
  incr: (teamId, count) => incrValueToCache(...)
  delete: throttle((teamId) => delRedisCache(...), 30000)
}
```

---

## 六、AI 能力抽象层 ⭐

### 6.1 统一 LLM 调用接口

FastGPT 封装了 `createLLMResponse`，屏蔽流式/非流式、Tool Call 模式的差异：

```typescript
export const createLLMResponse = async (props: {
  body: LLMRequestBodyType
  onStreaming?: (text: string) => void      // 流式输出回调
  onReasoning?: (text: string) => void      // 思考过程回调
  onToolCall?: (call) => void               // 工具调用回调
  isAborted?: () => boolean                  // 查询是否中止
}) => {
  // 统一处理：
  // 1. stream vs non-stream → 统一返回格式
  // 2. function call → 适配 OpenAI tool_calls 格式
  // 3. thinking model → 提取 reasoning_content
  // 4. token 计算与记录
}
```

**面试可以说的点**：
- "Stream 和非 Stream 的核心区别在于 SSE 推送，底层都走同一个 LLM API"
- "thinking model（o1/o3）返回的 reasoning_content 需要单独提取"
- "Tool Call 无论哪种模式都统一存为 tool_calls 格式"

### 6.2 Token 计算

```typescript
// 使用 tiktoken（OpenAI 的 BPE 分词器）
countGptMessagesTokens(messages, model)
countPromptTokens(text, model)

// Token 上限控制
computedMaxToken({
  model,
  maxTokens: userConfig.maxTokens,
  contextMaxToken: model.contextWindow
})
```

### 6.3 多模型支持

```typescript
// 模型配置在 MongoDB 中，可动态切换
getLLMModel(modelId: string): LLMModelItemType
getEmbeddingModel(teamId: string): EmbeddingModelItemType
getDefaultRerankModel(teamId: string): RerankModelItemType
```

### 6.4 Prompt 压缩

当上下文超出限制时，压缩历史消息：

```typescript
// filterGPTMessageByMaxContext
// 按相关性降序保留消息，超出则从中间裁剪（保留最新和最旧）
// 因为开头和结尾的 token 利用率最高
```

---

## 七、权限与多租户

### 7.1 多租户模型

```
Team（团队）
  └── TeamMember（团队成员）
        └── Permission（权限）
```

每个 App、Dataset、Plugin 都有 `teamId` 字段，通过 MongoDB 查询过滤实现数据隔离。

### 7.2 权限控制

```typescript
// 权限校验在 API 层统一做
checkTeamPermission({
  teamId,
  tmbId,    // team member id
  required: ['read' | 'write' | 'manage']
})
```

### 7.3 API Key 鉴权

```typescript
// OpenAPI 鉴权
const apiKey = req.headers['authorization'].replace('Bearer ', '')
const keyRecord = await MongoApiKey.findOne({ apiKey })
// keyRecord 包含 teamId 和权限范围
```

---

## 八、沙箱与安全执行

### 8.1 Agent 技能沙箱（agent-sandbox）

用户编写的 JavaScript 代码在隔离环境中执行：

```
packages/service/core/agentSkills/sandboxController.ts
  ↓
调用 projects/agent-sandbox 的沙箱服务
  ↓
沙箱环境：禁止网络请求、禁止文件系统访问
  ↓
返回执行结果或超时错误
```

### 8.2 MCP 协议支持

MCP（Model Context Protocol）让 FastGPT 可以调用外部工具：

```typescript
// packages/service/support/mcp/schema.ts
// 支持 MCP Tools 的注册与调用
// 工具定义：name, description, inputSchema
```

---

## 九、插件系统

```
用户上传插件
  ↓
packages/service/core/plugin/schema   ← 存储插件定义
  ↓
插件节点 dispatch                      ← 运行插件逻辑
  ↓
插件模板市场（projects/marketplace）   ← 分发和分享
```

**插件本质**：一段可配置的 Prompt + 输入输出定义，运行时像普通节点一样被调度。

---

## 十、部署架构

### 10.1 Docker Compose 最小部署

```yaml
services:
  fastgpt:
    image: ghcr.io/labring/fastgpt:latest
    ports:
      - "3000:3000"
    environment:
      - OPENAI_API_KEY=xxx
      - DB_MAX_KEY=xxx
      - REDIS_URL=redis://fastgpt-redis:6379
    depends_on:
      - fastgpt-mongo
      - fastgpt-redis
      - fastgpt-pgvector
```

### 10.2 环境变量驱动配置

```typescript
// 通过环境变量初始化各个组件
const {
  OPENAI_API_KEY,
  DB_MAX_KEY,       // MongoDB 连接 Key
  REDIS_URL,
  PG_HOST,
  S3_ENDPOINT,
  MILVUS_ADDRESS,   // 可选，向量库
} = process.env
```

### 10.3 Helm 支持

`deploy/helm/` 提供了 Kubernetes 生产部署配置，包括：
- Horizontal Pod Autoscaler（HPA）
- 健康检查（liveness/readiness probe）
- 持久化存储（PVC）

---

## 十一、设计亮点与面试可讲的点

### 11.1 图算法应用

| 场景 | 算法 | 收益 |
|------|------|------|
| 工作流循环检测 | Tarjan SCC | O(V+E) 一次遍历，区分循环/非循环边 |
| 边分类 | DFS 边分类 | 识别 tree/back/forward/cross 边 |
| 分组策略 | 按 SCC 分组 | 循环内精细化，非循环内批处理 |

### 11.2 性能优化技巧

1. **边索引用 Map 代替数组遍历**：O(1) 查找前置/后续节点
2. **预构建节点边分组 Map**：一次计算，多次复用（不用每次节点执行都重新计算）
3. **Redis 缓存团队向量计数**：减少 MongoDB 查询
4. **HNSW 索引参数调优**：`m=32, ef_construction=128` 平衡召回与性能
5. **Throttle 删除缓存**：30s 防抖，避免缓存击穿

### 11.3 可扩展性设计

| 维度 | 扩展方式 |
|------|---------|
| 向量库 | 抽象 `VectorControllerType`，切换不同实现 |
| LLM 模型 | 模型配置存 DB，动态加载 |
| 节点类型 | 注册到 `FlowNodeTypeEnum`，统一调度 |
| 插件 | Schema 定义 + 沙箱执行 |
| MCP 工具 | MCP Server 动态注册 |

### 11.4 工程化亮点

1. **Monorepo 规范**：packages/global + service + projects + sdk 边界清晰
2. **类型层与实现层分离**：改动范围可控
3. **OpenTelemetry 全链路追踪**：每个工作流节点都有 span
4. **SSE 流式输出**：10s 心跳保活，实时展示节点输出
5. **工作流可中断**：Redis + 定时轮询，优雅停止

---

## 十二、值得借鉴的设计模式

### 12.1 工厂模式：向量化控制器

```typescript
// 根据配置动态创建不同向量库实例
const getVectorObj = () => {
  if (MILVUS_ADDRESS) return new MilvusCtrl()
  return new PgVectorCtrl()  // 默认
}
```

### 12.2 策略模式：检索模式

```typescript
const searchMode = DatasetSearchModeMap[mode]
// embedding / fullTextRecall / mixedRecall
// 每种模式有自己的检索策略和评分计算
```

### 12.3 模板方法：节点调度

```typescript
// 所有节点都实现相同的 dispatch 接口
async dispatch(props: ModuleDispatchProps): Promise<DispatchNodeResultType>

// 工作流引擎统一调用，无需关心具体节点类型
const result = await node.dispatch(params)
```

### 12.4 发布-订阅：SSE 流式响应

```typescript
// 注册回调，工作流节点运行时实时推送
const emitter = new EventEmitter()
emitter.on('answer', (text) => res.write(`data: ${text}\n\n`))
emitter.on('tool_call', (call) => res.write(`data: ${call}\n\n`))
```

---

## 十三、如果你要基于 FastGPT 设计自己的 RAG 系统

### 13.1 核心模块划分建议

```
my-rag-system/
├── core/              ← 工作流引擎（参考 FastGPT WorkflowQueue）
├── ai/                ← LLM 抽象层（参考 createLLMResponse）
├── retrieval/          ← 检索系统（参考 vectorDB/controller.ts）
│   ├── embedding/      ← Embedding 服务
│   ├── rerank/        ← 重排序
│   └── storage/       ← 向量存储
├── models/            ← 数据模型（参考 MongoDB Schema）
└── api/              ← 对外接口
```

### 13.2 关键设计决策

| 决策点 | FastGPT 方案 | 备选方案 |
|--------|------------|---------|
| 工作流引擎 | 自研队列 + 节点图 | Temporal / Airflow |
| 向量库 | pgvector（默认） | Milvus / Qdrant / Chroma |
| 工作流持久化 | MongoDB JSON | PostgreSQL JSONB |
| LLM 调用 | OpenAI 兼容格式 | vLLM / Ollama |
| 前端 | Next.js | Nuxt / Vue |
| 部署 | K8s | Railway / Render |

---

*文档生成时间：2026-04-12*
*基于 FastGPT v4.0 源码分析*
