# RAGFlow 架构深度分析

> 项目地址：https://github.com/infiniflow/ragflow
> 本文档目标：深度理解架构设计，面试能讲、设计能用的参考素材
> 技术栈：Go + Python + React + Infinity（向量库）+ Elasticsearch + Redis

---

## 一、项目整体架构

### 1.1 双语言混合架构

RAGFlow 最有特色的设计是 **Go + Python 双服务混合部署**，不是简单的微服务拆分，而是按计算特性分配：

```
┌─────────────────────────────────────────────────────────────────┐
│                        React 前端 (web/)                         │
│                     TypeScript + Vite + Tailwind                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP REST API
         ┌─────────────────┴──────────────────┐
         │                                    │
   ┌─────▼───────┐                    ┌──────▼───────┐
   │  Go HTTP    │                    │ Python API    │
   │  服务       │◄── 共享存储 ──────►│ 服务          │
   │  (cmd/)     │   Redis + MySQL    │ (api/ + rag/) │
   │  轻量 API   │   MongoDB + S3     │ 重计算任务    │
   └─────────────┘                    └───────────────┘
```

**为什么这样设计？**

| 维度 | Go 服务 | Python 服务 |
|------|---------|------------|
| 职责 | 路由、认证、会话管理、租户管理 | 文档解析、Embedding、RAG 推理 |
| 特点 | 高并发、低内存、编译型 | 生态丰富、ML 支持、动态灵活 |
| 框架 | Gin + GORM | FastAPI-like 自研 |

两者通过 **共享数据层**（MongoDB + Redis + MySQL + S3）通信，不直接调用。Go 服务不依赖 Python 服务，任何一个崩了另一个照常工作。

### 1.2 项目目录结构

```
ragflow/
├── cmd/server_main.go     ← Go 服务入口（编译为二进制）
├── internal/              ← Go 后端核心
│   ├── handler/           ← HTTP Handler（Gin）
│   ├── service/           ← 业务逻辑层
│   ├── dao/               ← 数据访问层（GORM）
│   ├── entity/            ← 数据实体（Go struct）
│   ├── engine/            ← C++ 引擎绑定（文档解析加速）
│   ├── router/            ← 路由注册
│   ├── cache/             ← Redis 缓存封装
│   ├── storage/           ← S3/MinIO 存储封装
│   └── server/            ← 服务器初始化
│
├── api/                   ← Python API 服务（独立进程）
│   ├── ragflow_server.py  ← Python 服务入口
│   ├── apps/              ← API 路由（Python）
│   │   ├── restful_apis/  │   ← 对话、文档、检索 API
│   │   └── services/      │   ← 业务逻辑
│   └── db/                ← 数据库连接
│
├── rag/                   ← Python RAG 核心（推理引擎）
│   ├── flow/              │   ← Pipeline（文档处理流程）
│   │   ├── pipeline.py    │   ← Pipeline 图执行引擎
│   │   ├── chunker/       │   ← 文档分块策略
│   │   └── extractor/     │   ← 关键信息提取
│   ├── svr/               │   ← 任务执行器
│   ├── graphrag/          │   ← GraphRAG（知识图谱 RAG）
│   ├── llm/               │   ← LLM 调用封装
│   └── prompts/           │   ← Prompt 模板
│
├── agent/                 ← Python Agent 核心
│   ├── canvas.py          │   ← 图执行引擎（Graph/Canvas/Pipeline）
│   └── component/         │   ← Agent 组件库
│
├── deepdoc/               ← Python 文档解析（DeepDoc）
│   ├── parser/            │   ← 多格式解析器
│   └── vision/            │   ← OCR + 布局识别（YOLOv10）
│
├── web/                   ← React 前端
├── go.mod                 ← Go 依赖
└── pyproject.toml         ← Python 依赖（uv 管理）
```

### 1.3 技术栈总览

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| Go 后端 | Go 1.25 + Gin + GORM | 轻量 HTTP 路由 |
| Python API | Python 3.12 + uv | 推理计算 |
| Python RAG | asyncio + NetworkX | 图执行引擎 |
| 前端 | React + Vite + Tailwind + TypeScript | SPA |
| 主数据库 | MySQL 8（GORM） | 关系数据 |
| 文档数据库 | MongoDB | 文档、对话历史 |
| 向量库 | Infinity（Infiniflow 自研） | 向量存储与检索 |
| 搜索引擎 | Elasticsearch | 全文检索（可选） |
| 缓存 | Redis | 会话、任务队列、分布式锁 |
| 文件存储 | S3/MinIO | 原始文档、图片 |
| C++ 加速 | SWIG 绑定 | 文档解析关键路径加速 |

