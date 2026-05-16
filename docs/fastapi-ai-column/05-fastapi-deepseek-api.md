# 用FastAPI调用DeepSeek API搭智能助手

> **文章信息**  
> - 标题：用FastAPI调用DeepSeek API搭智能助手  
> - 字数：4200字  
> - 预估阅读时间：18分钟  
> - 难度：⭐⭐⭐☆☆

---

## 一、为什么选择DeepSeek？

2025年初，DeepSeek-R1和DeepSeek-V3的发布彻底改变了大模型的价格格局。DeepSeek API的核心优势：

1. **价格极低**：DeepSeek-V3输入价格$0.27/M tokens，仅为GPT-4o的1/30（数据来源：DeepSeek官方定价页，2025年5月）
2. **性能强劲**：在MMLU、HumanEval等基准测试中与GPT-4o持平
3. **国产可用**：国内直接访问，无需代理，延迟低
4. **兼容OpenAI格式**：API接口与OpenAI完全兼容，切换成本为零

| 模型 | 输入价格（$/M tokens） | 输出价格（$/M tokens） | 上下文长度 |
|------|----------------------|----------------------|-----------|
| DeepSeek-V3 | 0.27 | 1.10 | 64K |
| DeepSeek-R1 | 0.55 | 2.19 | 64K |
| GPT-4o | 2.50 | 10.00 | 128K |
| GPT-4o-mini | 0.15 | 0.60 | 128K |
| Qwen-Max | 2.00 | 6.00 | 32K |

> **选型建议**：日常对话和代码生成用DeepSeek-V3，复杂推理用DeepSeek-R1，需要超长上下文才考虑GPT-4o。

## 二、环境配置

### 2.1 项目结构

```
fastapi-deepseek/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI入口
│   ├── config.py            # 配置管理
│   ├── models.py            # Pydantic模型
│   ├── services/
│   │   ├── __init__.py
│   │   └── deepseek.py      # DeepSeek服务封装
│   └── routes/
│       ├── __init__.py
│       └── chat.py          # 聊天路由
├── .env                     # 环境变量
├── .env.example             # 环境变量示例
├── requirements.txt
└── pyproject.toml
```

### 2.2 安装依赖

```bash
# 创建项目
mkdir fastapi-deepseek && cd fastapi-deepseek
uv venv --python 3.12
source .venv/bin/activate

# 安装依赖
uv pip install fastapi uvicorn httpx pydantic-settings python-dotenv sse-starlette

# 验证安装
python -c "import httpx; print(f'httpx {httpx.__version__}')"
```

### 2.3 环境变量配置

创建`.env`文件：

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_DEFAULT_MODEL=deepseek-chat
DEEPSEEK_DEFAULT_MAX_TOKENS=2048
DEEPSEEK_DEFAULT_TEMPERATURE=0.7

# 服务配置
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=true
```

### 2.4 配置管理

```python
"""app/config.py - 配置管理"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class DeepSeekSettings(BaseSettings):
    """DeepSeek API配置"""
    api_key: str
    base_url: str = "https://api.deepseek.com"
    default_model: str = "deepseek-chat"
    default_max_tokens: int = 2048
    default_temperature: float = 0.7

    model_config = {"env_prefix": "DEEPSEEK_", "env_file": ".env"}


class AppSettings(BaseSettings):
    """应用配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    model_config = {"env_prefix": "APP_", "env_file": ".env"}


