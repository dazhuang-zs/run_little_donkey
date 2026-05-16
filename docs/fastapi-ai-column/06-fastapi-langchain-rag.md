# FastAPI + LangChain构建RAG知识库

> **文章信息**
> - 标题：FastAPI + LangChain构建RAG知识库
> - 字数：4500字
> - 预估阅读时间：20分钟
> - 难度：⭐⭐⭐⭐☆

---

## 一、为什么RAG是AI应用的必经之路

2024年RAG（Retrieval-Augmented Generation）已经成为企业AI应用的事实标准。原因很简单：大模型的知识有截止日期，且无法回答你公司内部的私有数据。RAG通过"检索+生成"的混合架构，让模型在最新、最私有、最专业的信息上作答。

FastAPI + LangChain是当前构建RAG系统最主流的技术组合，原因是：

1. **Python优先**：LangChain本身是Python生态，两者天然契合
2. **异步原生**：FastAPI异步特性与LangChain的LCEL（LangChain Expression Language）配合流畅
3. **可观测性强**：中间结果（检索到的文档、得分、生成过程）都能通过FastAPI暴露为API
4. **生产就绪**：流式输出（SSE）、并发控制、错误处理都能用FastAPI原生能力实现

## 二、RAG核心原理

```
用户问题 → 改写/向量化 → 向量数据库检索 → 上下文组装 → LLM生成 → 返回答案
```

完整RAG流程分为**索引阶段**和**检索阶段**：

**索引阶段（离线）**：
```
文档 → 加载(Loader) → 切分(Chunker) → 向量化(Embedding) → 写入向量数据库
```

**检索阶段（在线）**：
```
用户问题 → 向量化 → 相似度检索 → Top-K文档 → 组装Prompt → LLM生成 → 回答
```

## 三、向量数据库选型

| 数据库 | 适用场景 | 优点 | 缺点 |
|--------|----------|------|------|
| Chroma | 原型/小型应用 | 轻量、嵌入式、一键启动 | 不适合生产，不支持分布式 |
| FAISS | 中型数据、单机部署 | Meta开源、检索速度快、支持量化和聚类 | 无云原生、运维复杂 |
| Qdrant | 生产级应用 | 支持过滤条件、分布式、云原生API | 资源占用较高 |
| Milvus | 超大规模数据 | 亿级向量支持、成熟社区 | 部署运维复杂 |
| Pinecone | 云原生全托管 | 免运维、自动扩容 | 需要付费、供应商锁定 |

**选型建议**：
- 个人项目/原型 → Chroma
- 中型企业内部系统 → Qdrant（Docker一键部署）
- 大型企业/超大规模 → Milvus或Pinecone

本文演示用**Chroma**（快速原型）和**Qdrant**（生产级）两种方案。

## 四、完整项目结构

```
fastapi-rag/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_loader.py    # 文档加载
│   │   ├── text_splitter.py      # 文本切分
│   │   ├── embedder.py           # 向量化
│   │   ├── vector_store.py       # 向量库管理
│   │   └── rag_chain.py         # RAG链
│   └── routes/
│       ├── __init__.py
│       ├── ingest.py             # 文档入库路由
│       └── query.py              # 查询路由
├── data/
│   └── sample.pdf                # 测试文档
├── .env
├── requirements.txt
└── pyproject.toml
```

## 五、环境安装

```bash
mkdir fastapi-rag && cd fastapi-rag
uv venv --python 3.12
source .venv/bin/activate

# 核心依赖
uv pip install \
    fastapi uvicorn \
    langchain langchain-core langchain-community \
    langchain-deepseek \
    chromadb qdrant-client \
    unstructured[pdf] python-dotenv \
    pydantic-settings \
    sse-starlette tiktoken \
    httpx aiofiles
```

## 六、配置管理