---

## 二、Go 后端服务

### 2.1 服务入口

```go
// cmd/server_main.go
func main() {
    logger.Init("info")           // 初始化日志
    server.Init("")               // 加载配置（YAML）
    LoadModelProviders("")        // 加载模型提供商配置
    dao.InitDB()                  // 初始化 MySQL
    dao.InitLLMFactory()          // 初始化 LLM 工厂
    engine.Init(&config.DocEngine) // 初始化 C++ 文档解析引擎
    cache.Init(&config.Redis)     // 初始化 Redis
    // ... 启动 Gin HTTP 服务
}
```

### 2.2 核心 Handler

RAGFlow 的 Go Handler 负责所有轻量 API：

| Handler | 职责 |
|---------|------|
| `AuthHandler` | 用户认证（邮箱注册/登录/OAuth） |
| `TenantHandler` | 租户管理 |
| `UserHandler` | 用户信息 |
| `DatasetsHandler` | 知识库管理 |
| `DocumentHandler` | 文档管理 |
| `ChunkHandler` | Chunk（元数据）管理 |
| `ChatHandler` | 对话管理 |
| `ChatSessionHandler` | 会话管理 |
| `LLMHandler` | 模型配置 |
| `FileHandler` | 文件上传/下载 |
| `ConnectorHandler` | 数据源连接器（S3/Notion/Confluence 等） |
| `SearchHandler` | 搜索应用管理 |
| `KnowledgebaseHandler` | 知识库（别名） |
| `MemoryHandler` | Agent 记忆管理 |
| `ProviderHandler` | 模型提供商管理 |

### 2.3 DAO 数据访问层

Go 服务使用 **GORM** 操作 MySQL，每个实体对应一个 DAO：

```go
// internal/entity/document.go → MongoDB
// internal/entity/canvas.go → MongoDB (图配置)
// internal/entity/chat.go → MongoDB (对话历史)
// internal/entity/search.go → MySQL (搜索应用)

type DocumentDAO struct{}
type ChatDAO struct{}
type SearchDAO struct{}
```

**有趣的发现**：Go 后端同时操作 MySQL 和 MongoDB —— MySQL 存关系数据（用户、租户、API Token），MongoDB 存文档类数据（Canvas 配置、对话历史）。

### 2.4 两层数据库架构

```
MySQL (Go/GORM)           MongoDB (Python)          Infinity (向量库)
──────────────────        ──────────────────        ──────────────────
用户、租户、权限          Canvas DSL 配置            Chunk 向量
API Token                 对话历史                   文档向量
模型配置                  任务状态                   全文索引
搜索应用                  解析结果                   检索结果
```

**Infinity（Infiniflow 自研向量库）**：支持 embedding 存储、向量检索、稀疏检索、混合检索，是 RAGFlow 推荐的向量库替代 Elasticsearch。

---

## 三、Python API 服务

### 3.1 服务入口

```python
# api/ragflow_server.py
# 独立进程，每 60 秒轮询文档处理进度
# 流程：acquire Redis 锁 → update_progress() → release 锁
```

### 3.2 REST API 路由

```
api/apps/restful_apis/
├── chat_api.py          ← 对话 API（对话、检索、生成）
├── document_api.py       ← 文档上传/解析
├── kb_api.py            ← 知识库 API
├── file_api.py          ← 文件操作
└── ...
```

### 3.3 Python 服务职责

Python 层处理所有 **CPU/IO 密集型任务**：

| 模块 | 职责 |
|------|------|
| `rag/svr/task_executor.py` | 异步任务执行器（文档解析、Embedding） |
| `rag/flow/pipeline.py` | 文档处理 Pipeline 执行引擎 |
| `deepdoc/` | PDF/Word/Excel 等文档解析 |
| `agent/canvas.py` | Agent 图执行引擎 |
| `rag/graphrag/` | GraphRAG 知识图谱构建 |

---

## 四、Canvas 图执行引擎 ⭐（Agent 核心）

### 4.1 三层架构

RAGFlow 的核心是一个 **DSL 驱动的图执行引擎**，分为三层：