@lru_cache
def get_deepseek_settings() -> DeepSeekSettings:
    return DeepSeekSettings()


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()
```

## 三、Pydantic模型定义

```python
"""app/models.py - 请求/响应模型"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """聊天消息"""
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    """聊天请求"""
    messages: list[ChatMessage] = Field(
        ...,
        description="对话消息列表",
        min_length=1,
    )
    model: Optional[str] = Field(
        None,
        description="模型名称，默认使用配置中的模型",
    )
    max_tokens: Optional[int] = Field(
        None,
        ge=1,
        le=8192,
        description="最大生成token数",
    )
    temperature: Optional[float] = Field(
        None,
        ge=0.0,
        le=2.0,
        description="温度参数，控制随机性",
    )
    stream: bool = Field(
        False,
        description="是否使用流式输出",
    )


class ChatResponse(BaseModel):
    """聊天响应"""
    content: str
    model: str
    usage: dict  # {"prompt_tokens": n, "completion_tokens": n, "total_tokens": n}


class StreamChunk(BaseModel):
    """流式响应块"""
    delta: str
    model: str
    finished: bool = False
```

## 四、DeepSeek服务封装

### 4.1 为什么用httpx而不是openai SDK？

| 对比项 | httpx | openai SDK |
|--------|-------|-----------|
| 依赖大小 | ~200KB | ~2MB |
| 流式支持 | 原生SSE | 内置streaming |
| 多API兼容 | 需自己封装 | 仅限OpenAI |
| 底层控制 | 完全可控 | 黑盒封装 |
| 超时配置 | 灵活 | 需要hack |

> **结论**：DeepSeek兼容OpenAI格式，用httpx直接调HTTP接口更轻量、更可控。如果后续要对接多种API，httpx的灵活性是关键。

### 4.2 完整服务实现

```python
"""app/services/deepseek.py - DeepSeek API服务"""
import httpx
import json
from typing import AsyncGenerator
from app.config import get_deepseek_settings
from app.models import ChatMessage, ChatResponse, StreamChunk


class DeepSeekService:
    """DeepSeek API服务封装"""

    def __init__(self):
        settings = get_deepseek_settings()
        self.api_key = settings.api_key
        self.base_url = settings.base_url.rstrip("/")
        self.default_model = settings.default_model
        self.default_max_tokens = settings.default_max_tokens
        self.default_temperature = settings.default_temperature

        # 创建持久化HTTP客户端（连接池复用）
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(60.0, connect=10.0),
        )

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> ChatResponse:
        """同步调用DeepSeek API"""
        payload = {
            "model": model or self.default_model,
            "messages": [m.model_dump() for m in messages],
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature or self.default_temperature,
        }

        response = await self.client.post("/v1/chat/completions", json=payload)

        if response.status_code != 200:
            error_detail = response.text
            raise Exception(f"DeepSeek API错误 [{response.status_code}]: {error_detail}")

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return ChatResponse(
            content=content,
            model=data["model"],
            usage=usage,
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """流式调用DeepSeek API"""
        payload = {
            "model": model or self.default_model,
            "messages": [m.model_dump() for m in messages],
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature or self.default_temperature,
            "stream": True,
        }

        async with self.client.stream(
            "POST", "/v1/chat/completions", json=payload
        ) as response:
            if response.status_code != 200:
                error_detail = await response.aread()
                raise Exception(
                    f"DeepSeek API错误 [{response.status_code}]: {error_detail.decode()}"
                )

            async for line in response.aiter_lines():
                # SSE格式：data: {...}
                if not line.startswith("data: "):
                    continue

                data_str = line[6:]  # 去掉 "data: " 前缀
                if data_str.strip() == "[DONE]":
                    yield StreamChunk(
                        delta="",
                        model=model or self.default_model,
                        finished=True,
                    )
                    break

                try:
                    data = json.loads(data_str)
                    delta = data["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    finish_reason = data["choices"][0].get("finish_reason")

                    yield StreamChunk(
                        delta=content or "",
                        model=data.get("model", self.default_model),
                        finished=finish_reason == "stop",
                    )
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


# 全局单例
_deepseek_service: DeepSeekService | None = None


async def get_deepseek_service() -> DeepSeekService:
    """获取DeepSeek服务单例"""
    global _deepseek_service
    if _deepseek_service is None:
        _deepseek_service = DeepSeekService()
    return _deepseek_service
```

## 五、FastAPI路由集成

### 5.1 聊天路由

```python
"""app/routes/chat.py - 聊天接口"""
from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from app.models import ChatRequest, ChatResponse, StreamChunk
from app.services.deepseek import get_deepseek_service, DeepSeekService
import asyncio

router = APIRouter(prefix="/api/v1", tags=["聊天"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: DeepSeekService = Depends(get_deepseek_service),
):
    """同步聊天接口"""
    response = await service.chat(
        messages=request.messages,
        model=request.model,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
    )
    return response


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    service: DeepSeekService = Depends(get_deepseek_service),
):
    """流式聊天接口（SSE）"""
    async def event_generator():
        try:
            async for chunk in service.chat_stream(
                messages=request.messages,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            ):
                yield {
                    "event": "message",
                    "data": chunk.model_dump_json(),
                }
                # 控制发送频率，避免客户端处理不过来
                if not chunk.finished:
                    await asyncio.sleep(0.01)

            yield {"event": "done", "data": ""}
        except Exception as e:
            yield {
                "event": "error",
                "data": str(e),
            }

    return EventSourceResponse(event_generator())
```

### 5.2 应用入口

```python
"""app/main.py - FastAPI应用入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import get_app_settings
from app.routes import chat
from app.services.deepseek import _deepseek_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：无需额外初始化，服务懒加载
    yield
    # 关闭时：清理HTTP连接池
    if _deepseek_service is not None:
        await _deepseek_service.close()