```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal

class Settings(BaseSettings):
    # DeepSeek Embedding配置
    deepseek_api_key: str = "sk-your-key"
    deepseek_base_url: str = "https://api.deepseek.com"
    embed_model: str = "deepseek-embed"
    
    # LLM配置
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048
    
    # 向量库配置
    vector_store_type: Literal["chroma", "qdrant"] = "chroma"
    chroma_persist_dir: str = "./data/chroma_db"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "rag_knowledge_base"
    qdrant_vector_size: int = 1536  # DeepSeek Embedding维度
    
    # RAG配置
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 5
    similarity_threshold: float = 0.6
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

## 七、文档加载与切分

### 7.1 文档加载服务

LangChain提供了丰富的文档加载器，支持PDF、Markdown、HTML、TXT、CSV等多种格式：

```python
# app/services/document_loader.py
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredMarkdownLoader,
    TextLoader,
    CSVLoader,
)
from langchain_core.documents import Document
from pathlib import Path
from typing import Optional

class DocumentLoaderService:
    """统一文档加载服务，支持多种格式"""
    
    LOADERS = {
        ".pdf": PyPDFLoader,
        ".md": UnstructuredMarkdownLoader,
        ".txt": TextLoader,
        ".csv": CSVLoader,
    }
    
    @classmethod
    def get_loader(cls, file_path: str) -> Optional[object]:
        """根据文件扩展名返回对应的加载器"""
        ext = Path(file_path).suffix.lower()
        loader_cls = cls.LOADERS.get(ext)
        if not loader_cls:
            return None
        return loader_cls(file_path)
    
    @classmethod
    def load_file(cls, file_path: str) -> list[Document]:
        """加载单个文件"""
        loader = cls.get_loader(file_path)
        if not loader:
            raise ValueError(f"Unsupported file type: {file_path}")
        
        # PyPDFLoader需要单独处理编码
        if isinstance(loader, PyPDFLoader):
            docs = loader.load_and_split()
        else:
            docs = loader.load()
        
        return docs
    
    @classmethod
    def load_directory(cls, directory: str, glob_pattern: str = "**/*") -> list[Document]:
        """批量加载目录下的所有文档"""
        all_docs = []
        for file_path in Path(directory).glob(glob_pattern):
            try:
                docs = cls.load_file(str(file_path))
                for doc in docs:
                    doc.metadata["source_file"] = str(file_path)
                all_docs.extend(docs)
            except Exception as e:
                print(f"Failed to load {file_path}: {e}")
        return all_docs
```

### 7.2 文本切分策略

切分是RAG质量最关键的一步。切得太长，上下文窗口浪费；切得太短，语义断裂。推荐使用`RecursiveCharacterTextSplitter`：

```python
# app/services/text_splitter.py
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import Optional

class TextSplitterService:
    """智能文本切分服务"""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[list[str]] = None,
    ):
        if separators is None:
            separators = [
                "\n\n",   # 优先按段落切分
                "\n",     # 然后按句子切分
                "。",     # 中文句号
                "！",     # 中文感叹号
                "？",     # 中文问号
                " ",      # 空格
                "",      # 最后按字符切分
            ]
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=self._len_with_chinese,
        )
    
    @staticmethod
    def _len_with_chinese(text: str) -> int:
        """中文字符算1个字符，英文按字符计算"""
        return len(text)
    
    def split_documents(self, documents: list[Document]) -> list[Document]:
        """切分文档列表"""
        if not documents:
            return []
        chunks = self.splitter.split_documents(documents)
        
        # 为每个chunk添加序号元数据
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["total_chunks"] = len(chunks)
        
        return chunks
```

**踩坑记录1**：中文切分使用英文默认separator会导致"我是一个好人"被切成"我是一个"+"好人"，语义割裂。务必自定义中文separator列表。

## 八、Embedding服务（DeepSeek）

```python
# app/services/embedder.py
from langchain_core.embeddings import Embeddings
from langchain_deepseek import DeepSeekEmbeddings
from app.config import get_settings
from functools import lru_cache

class DeepSeekEmbedder(Embeddings):
    """DeepSeek Embedding封装"""
    
    def __init__(self, api_key: str, model: str = "deepseek-embed"):
        self._embedder = DeepSeekEmbeddings(
            deepseek_api_key=api_key,
            model=model,
        )
    
    def embed_query(self, text: str) -> list[float]:
        return self._embedder.embed_query(text)
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embedder.embed_documents(texts)

@lru_cache
def get_embedder() -> DeepSeekEmbedder:
    settings = get_settings()
    return DeepSeekEmbedder(
        api_key=settings.deepseek_api_key,
        model=settings.embed_model,
    )