```
Graph（基类）
  └── Canvas（对话 Agent）
        └── Pipeline（文档处理）
```

**Graph 基类**：纯图结构，管理 components 和上下游关系。

**Canvas 类**：扩展为对话 Agent，增加了：
- `globals`：全局变量（sys.query, sys.history, sys.files 等）
- `variables`：用户自定义变量
- `history`：对话历史
- `retrieval`：RAG 检索结果
- `memory`：Agent 记忆

**Pipeline 类**：扩展为文档处理，增加了：
- `doc_id`：当前处理的文档 ID
- 进度回调（callback）
- Redis 日志追踪

### 4.2 DSL 图格式

```json
{
  "components": {
    "begin": {
      "obj": { "component_name": "Begin", "params": {} },
      "downstream": ["retrieval_0"],
      "upstream": []
    },
    "retrieval_0": {
      "obj": { "component_name": "Retrieval", "params": { "top_n": 8 } },
      "downstream": ["generate_0"],
      "upstream": ["begin"]
    },
    "generate_0": {
      "obj": { "component_name": "Agent", "params": { "max_rounds": 5 } },
      "downstream": ["answer_0"],
      "upstream": ["retrieval_0"]
    }
  },
  "history": [],
  "path": ["begin"],
  "retrieval": { "chunks": [], "doc_aggs": [] },
  "globals": { "sys.query": "", "sys.history": [], "sys.files": [] }
}
```

**设计亮点**：
- 每个组件用 UUID-like ID（如 `retrieval_0`）而非真实名称
- `upstream`/`downstream` 双向记录，方便双向遍历
- `path` 数组记录执行路径（拓扑排序结果）
- `globals` 是全局 KV 存储，所有组件共享

### 4.3 变量引用机制

RAGFlow 实现了类似模板引擎的 **变量插值**：

```python
# {cpn_id@var_name} 引用其他组件的输出
# {sys.query} 引用全局系统变量
# {env.var_name} 引用用户自定义变量

# 解析示例
"{retrieval_0@_references}"  →  retrieval_0 组件的 _references 输出
"{sys.query}"               →  系统查询变量
```

```python
def get_value_with_variable(self, value: str) -> Any:
    # 正则匹配 {xxx@yyy} 或 {sys.xxx}
    pat = re.compile(r'\{* *\{([a-zA-Z:0-9]+@[A-Za-z0-9_.-]+|sys\.[A-Za-z0-9_.]+|env\.[A-Za-z0-9_.]+)\} *\}*')
    # 替换所有变量引用为实际值
```

### 4.4 组件注册系统

```python
from agent.component import component_class

# 动态加载组件
param = component_class("Retrieval" + "Param")()
obj = component_class("Retrieval")(self, cpn_id, param)

# 组件继承关系
ComponentBase ← ToolBase ← Retrieval
              ← LLM ← Agent ← AgentWithTools
              ← Begin / Categorize / Switch / Loop / ...
```

**这种设计的优势**：组件定义和组件执行完全解耦，新增组件只需注册到 `component_class` 字典，不需要改引擎代码。

### 4.5 组件类型一览

| 分类 | 组件 | 功能 |
|------|------|------|
| **控制流** | Begin | 入口节点 |
| | Exit Loop | 退出循环 |
| | Switch / Categorize | 条件分支/问题分类 |
| | Iteration / Loop | 迭代/循环 |
| **LLM** | LLM | 纯 LLM 调用 |
| | Agent | 带工具的 Agent |
| | Agent with Tools | 多工具 Agent |
| **检索** | Retrieval | RAG 检索（向量化+重排） |
| **数据** | Message | 消息输出 |
| | Variable Assigner | 变量赋值 |
| | Variable Aggregator | 变量聚合 |
| | String Transform | 字符串处理 |
| **专业** | Fillin | 表单填充 |
| | Excel Processor | Excel 分析 |
| | Docs Generator | 文档生成 |
| | Data Operations | 数据操作 |
| | List Operations | 列表操作 |
| | Invoke | 外部调用 |

### 4.6 执行流程（Async）