app = FastAPI(
    title="FastAPI + DeepSeek 智能助手",
    description="基于DeepSeek API的智能对话服务",
    version="1.0.0",
    lifespan=lifespan,
)

# 注册路由
app.include_router(chat.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    settings = get_app_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
```

### 5.3 启动服务

```bash
# 启动开发服务器
python -m app.main

# 或使用uvicorn直接启动（支持热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 `http://localhost:8000/docs` 查看Swagger文档。

## 六、多轮对话实现

### 6.1 会话管理

实际应用中需要维护对话历史。下面是一个基于内存的会话管理器：

```python
"""app/services/session.py - 会话管理"""
from collections import defaultdict
from datetime import datetime
from app.models import ChatMessage, MessageRole
import asyncio


class SessionManager:
    """会话管理器（内存存储）"""

    def __init__(self, max_history: int = 20, max_sessions: int = 1000):
        self._sessions: dict[str, list[ChatMessage]] = defaultdict(list)
        self._max_history = max_history  # 每个会话最大消息数
        self._max_sessions = max_sessions
        self._lock = asyncio.Lock()

    async def add_message(self, session_id: str, role: MessageRole, content: str):
        """添加消息到会话"""
        async with self._lock:
            if len(self._sessions) >= self._max_sessions:
                # LRU淘汰：删除最早的会话
                oldest_key = next(iter(self._sessions))
                del self._sessions[oldest_key]

            self._sessions[session_id].append(
                ChatMessage(role=role, content=content)
            )

            # 超过最大历史长度，保留system + 最近的消息
            if len(self._sessions[session_id]) > self._max_history:
                messages = self._sessions[session_id]
                system_msgs = [m for m in messages if m.role == MessageRole.SYSTEM]
                other_msgs = messages[-(self._max_history - len(system_msgs)):]
                self._sessions[session_id] = system_msgs + other_msgs

    async def get_messages(self, session_id: str) -> list[ChatMessage]:
        """获取会话历史"""
        return self._sessions.get(session_id, [])

    async def clear_session(self, session_id: str):
        """清空会话"""
        self._sessions.pop(session_id, None)


# 全局单例
session_manager = SessionManager()
```

### 6.2 带会话的聊天接口

```python
"""app/routes/chat.py - 新增带会话的接口"""
from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
from app.models import ChatRequest, ChatResponse, ChatMessage, MessageRole
from app.services.deepseek import get_deepseek_service, DeepSeekService
from app.services.session import session_manager
import asyncio, uuid

router = APIRouter(prefix="/api/v1", tags=["聊天"])


@router.post("/chat")
async def chat(
    request: ChatRequest,
    service: DeepSeekService = Depends(get_deepseek_service),
):
    """同步聊天（无状态）"""
    response = await service.chat(
        messages=request.messages,
        model=request.model,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
    )
    return response


class SessionChatRequest(BaseModel):
    """带会话的聊天请求"""
    session_id: str | None = None  # 为空则创建新会话
    content: str
    model: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None


class SessionChatResponse(BaseModel):
    """带会话的聊天响应"""
    session_id: str
    content: str
    model: str
    usage: dict


@router.post("/chat/session", response_model=SessionChatResponse)
async def chat_with_session(
    request: SessionChatRequest,
    service: DeepSeekService = Depends(get_deepseek_service),
):
    """带会话管理的聊天接口"""
    session_id = request.session_id or str(uuid.uuid4())

    # 添加用户消息
    await session_manager.add_message(session_id, MessageRole.USER, request.content)

    # 获取完整历史
    messages = await session_manager.get_messages(session_id)

    # 调用DeepSeek
    response = await service.chat(
        messages=messages,
        model=request.model,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
    )

    # 保存助手回复
    await session_manager.add_message(
        session_id, MessageRole.ASSISTANT, response.content
    )

    return SessionChatResponse(
        session_id=session_id,
        content=response.content,
        model=response.model,
        usage=response.usage,
    )
```

## 七、系统提示词设计

系统提示词是控制AI行为的核心手段。不同的系统提示词设计对输出质量影响巨大。

```python
"""app/prompts.py - 系统提示词模板"""
from enum import Enum


class SystemPrompt(str, Enum):
    """预定义系统提示词"""

    GENERAL_ASSISTANT = """你是一个有用的AI助手。请用简洁、准确的中文回答问题。
规则：
1. 如果不确定，直接说不知道，不要编造
2. 技术问题优先给出代码示例
3. 回答长度控制在500字以内，除非用户要求详细说明"""

    CODE_ASSISTANT = """你是一个高级编程助手，精通Python、JavaScript、Go等主流语言。
规则：
1. 代码必须完整可运行，不要省略
2. 优先使用类型注解
3. 关键代码添加注释
4. 给出多种实现方案并对比优劣
5. 提及时间/空间复杂度"""

    TRANSLATOR = """你是一个专业翻译，中英文互译。
规则：
1. 保持原文的语气和风格
2. 技术术语保留英文原文
3. 翻译自然流畅，不要直译"""


def build_system_prompt(
    base_prompt: str,
    context: str | None = None,
    constraints: list[str] | None = None,
) -> str:
    """构建系统提示词"""
    parts = [base_prompt]

    if context:
        parts.append(f"\n\n## 背景信息\n{context}")

    if constraints:
        constraint_text = "\n".join(f"- {c}" for c in constraints)
        parts.append(f"\n\n## 额外约束\n{constraint_text}")

    return "".join(parts)
```

使用示例：

```python
from app.prompts import SystemPrompt, build_system_prompt

# 基础提示词
system_msg = ChatMessage(role=MessageRole.SYSTEM, content=SystemPrompt.CODE_ASSISTANT.value)

# 自定义提示词
custom_prompt = build_system_prompt(
    base_prompt=SystemPrompt.GENERAL_ASSISTANT.value,
    context="你正在帮助一个Python后端开发者调试FastAPI应用。",
    constraints=["回答不超过300字", "优先使用async/await"],
)
```

## 八、价格优化策略

### 8.1 DeepSeek缓存命中

DeepSeek API支持前缀缓存（prefix caching）。当连续请求的system prompt相同时，API会自动缓存，被缓存部分的token按0.1倍计费。

```python
"""app/services/deepseek.py - 添加缓存优化提示"""
class DeepSeekService:
    async def chat_with_cache_hint(self, messages: list[ChatMessage], **kwargs) -> ChatResponse:
        """带缓存优化的调用"""
        payload = {
            "model": kwargs.get("model") or self.default_model,
            "messages": [m.model_dump() for m in messages],
            "max_tokens": kwargs.get("max_tokens") or self.default_max_tokens,
            "temperature": kwargs.get("temperature") or self.default_temperature,
        }

        # 关键：确保system prompt始终在第一条，且完全一致
        # 这样DeepSeek可以命中前缀缓存
        response = await self.client.post("/v1/chat/completions", json=payload)

        if response.status_code != 200:
            raise Exception(f"API错误: {response.text}")

        data = response.json()
        usage = data.get("usage", {})

        # 检查缓存命中情况
        cached_tokens = usage.get("prompt_cache_hit_tokens", 0)
        if cached_tokens > 0:
            print(f"缓存命中 {cached_tokens} tokens，节省 {(cached_tokens / usage['prompt_tokens']):.0%}")

        return ChatResponse(
            content=data["choices"][0]["message"]["content"],
            model=data["model"],
            usage=usage,
        )
```

### 8.2 模型降级策略

简单问题用便宜的模型，复杂问题用贵的模型：

```python
"""app/services/model_selector.py - 模型选择器"""
from app.models import ChatMessage, MessageRole


class ModelSelector:
    """根据问题复杂度自动选择模型"""

    # 复杂度关键词
    COMPLEX_KEYWORDS = [
        "架构设计", "系统设计", "性能优化", "分布式",
        "算法", "递归", "动态规划", "机器学习",
        "详细分析", "对比分析", "深入解析",
        "refactor", "design pattern", "architecture",
    ]

    def select_model(self, messages: list[ChatMessage]) -> str:
        """选择合适的模型"""
        # 获取最后一条用户消息
        user_msg = next(
            (m for m in reversed(messages) if m.role == MessageRole.USER),
            None,
        )
        if not user_msg:
            return "deepseek-chat"  # 默认V3

        # 检查消息长度
        if len(user_msg.content) > 1000:
            return "deepseek-reasoner"  # 长问题用R1

        # 检查复杂度关键词
        for keyword in self.COMPLEX_KEYWORDS:
            if keyword.lower() in user_msg.content.lower():
                return "deepseek-reasoner"

        # 简单问题用mini模型
        if len(user_msg.content) < 50:
            return "deepseek-chat"

        return "deepseek-chat"
```

## 九、前端调用示例

流式输出的前端调用：

```javascript
// 前端流式调用示例
async function streamChat(messages) {
    const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages, stream: true }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();  // 保留不完整的行

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const chunk = JSON.parse(line.slice(6));
                    if (chunk.delta) {
                        process.stdout.write(chunk.delta);  // 逐字输出
                    }
                } catch (e) {
                    // 忽略解析错误
                }
            }
        }
    }
}
```

## 十、踩坑记录

### 坑1：SSE流式输出断连

**现象**：流式输出中途断开，前端收到`EventSource`的error事件。

**原因**：Nginx默认有`proxy_buffering on`，会缓冲SSE响应。60秒没有新数据时Nginx主动断开连接。

**解决**：

```nginx
# Nginx配置
location /api/v1/chat/stream {
    proxy_pass http://backend;
    proxy_buffering off;           # 关闭缓冲
    proxy_cache off;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding off;  # 关闭分块传输编码
    proxy_read_timeout 300s;        # 延长超时
}
```

### 坑2：httpx连接池耗尽

**现象**：高并发时出现`Connection pool is full`错误。

**原因**：默认httpx连接池大小（`max_connections=100`）不够用。

**解决**：

```python
self.client = httpx.AsyncClient(
    base_url=self.base_url,
    headers={
        "Authorization": f"Bearer {self.api_key}",
    },
    timeout=httpx.Timeout(60.0, connect=10.0),
    limits=httpx.Limits(
        max_connections=200,       # 增大连接池
        max_keepalive_connections=50,
        keepalive_expiry=30,       # 30秒空闲后关闭
    ),
)
```

### 坑3：中文编码问题

**现象**：流式输出时中文出现乱码，尤其是多字节字符在chunk边界被截断。

**原因**：UTF-8中文是3字节，SSE按行切分时可能从中间截断。

**解决**：使用`aiter_lines()`而不是`aiter_bytes()`，httpx会自动处理行边界。如果用`aiter_bytes()`，需要在应用层处理编码：

```python
# 错误做法
async for chunk in response.aiter_bytes():
    text = chunk.decode("utf-8")  # 可能截断多字节字符

# 正确做法
async for line in response.aiter_lines():  # 自动按行分割
    if line.startswith("data: "):
        data = json.loads(line[6:])
```

### 坑4：DeepSeek API返回429

**现象**：调用频率高时返回429 Too Many Requests。

**原因**：DeepSeek对免费用户和付费用户的限流策略不同。Tier 1账号限制为3 RPM（Requests Per Minute），Tier 2为10 RPM。

**解决**：

1. 升级账号等级（充值后自动升级）
2. 在应用层做请求队列和重试：

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry_error_callback=lambda x: None,  # 重试耗尽后返回None
)
async def chat_with_retry(self, messages, **kwargs):
    response = await self.client.post("/v1/chat/completions", json=payload)
    response.raise_for_status()
    return response.json()
```

## 十一、总结

本文从零搭建了一个完整的FastAPI + DeepSeek智能助手服务，涵盖了：

1. **API调用**：使用httpx封装同步和流式两种调用方式
2. **会话管理**：内存级别的多轮对话支持
3. **系统提示词**：可复用的提示词模板设计
4. **价格优化**：利用前缀缓存和模型降级降低成本
5. **生产实战**：解决了SSE断连、连接池耗尽、中文编码等真实问题

**下一步**：第六篇将在这个基础上接入LangChain，构建RAG知识库，让AI能基于私有文档回答问题。

---

> **完整代码仓库**：`https://github.com/your-repo/fastapi-ai-column/tree/main/05-deepseek-assistant`