```

## 九、向量数据库管理

### 9.1 Chroma方案（轻量级）

```python
# app/services/vector_store.py (Chroma部分)
from langchain_core.vectorstores import VectorStore
from langchain_core.documents import Document
from langchain_chroma import Chroma
from app.services.embedder import get_embedder
from app.config import get_settings

class ChromaVectorStore:
    """Chroma向量库管理"""
    
    def __init__(self, collection_name: str = "documents"):
        settings = get_settings()
        self._embedder = get_embedder()
        self._persist_dir = settings.chroma_persist_dir
        self._collection_name = collection_name
        self._vectorstore: VectorStore | None = None
    
    def _get_or_create(self) -> VectorStore:
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                collection_name=self._collection_name,
                embedding_function=self._embedder,
                persist_directory=self._persist_dir,
            )
        return self._vectorstore
    
    def add_documents(self, documents: list[Document]) -> list[str]:
        """入库文档"""
        vs = self._get_or_create()
        return vs.add_documents(documents)
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: dict | None = None,
    ) -> list[Document]:
        """相似度检索"""
        vs = self._get_or_create()
        return vs.similarity_search(query, k=k, filter=filter)
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: dict | None = None,
    ) -> list[tuple[Document, float]]:
        """带得分的相似度检索"""
        vs = self._get_or_create()
        return vs.similarity_search_with_score(query, k=k, filter=filter)
    
    def delete_collection(self) -> None:
        """清空集合"""
        vs = self._get_or_create()
        vs.delete_collection()
        self._vectorstore = None
```

### 9.2 Qdrant方案（生产级）

```python
# app/services/vector_store.py (Qdrant部分)
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from app.config import get_settings

class QdrantVectorStore:
    """Qdrant向量库管理"""
    
    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection_name: str = "rag_knowledge_base",
        vector_size: int = 1536,
    ):
        settings = get_settings()
        self._embedder = get_embedder()
        self._url = settings.qdrant_url
        self._collection = settings.qdrant_collection
        self._vector_size = settings.qdrant_vector_size
        self._client = QdrantClient(url=self._url)
        self._vectorstore: VectorStore | None = None
    
    def _ensure_collection(self) -> None:
        """确保集合存在，不存在则创建"""
        collections = self._client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self._collection not in collection_names:
            from qdrant_client.http import models
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=models.VectorParams(
                    size=self._vector_size,
                    distance=models.Distance.COSINE,
                ),
            )
            print(f"Created Qdrant collection: {self._collection}")
    
    def _get_or_create(self) -> VectorStore:
        if self._vectorstore is None:
            self._ensure_collection()
            self._vectorstore = QdrantVectorStore(
                client=self._client,
                collection_name=self._collection,
                embedding=self._embedder,
            )
        return self._vectorstore
    
    def add_documents(self, documents: list[Document]) -> list[str]:
        vs = self._get_or_create()
        return vs.add_documents(documents)
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: dict | None = None,
    ) -> list[tuple[Document, float]]:
        vs = self._get_or_create()
        return vs.similarity_search_with_score(query, k=k, filter=filter)
```

## 十、RAG检索链

```python
# app/services/rag_chain.py
from langchain_core.documents import Document
from langchain_core.output_interpreters import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_deepseek import ChatDeepSeek
from typing import Literal, TypedDict
from app.config import get_settings

# RAG Prompt模板
RAG_PROMPT_TEMPLATE = """你是一个专业的知识库助手。请基于以下检索到的参考资料回答用户问题。

**参考资料**:
{context}

**用户问题**: {question}

**回答要求**:
1. 必须基于参考资料回答，不要编造信息
2. 如果参考资料中没有相关信息，请明确告知用户"没有找到相关内容"
3. 回答要简洁、有条理，必要时可列出要点
4. 在回答末尾注明参考来源

回答:"""

RAG_PROMPT = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

class RetrievedDocs(TypedDict):
    """带元数据的检索结果"""
    content: str
    source: str
    score: float
    chunk_index: int