```python
async def run(self, **kwargs):
    self.globals["sys.query"] = kwargs.get("query")
    self.add_user_input(kwargs["query"])

    # 异步执行：遍历 path，按拓扑序执行
    for cpn_id in self.path:
        cpn = self.components[cpn_id]["obj"]

        # 替换变量引用
        for key, val in cpn._param.__dict__.items():
            if isinstance(val, str):
                val = self.get_value_with_variable(val)
                cpn._param.__dict__[key] = val

        # 执行为异步协程
        if asyncio.iscoroutinefunction(cpn.render):
            result = await cpn.render()
        else:
            result = cpn.render()

        # 更新 path（动态图：某些节点可能改变下游）
        self.path = self.update_path()
```

---

## 五、DeepDoc 文档解析系统 ⭐

### 5.1 多格式解析架构

```
deepdoc/
├── parser/
│   ├── pdf_parser.py         ← PDF 解析
│   ├── docx_parser.py        ← Word 解析
│   ├── excel_parser.py       ← Excel 解析
│   ├── ppt_parser.py         ← PPT 解析
│   ├── html_parser.py        ← HTML 解析
│   ├── markdown_parser.py    ← Markdown 解析
│   ├── docling_parser.py      ← Docling（先进解析器）
│   ├── mineru_parser.py       ← MinerU（先进解析器）
│   ├── paddleocr_parser.py   ← PaddleOCR
│   └── figure_parser.py      ← 图片提取
└── vision/
    ├── recognizer.py          ← 布局识别（YOLOv10）
    ├── ocr.py                ← OCR 识别
    ├── layout_recognizer.py  ← 布局分析
    └── table_structure_recognizer.py  ← 表格结构识别
```

**支持的解析方法**（用户可选）：
- **Naive**：简单按页/段落切分
- **Table**：表格优先解析
- **Docling**：Meta AI 的 Docling 解析器
- **MinerU**：字节跳动的 MinerU 解析器
- **Manual**：手动标注

### 5.2 PDF 解析流程

```python
# deepdoc/vision/__init__.py
def init_in_out(args):
    # 1. PDF → 图片（pdfplumber，300 DPI）
    with pdfplumber.open(fnm) as pdf:
        images = [p.to_image(resolution=72 * zoomin).annotated
                  for i, p in enumerate(pdf.pages)]

    # 2. 图片 → 布局识别（YOLOv10）
    recognizer = AscendLayoutRecognizer()  # 或 LayoutRecognizer4YOLOv10
    layout_result = recognizer.predict(images)

    # 3. 布局 → OCR + 表格识别
    ocr = OCR()
    table_recognizer = TableStructureRecognizer()
    for block in layout_result:
        if block.type == "text":
            text = ocr.recognize(block.coords)
        elif block.type == "table":
            table_data = table_recognizer.recognize(block.coords)

    # 4. 关键信息提取
    extractor =Extractor()
    entities = extractor.extract(layout_result)
```

### 5.3 表格识别特别处理

表格是 RAG 的难点，RAGFlow 用两阶段识别：

```
阶段 1: 表格结构识别
  → 找出表格边界（行/列/单元格位置）

阶段 2: 表格内容 OCR
  → 对每个单元格内容进行 OCR

结果输出:
  - HTML 格式表格（保留结构）
  - Markdown 格式（便于 LLM 理解）
  - 原始文本（用于向量检索）
```

---

## 六、RAG 检索系统 ⭐

### 6.1 Retrieval 组件参数

```python
class RetrievalParam(ToolParamBase):
    similarity_threshold = 0.2       # 相似度阈值
    keywords_similarity_weight = 0.5  # 关键词权重
    top_n = 8                        # 返回 Top N chunks
    top_k = 1024                     # Token 数量上限
    dataset_ids = []                 # 目标知识库
    rerank_id = ""                   # 重排模型 ID
    empty_response = ""              # 空结果提示
    use_kg = False                  # 是否启用知识图谱
    cross_languages = []              # 跨语言检索
    toc_enhance = False              # 目录增强
    meta_data_filter = {}            # 元数据过滤
```

### 6.2 检索流程

```
Query 输入
  ↓
1. Query 扩展（可选，跨语言）
  ↓
2. 向量检索（Infinity/Elasticsearch）
  ↓
3. BM25 全文检索（关键词匹配）
  ↓
4. 混合排序（向量相似度 × 关键词权重）
  ↓
5. Rerank 重排（可选，LLM-as-judge）
  ↓
6. 元数据过滤
  ↓
7. 引用溯源（Chunk → Document）
  ↓
8. 上下文拼接（格式化为 LLM 输入）
```

### 6.3 向量数据库：Infinity