class RAGChain:
    """RAG检索生成链"""
    
    def __init__(self):
        settings = get_settings()
        self._llm = ChatDeepSeek(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
        self._top_k = settings.top_k
        self._similarity_threshold = settings.similarity_threshold
    
    def _format_docs(self, docs: list[Document]) -> str:
        """将检索到的文档格式化为上下文字符串"""
        formatted = []
        for i, doc in enumerate(docs):
            source = doc.metadata.get("source_file", "unknown")
            chunk_idx = doc.metadata.get("chunk_index", i)
            formatted.append(
                f"[文档{i+1}] 来源: {source} (chunk #{chunk_idx})\n{doc.page_content}"
            )
        return "\n\n---\n\n".join(formatted)
    
    def _build_chain(self, retriever):
        """构建RAG链"""
        return (
            {"context": retriever | self._format_docs, "question": RunnablePassthrough()}
            | RAG_PROMPT
            | self._llm
            | StrOutputParser()
        )
    
    def query(self, question: str, retriever) -> tuple[str, list[RetrievedDocs]]:
        """执行RAG查询"""
        # 先检索
        docs_with_scores = retriever.invoke(question)
        
        # 过滤低分结果
        filtered_docs = [
            doc for doc, score in docs_with_scores
            if score >= self._similarity_threshold
        ]
        
        if not filtered_docs:
            return "没有找到与您问题相关的参考资料。请尝试调整问题的表述或确认知识库中是否有相关内容。", []
        
        # 构建链并执行
        chain = self._build_chain(retriever)
        answer = chain.invoke(question)
        
        # 构造检索结果摘要
        retrieved: list[RetrievedDocs] = [
            {
                "content": doc.page_content[:100] + "...",
                "source": doc.metadata.get("source_file", "unknown"),
                "score": score,
                "chunk_index": doc.metadata.get("chunk_index", 0),
            }
            for doc, score in docs_with_scores
        ]
        
        return answer, retrieved
```

## 十一、FastAPI路由封装

```python
# app/models.py
from pydantic import BaseModel, Field
from typing import Optional

class IngestRequest(BaseModel):
    file_path: str = Field(description="要入库的文档路径")
    collection_name: Optional[str] = Field(default=None, description="集合名称")

class IngestResponse(BaseModel):
    status: str
    chunks_count: int
    document_id: str

class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000, description="用户问题")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="检索数量")
    stream: bool = Field(default=False, description="是否启用流式输出")

class RetrievedDoc(BaseModel):
    content: str
    source: str
    score: float
    chunk_index: int

class QueryResponse(BaseModel):
    answer: str
    retrieved_docs: list[RetrievedDoc]
    total_retrieved: int
```

```python
# app/routes/ingest.py
from fastapi import APIRouter, HTTPException
from app.models import IngestRequest, IngestResponse
from app.services.document_loader import DocumentLoaderService
from app.services.text_splitter import TextSplitterService
from app.services.vector_store import ChromaVectorStore
from app.config import get_settings
import uuid

router = APIRouter(prefix="/ingest", tags=["文档入库"])