Infinity 是 Infiniflow 自研的向量数据库（RAGFlow 的母公司），Go 服务通过 Infinity Go SDK 操作：

```go
// internal/service/search.go
// Infinity 提供向量插入、ANN 检索、混合检索
```

Python 侧通过 `rag/svr/task_executor.py` 与 Infinity 交互。

**Infinity 特色**：
- 统一的稠密向量 + 稀疏向量检索
- 支持 SQL-like 查询
- 高性能（Rust 实现）
- 与 Elasticsearch 混用（全文 + 向量双引擎）

### 6.4 Raptor 检索

Raptor 是树形检索策略，当传统向量检索不够用时启用：

```
传统向量检索: 查询 → Top-K chunks
     ↓ （结果不够时）
Raptor 检索: 查询 → 聚类树 → 多层摘要 → 召回更广的 chunks
```

**核心思想**：在粗粒度（高层聚类节点）先做一个语义摘要匹配，快速定位可能相关的区域，再在细粒度层精确召回。

---

## 七、Agent 系统 ⭐

### 7.1 Agent 执行循环

```python
class Agent(LLM, ToolBase):
    async def render(self):
        reasoning = ""
        max_rounds = self._param.max_rounds  # 默认 5

        for round in range(max_rounds):
            # 1. LLM 生成（带工具调用）
            response = await self._call_llm_with_tools(
                tools=self.tools,    # 加载的工具列表
                messages=self._history,
            )

            # 2. 检查是否有工具调用
            if response.tool_calls:
                # 3. 执行工具
                for tool_call in response.tool_calls:
                    result = await self._execute_tool(tool_call)
                    self._history.append(result)
            else:
                # 4. 无工具调用，直接返回
                return response.content

        return "Max rounds reached"
```

### 7.2 工具系统

```python
class ToolBase(ABC):
    def _load_tool(self, tool_config):
        # 从配置动态加载工具
        tool_name = tool_config["name"]
        if tool_name in self.built_in_tools:
            return self.built_in_tools[tool_name]
        # 或从 MCP 协议加载
        return MCPToolLoader.load(tool_name)

# 内置工具
built_in_tools = {
    "retrieval": Retrieval,           # 知识库检索
    "code_exec": CodeExecution,       # 代码执行
    "duckduckgo": DuckDuckGoSearch,   # 网页搜索
    "wikipedia": WikipediaSearch,      # Wikipedia
    "arxiv": ArxivSearch,             # 学术论文
    "github": GitHubSearch,           # GitHub
    "google": GoogleScholar,          # 学术搜索
    "tavily": TavilySearch,           # AI 搜索
    "akshare": AKShare,               # 金融数据
    "jin10": Jin10News,               # 财经资讯
    "pubmed": PubMedSearch,           # 医学文献
    "tushare": TuShare,               # A股数据
    "deepl": DeepLTranslate,          # 翻译
    "email": EmailTool,               # 邮件
    "exesql": ExeSQL,                 # SQL 执行
    "crawler": WebCrawler,            # 网页爬虫
}
```

### 7.3 MCP 协议支持

RAGFlow 支持 **Model Context Protocol**，可以接入外部工具服务：

```python
from common.mcp_tool_call_conn import MCPToolCallSession

# MCP Server 注册后，工具通过 MCP 调用外部服务
mcp_session = MCPToolCallSession(mcp_config)
result = await mcp_session.call_tool("tool_name", params)
```

### 7.4 LLM 调用封装

```python
class LLMBundle:
    """统一 LLM 调用封装"""
    def chat(self, model, messages, stream=False, tools=None):
        # 支持 OpenAI / Anthropic / Azure / DashScope / Local 等
        provider = self.get_provider(model)
        return provider.chat(model, messages, stream, tools)
```

**支持的模型提供商**（通过 `conf/model_providers.yaml` 配置）：
- OpenAI GPT 系列
- Anthropic Claude 系列
- Azure OpenAI
- DashScope（阿里通义）
- Local 模型（Ollama/vLLM）
- Cohere
- DeepSeek
- Gemini
- Groq
- 等等

---

## 八、GraphRAG 系统 ⭐

### 8.1 GraphRAG 架构

RAGFlow 内置了 **GraphRAG**（基于微软 GraphRAG 改进）：