@router.post("/", response_model=IngestResponse)
async def ingest_document(request: IngestRequest):
    """文档入库：加载→切分→向量化→存储"""
    try:
        settings = get_settings()
        
        # 1. 加载文档
        docs = DocumentLoaderService.load_file(request.file_path)
        if not docs:
            raise HTTPException(status_code=400, detail="文档加载失败，无内容")
        
        # 2. 切分
        splitter = TextSplitterService(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        chunks = splitter.split_documents(docs)
        
        # 3. 入库
        vector_store = ChromaVectorStore(
            collection_name=request.collection_name or "default"
        )
        doc_ids = vector_store.add_documents(chunks)
        
        return IngestResponse(
            status="success",
            chunks_count=len(chunks),
            document_id=doc_ids[0] if doc_ids else str(uuid.uuid4()),
        )
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"文件不存在: {request.file_path}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"入库失败: {str(e)}")
```

```python
# app/routes/query.py
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.models import QueryRequest, QueryResponse, RetrievedDoc
from app.services.vector_store import ChromaVectorStore
from app.services.rag_chain import RAGChain
from app.config import get_settings
import asyncio

router = APIRouter(prefix="/query", tags=["RAG查询"])

@router.post("/", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """知识库问答"""
    try:
        settings = get_settings()
        
        # 获取向量库和检索器
        vector_store = ChromaVectorStore()
        retriever = vector_store.similarity_search_with_score
        
        # 执行RAG查询
        rag = RAGChain()
        answer, retrieved_docs = rag.query(request.question, retriever)
        
        return QueryResponse(
            answer=answer,
            retrieved_docs=[
                RetrievedDoc(**doc) for doc in retrieved_docs[:request.top_k]
            ],
            total_retrieved=len(retrieved_docs),
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@router.post("/stream")
async def query_stream(request: QueryRequest):
    """流式RAG问答（Server-Sent Events）"""
    async def event_generator():
        try:
            settings = get_settings()
            vector_store = ChromaVectorStore()
            rag = RAGChain()
            
            answer, retrieved = rag.query(request.question, vector_store.similarity_search_with_score)
            
            # 先发送检索结果
            yield f"event: retrieved\ndata: {retrieved}\n\n"
            
            # 流式发送答案（按句子切分）
            sentences = answer.split("。")
            for i, sent in enumerate(sentences):
                if sent.strip():
                    yield f"event: token\ndata: {sent}。\n\n"
                await asyncio.sleep(0.05)
            
            yield "event: done\ndata: \n\n"
        
        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import ingest, query

app = FastAPI(title="RAG知识库API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(query.router)

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

## 十二、性能优化

### 12.1 批量入库

```python
# 避免单条入库，每次批量处理
BATCH_SIZE = 100

def batch_add_documents(vector_store, chunks: list[Document]):
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        vector_store.add_documents(batch)
        print(f"Progress: {min(i + BATCH_SIZE, len(chunks))}/{len(chunks)}")
```

### 12.2 异步并发检索

```python
# app/services/vector_store.py (异步版本)
async def async_similarity_search(
    queries: list[str],
    k: int = 5,
) -> list[list[tuple[Document, float]]]:
    """并发执行多个查询"""
    import asyncio
    
    async def single_query(q: str):
        return vector_store.similarity_search_with_score(q, k=k)
    
    tasks = [single_query(q) for q in queries]
    results = await asyncio.gather(*tasks)
    return results
```

### 12.3 Embedding缓存

```python
# 使用缓存避免重复计算相同query的embedding
from functools import lru_cache

@lru_cache(maxsize=1024)
def cached_embed_query(text: str) -> tuple[str, list[float]]:
    """缓存Embedding结果，text作为cache key"""
    return text, embedder.embed_query(text)
```

**踩坑记录2**：Embedding计算是RAG延迟的主要来源。生产环境务必做缓存，特别是高频重复查询同一个问题。

### 12.4 Chroma批量操作

```python
# Chroma原生支持批量add，避免逐条插入
vectorstore = Chroma(...)
vectorstore.add_documents(documents)  # 一次性批量入库，比循环单条入库快10倍+
```

## 十三、踩坑记录总结

| 坑 | 现象 | 解决方案 |
|----|------|----------|
| 中文切分语义割裂 | 切分后的chunk语义不完整 | 自定义separator列表，加入中文标点 |
| Chroma入库极慢 | 大量文档入库时卡死 | 使用批量add，避免循环单条入库 |
| Embedding重复计算 | 相同query重复计算 | 使用LRU缓存（@lru_cache） |
| 流式输出被nginx截断 | SSE响应被buffer截断 | nginx配置`proxy_buffering off`或去掉nginx直接代理 |
| Qdrant连接超时 | 容器未启动就访问 | 先轮询检查Qdrant健康状态再操作 |
| 相似度分数不可信 | 不同模型的score范围不同 | 设relative_threshold而非absolute threshold |
| 向量维度不匹配 | Chroma报错dimension mismatch | 确保Embedding模型输出维度与Chroma collection配置一致 |

## 十四、总结

本文完整构建了一套基于FastAPI + LangChain的RAG知识库系统，覆盖了：

1. **文档加载**：支持PDF、Markdown、TXT等多种格式
2. **智能切分**：RecursiveCharacterTextSplitter + 中文优化
3. **向量检索**：Chroma（原型）和Qdrant（生产）两种方案
4. **RAG生成链**：DeepSeek + 精选Prompt + 检索结果注入
5. **API封装**：同步查询 + 流式SSE双模式
6. **性能优化**：批量入库、缓存、异步并发

RAG的核心不在于技术实现，而在于**文档质量**和**切分策略**。再好的检索系统也拯救不了差的文档。入库前务必清洗文档格式、去除无关噪音内容。