```python
# rag/graphrag/general/index.py
async def run_graphrag_for_kb(kb_id, tenant_id):
    # 1. 文档 → 实体抽取
    extractor = GeneralKGExt()
    entities, relationships = extractor.extract(documents)

    # 2. 社区检测（Leiden 算法）
    G = build_entity_graph(entities, relationships)
    communities = leiden_clustering(G)

    # 3. 社区摘要生成（LLM）
    community_reports = generate_community_reports(communities, G)

    # 4. 存储到图数据库
    store_graph(entities, relationships, community_reports)
```

### 8.2 知识图谱构建流程

```
原始文档
  ↓
实体抽取（LLM）→ 节点：人物/组织/地点/概念
  ↓
关系抽取（LLM）→ 边：（实体A, 关系, 实体B）
  ↓
社区检测（Leiden）→ 聚类相关实体
  ↓
社区摘要（LLM）→ 每个社区生成摘要
  ↓
存储到图数据库（NetworkX → 持久化）
```

### 8.3 知识图谱检索

```python
# 查询时，混合使用：
# 1. 传统向量检索 → 获取相关 chunks
# 2. 图检索 → 获取相关实体和社区
# 3. 混合 → 最终结果

# GraphRAG 检索层级：
# - 源文档（Source）→ 直接引用
# - 实体（Entity）→ 精确事实
# - 社区（Community）→ 宽泛主题
# - 社区报告（Community Report）→ 全局概览
```

---

## 九、文档分块（Chunking）策略

### 9.1 Token Chunking

```python
# rag/flow/chunker/token_chunker.py
class TokenChunker:
    """
    按 Token 数切分文档块
    chunk_size: 每块 token 数（默认 512）
    chunk_overlap: 重叠 token 数（默认 64）
    """
    def chunk(self, text, chunk_size=512, overlap=64):
        tokens = self._tokenize(text)
        chunks = []
        for i in range(0, len(tokens), chunk_size - overlap):
            chunk_tokens = tokens[i:i + chunk_size]
            chunks.append(self._detokenize(chunk_tokens))
        return chunks
```

### 9.2 标题感知分块

```python
# rag/flow/chunker/title_chunker/
# 识别文档层级结构（标题 H1/H2/H3）
# 保证每个块从标题开始，不跨章节切分
```

### 9.3 分块策略对比

| 策略 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| Naive | 固定 token 数滑动窗口 | 简单 | 可能切断语义 |
| Title-aware | 识别标题，按标题边界切 | 保留语义结构 | 块大小不均匀 |
| Table | 表格整块保留 | 表格完整性 | 大表格 token 超限 |
| Docling/MinerU | 语义感知切分（LLM） | 最精确 | 慢、贵 |
| Hierarchical | 递归按层级切分 | 多粒度 | 复杂 |

---

## 十、异步任务系统

### 10.1 任务执行器

```python
# rag/svr/task_executor.py
# 独立线程，每轮询执行：
# 1. 从 Redis 队列获取待处理任务
# 2. 根据任务类型分发
# 3. 更新 MongoDB 任务状态
# 4. 回调进度（Redis Pub/Sub）
```

### 10.2 任务类型

| 任务类型 | 说明 |
|---------|------|
| `parse` | 文档解析（PDF → 文本/图片/表格） |
| `embedding` | 生成 Embedding 向量 |
| `rename` | 重命名文档 |
| `rm` | 删除文档 |
| `recover` | 恢复删除 |
| `reprocess` | 重新处理文档 |

### 10.3 分布式锁

```python
# rag/utils/redis_conn.py
class RedisDistributedLock:
    def acquire(self):
        # SET NX EX 实现 Redis 分布式锁
        return REDIS_CONN.set(self.key, lock_value, nx=True, ex=timeout)

    def release(self):
        # Lua 脚本：只有持有锁才能释放（防误删）
        EVAL(script, 1, key, lock_value)
```

---

## 十一、部署架构

### 11.1 Docker Compose 结构

```yaml
services:
  ragflow:
    image: infiniflow/ragflow:latest
    ports: ["9380:9380"]
    environment:
      - LOG_LEVEL=info
      - MYSQL_PASSWORD=xxx
      - MINIO_PASSWORD=xxx
    volumes:
      - ./conf:/ragflow/conf
      - ./db/db_sqlite.db:/ragflow/db/db_sqlite.db
      - ./s3file:/ragflow/s3file

  # 依赖服务（docker/compose 目录）
  mysql-8:
  mongodb-7:
  redis-7:
  elasticsearch-8:
  infinity:    # Infiniflow 向量库
  minio:
```

### 11.2 环境配置

```yaml
# conf/service_conf.yaml
# Go 服务配置：端口、数据库连接、模型提供商
# Python 服务：Embedding 模型、解析引擎配置
# Infinity 配置：向量维度、索引参数
# 模型提供商：API Key、Endpoint、超时配置
```

---

## 十二、设计亮点与面试可讲的点

### 12.1 双语言混合架构

**为什么 Go + Python？**

| 考量 | Go | Python |
|------|-----|--------|
| 启动速度 | 即时（编译） | 慢（解释器加载） |
| 内存占用 | ~10MB | ~100MB+ |
| 并发能力 | Goroutine（轻量） | GIL 限制 |
| ML 生态 | 无 | Numpy/PyTorch丰富 |
| 开发速度 | 中 | 快 |

**RAGFlow 的解法**：
- Go 处理 HTTP 路由和轻量查询（低内存、即时响应）
- Python 处理 ML 推理（灵活、库丰富）
- 两者完全解耦，通过共享数据层通信

### 12.2 DSL 驱动的工作流

**和 FastGPT 对比**：

| 维度 | FastGPT | RAGFlow |
|------|---------|---------|
| 工作流格式 | JSON 模块图 | JSON DSL 图 |
| 执行引擎 | Go（WorkflowQueue） | Python（Canvas/Graph） |
| 节点类型 | 20+ 内置节点 | 20+ 组件 |
| 循环支持 | 支持（Tarjan 检测） | 支持（Loop/Iteration） |
| 变量机制 | 运行时上下文传递 | 模板插值 `{cpn@var}` |

**RAGFlow 的 DSL 亮点**：
- 变量引用语法简洁直观
- 组件按类型自动分类（控制流/LLM/数据）
- 图可以序列化保存（`__str__` 返回 JSON）

### 12.3 向量库多选支持

```python
# 检索层通过配置切换向量库
VectorStore = {
    "infinity": InfinityCtrl,
    "elasticsearch": ElasticsearchCtrl,
    "pgvector": PgVectorCtrl,
}
```

**Infinity 特色**：稠密向量 + 稀疏向量统一索引，一次查询返回混合结果，不需要二次混合。

### 12.4 文档解析的分层设计

```
DeepDoc（Python 解析层）
  ├── YOLOv10（布局识别）→ 找出文本块/表格/图片位置
  ├── PaddleOCR（文字识别）→ 提取文本内容
  ├── TableStructureRec → 表格结构还原
  └── 切分策略 → 按语义块切分

C++ 引擎（可选加速层）
  └── SWIG 绑定 → 关键路径 C++ 实现
```

### 12.5 GraphRAG 与传统 RAG 的融合

```python
# 检索时同时执行：
retrieval_results = await vector_search(query, top_k)
graph_results = await graph_search(query, community_level)
kg_results = await entity_search(query)

# 混合排序
final_results = rerank(
    candidates = retrieval_results + graph_results + kg_results,
    query = query
)
```

### 12.6 工程化亮点

1. **Redis 分布式锁**：所有状态变更加锁，防止并发冲突
2. **异步任务队列**：文档解析/Embedding 完全异步，不阻塞 API
3. **进度实时推送**：通过 Redis Pub/Sub + SSE 推送解析进度
4. **MCP 协议**：标准化外部工具接入
5. **模型热插拔**：通过配置文件切换 LLM/Embedding/Rerank 模型

---

## 十三、与 FastGPT 对比总结

| 维度 | FastGPT | RAGFlow |
|------|---------|---------|
| 主语言 | Node.js + TypeScript | Go + Python |
| 工作流引擎 | 自研（WorkflowQueue，1677 行 Go） | 自研（Canvas Graph，Python） |
| 文档解析 | 基础切分 | DeepDoc（YOLOv10 + OCR） |
| RAG 检索 | pgvector（默认） | Infinity/ES 双引擎 |
| GraphRAG | 无 | 内置 |
| 工具生态 | MCP + 插件 | MCP + 内置 20+ 工具 |
| 前端 | Next.js Pages Router | React + Vite + Tailwind |
| 多租户 | Team/Member 模型 | Tenant/User 模型 |
| 部署 | Docker + K8s | Docker Compose + K8s Helm |

---

*文档生成时间：2026-04-12*
*基于 RAGFlow v0.24.0 源码分析*
