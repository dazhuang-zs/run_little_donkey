# MCP 实战指南：从本地 AI 工具到 Web 项目的完整接入方案

> **阅读时间**：约35分钟 | **你将学到**：MCP 的真实调用原理、3种本地接入方式、2种 Web 接入架构、完整可运行代码
>
> **核心观点**：MCP 不只是一个协议规范，它是一套"工具发现 + 工具调用 + 结果返回"的完整通信机制。本地用 stdio，Web 用 HTTP/SSE，原理相同，传输方式不同。

---

## 一、MCP 到底是什么（3分钟真正搞懂）

### 1.1 一句话说清楚

MCP（Model Context Protocol）= AI 应用调用外部工具的标准协议。

就像 USB 是硬件接口标准，MCP 是 AI 调用工具的接口标准。

```
没有 MCP 的世界：                    有 MCP 的世界：
┌──────────┐                        ┌──────────┐
│ AI 应用   │                        │ AI 应用   │
│          │                        │          │
│ 调GitHub → 写一套适配代码          │ 统一调用   │────→ MCP Server A（GitHub）
│ 调数据库 → 又写一套适配代码        │ MCP 协议   │────→ MCP Server B（数据库）
│ 调搜索引擎 → 再写一套适配代码      │          │────→ MCP Server C（搜索）
└──────────┘                        └──────────┘

每个工具一套接口，维护成本爆炸        一套协议，所有工具通用
```

### 1.2 MCP 的三个核心能力

| 能力 | 说明 | 类比 |
|------|------|------|
| **Tools** | AI 可以调用的函数 | 你给AI的"工具箱" |
| **Resources** | AI 可以读取的数据 | 你给AI的"资料库" |
| **Prompts** | 预设的提示词模板 | 你给AI的"话术本" |

实际项目中最常用的是 **Tools**（占 95% 的使用场景）。

### 1.3 通信协议：JSON-RPC 2.0

MCP 用 JSON-RPC 2.0 通信。就两种消息：

```json
// 请求（AI 应用 → MCP Server）
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_github",
    "arguments": {"query": "mcp server"}
  }
}

// 响应（MCP Server → AI 应用）
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {"type": "text", "text": "找到 1234 个仓库..."}
    ]
  }
}
```

就这么简单。请求带着方法名和参数，响应带着结果。

---

## 二、本地 AI 工具中使用 MCP

### 2.1 本地 MCP 的通信方式：stdio

本地 AI 工具（OpenClaw、Claude Desktop、Claude Code）用的是 **stdio**（标准输入输出）通信。

```
┌─────────────────────┐     stdin/stdout     ┌─────────────────────┐
│   AI 应用进程        │ ←──────────────────→ │   MCP Server 进程    │
│   (Claude Desktop)  │     JSON-RPC 2.0     │   (子进程)           │
└─────────────────────┘                      └─────────────────────┘
        │                                            │
        │ 不需要网络                                  │ 调用实际资源
        │ 同一台机器                                  │
        ▼                                            ▼
   用户交互                                    文件系统/数据库/API
```

**关键点**：MCP Server 是 AI 应用拉起来的子进程，通过管道（pipe）通信，不需要网络。

### 2.2 实战一：Claude Desktop 接入 MCP Server

**第 1 步**：安装 MCP Server

```bash
# 安装文件系统 MCP Server
npm install -g @modelcontextprotocol/server-filesystem

# 安装 GitHub MCP Server
npm install -g @modelcontextprotocol/server-github

# 安装 SQLite MCP Server
npm install -g @modelcontextprotocol/server-sqlite
```

**第 2 步**：配置 Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）或 `%APPDATA%\Claude\claude_desktop_config.json`（Windows）：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/xiaoyuer/projects",
        "/Users/xiaoyuer/Documents"
      ]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here"
      }
    },
    "sqlite": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sqlite",
        "/path/to/your/database.db"
      ]
    }
  }
}
```

**第 3 步**：重启 Claude Desktop，开始使用

重启后，Claude 会自动拉起配置中的 MCP Server 进程。你可以在对话中直接说：

- "读一下 /Users/xiaoyuer/projects/main.py"
- "搜索 GitHub 上 star 最多的 MCP 项目"
- "查一下数据库里最近的订单"

Claude 会自动调用对应的 MCP Server。

### 2.3 实战二：OpenClaw 接入 MCP Server

OpenClaw 的 MCP 配置在 `~/.openclaw/config.yaml` 中：

```yaml
# ~/.openclaw/config.yaml
mcp:
  servers:
    # 文件系统 MCP Server
    filesystem:
      command: npx
      args:
        - "-y"
        - "@modelcontextprotocol/server-filesystem"
        - "/Users/xiaoyuer/projects"
    
    # 自定义 MCP Server（Python 写的）
    my-tools:
      command: python
      args:
        - "/Users/xiaoyuer/mcp-servers/my_tools_server.py"
    
    # 远程 MCP Server（HTTP/SSE）
    remote-search:
      url: "https://mcp.example.com/sse"
```

**OpenClaw 的特殊能力**：同时支持 stdio 和 HTTP/SSE 两种方式连接 MCP Server。

### 2.4 实战三：Claude Code 接入 MCP Server

Claude Code 通过命令行配置：

```bash
# 添加 MCP Server
claude mcp add filesystem npx -y @modelcontextprotocol/server-filesystem /Users/xiaoyuer/projects

# 添加带环境变量的 MCP Server
claude mcp add github -e GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx -- npx -y @modelcontextprotocol/server-github

# 查看已配置的 MCP Server
claude mcp list

# 删除 MCP Server
claude mcp remove filesystem
```

### 2.5 自己写一个 MCP Server（Python）

这是最重要的实战能力。项目里经常需要自定义工具。

```python
"""
自定义 MCP Server - 项目管理工具
功能：查询项目状态、搜索代码、管理任务
"""

import json
import sys
import asyncio
from typing import Any

# 安装依赖：pip install mcp


from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)


# 创建 Server 实例
app = Server("project-manager")


# ===== 1. 注册工具列表 =====

@app.list_tools()
async def list_tools() -> list[Tool]:
    """告诉 AI 应用：我提供哪些工具"""
    
    return [
        Tool(
            name="get_project_status",
            description="获取项目状态，包括进度、待办事项、最近变更",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "项目名称"
                    }
                },
                "required": ["project_name"]
            }
        ),
        Tool(
            name="search_code",
            description="在项目代码中搜索关键词",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "项目名称"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "file_type": {
                        "type": "string",
                        "description": "文件类型过滤，如 py/js/ts",
                        "default": None
                    }
                },
                "required": ["project_name", "keyword"]
            }
        ),
        Tool(
            name="create_task",
            description="创建项目管理任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "项目名称"
                    },
                    "title": {
                        "type": "string",
                        "description": "任务标题"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "优先级",
                        "default": "medium"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "负责人",
                        "default": None
                    }
                },
                "required": ["project_name", "title"]
            }
        ),
    ]


# ===== 2. 实现工具逻辑 =====

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent | ImageContent | EmbeddedResource]:
    """执行工具调用"""
    
    if name == "get_project_status":
        return await handle_get_project_status(arguments)
    elif name == "search_code":
        return await handle_search_code(arguments)
    elif name == "create_task":
        return await handle_create_task(arguments)
    else:
        return [TextContent(type="text", text=f"未知工具：{name}")]


async def handle_get_project_status(args: dict) -> list[TextContent]:
    """获取项目状态"""
    
    project_name = args["project_name"]
    
    # 这里替换成你的实际逻辑
    # 比如：查数据库、调API、读文件等
    status = {
        "project": project_name,
        "progress": "68%",
        "open_issues": 12,
        "recent_commits": [
            {"hash": "a1b2c3d", "message": "feat: 添加用户认证", "author": "zhangsan"},
            {"hash": "e4f5g6h", "message": "fix: 修复分页bug", "author": "lisi"},
        ],
        "pending_tasks": [
            {"title": "接口压测", "priority": "high"},
            {"title": "文档更新", "priority": "medium"},
        ]
    }
    
    return [TextContent(
        type="text",
        text=json.dumps(status, ensure_ascii=False, indent=2)
    )]


async def handle_search_code(args: dict) -> list[TextContent]:
    """搜索代码"""
    
    project_name = args["project_name"]
    keyword = args["keyword"]
    file_type = args.get("file_type")
    
    # 这里替换成你的实际逻辑
    # 比如：用 grep/ripgrep 搜索、调 GitHub API 等
    results = [
        {
            "file": f"src/api/{project_name}/routes.py",
            "line": 42,
            "content": f"def search_{keyword}(query: str):"
        },
        {
            "file": f"src/services/{project_name}/service.py",
            "line": 88,
            "content": f"class {keyword.capitalize()}Service:"
        },
    ]
    
    return [TextContent(
        type="text",
        text=json.dumps(results, ensure_ascii=False, indent=2)
    )]


async def handle_create_task(args: dict) -> list[TextContent]:
    """创建任务"""
    
    project_name = args["project_name"]
    title = args["title"]
    priority = args.get("priority", "medium")
    assignee = args.get("assignee")
    
    # 这里替换成你的实际逻辑
    # 比如：调 Jira API、写数据库等
    task = {
        "id": "TASK-2026-001",
        "project": project_name,
        "title": title,
        "priority": priority,
        "assignee": assignee or "未分配",
        "status": "created"
    }
    
    return [TextContent(
        type="text",
        text=json.dumps(task, ensure_ascii=False, indent=2)
    )]


# ===== 3. 启动 Server =====

async def main():
    """启动 MCP Server（stdio 模式）"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
```

**配置到 Claude Desktop**：

```json
{
  "mcpServers": {
    "project-manager": {
      "command": "python",
      "args": ["/Users/xiaoyuer/mcp-servers/my_tools_server.py"]
    }
  }
}
```

重启 Claude Desktop 后，你就能直接说"查一下 smart-trip-planner 项目状态"或"在项目里搜一下 auth 相关代码"，Claude 会自动调用你的 MCP Server。

---

## 三、Web 项目中使用 MCP

### 3.1 Web 项目和本地 AI 工具的核心区别

```
本地 AI 工具（Claude Desktop / OpenClaw）：
┌─────────────────┐  stdio（管道）  ┌─────────────────┐
│  AI 应用进程      │ ←────────────→ │  MCP Server 进程 │
│  同一台机器       │                 │  同一台机器       │
└─────────────────┘                  └─────────────────┘
  特点：不需要网络，进程间直接通信


Web 项目：
┌─────────────────┐  HTTP/SSE（网络）  ┌─────────────────┐
│  Web 后端        │ ←───────────────→ │  MCP Server 服务 │
│  任意机器        │                    │  可能是另一台机器  │
└─────────────────┘                    └─────────────────┘
  特点：需要网络，跨机器通信，需要考虑认证、超时、负载均衡
```

**核心区别**：

| 维度 | 本地 AI 工具 | Web 项目 |
|------|-------------|----------|
| 通信方式 | stdio（管道） | HTTP/SSE（网络） |
| MCP Server 生命周期 | 随 AI 应用启动/关闭 | 独立部署，长期运行 |
| 认证 | 不需要 | 需要考虑（API Key / OAuth） |
| 并发 | 单用户 | 多用户并发 |
| 部署 | 本地进程 | 云服务器 / Docker |
| 延迟 | 极低（进程间） | 较高（网络传输） |

### 3.2 Web 项目的两种 MCP 架构

#### 架构一：Web 后端 = MCP Client（调用外部 MCP Server）

```
┌──────────────┐     ┌──────────────────┐     HTTP/SSE     ┌──────────────────┐
│   前端        │ ──→ │  Web 后端         │ ──────────────→ │  MCP Server      │
│   (React/Vue) │     │  (FastAPI/Next)   │ ←────────────── │  (远程服务)       │
└──────────────┘     │                  │                  │                  │
                     │  MCP Client 逻辑  │                  │  工具实现          │
                     └──────────────────┘                  └──────────────────┘
```

适用场景：你的 Web 项目需要调用现成的 MCP Server 提供的工具。

#### 架构二：Web 后端 = MCP Server（给 AI 应用提供工具）

```
┌──────────────────┐     HTTP/SSE     ┌──────────────────┐     ┌──────────────┐
│  AI 应用          │ ──────────────→ │  Web 后端         │ ──→ │   数据库/API   │
│  (Claude/OpenClaw)│ ←────────────── │  (FastAPI/Next)   │ ←── │              │
│                  │                  │  MCP Server 逻辑   │     └──────────────┘
└──────────────────┘                  └──────────────────┘
```

适用场景：你想让 AI 应用直接调用你 Web 项目的功能。

### 3.3 实战：Web 后端作为 MCP Client

```python
"""
Web 后端 - MCP Client
FastAPI 项目调用远程 MCP Server 的工具
"""

import httpx
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional


app = FastAPI(title="MCP Client Demo")


class MCPClient:
    """MCP 客户端（HTTP 模式）"""
    
    def __init__(self, server_url: str, api_key: Optional[str] = None):
        self.server_url = server_url.rstrip("/")
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        self._request_id = 0
        self._client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers=self.headers,
            )
        return self._client
    
    async def _send_request(self, method: str, params: dict = None) -> dict:
        """发送 JSON-RPC 请求"""
        
        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
        }
        if params:
            payload["params"] = params
        
        client = await self._get_client()
        response = await client.post(
            f"{self.server_url}/mcp",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            raise Exception(f"MCP Error: {data['error']}")
        
        return data.get("result", {})
    
    async def initialize(self) -> dict:
        """初始化连接"""
        return await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "web-backend",
                "version": "1.0.0"
            }
        })
    
    async def list_tools(self) -> list:
        """获取工具列表"""
        result = await self._send_request("tools/list")
        return result.get("tools", [])
    
    async def call_tool(self, name: str, arguments: dict) -> dict:
        """调用工具"""
        return await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
    
    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# 全局 MCP Client 实例
mcp_client = MCPClient(
    server_url="https://mcp.example.com",
    api_key="your-api-key"  # 生产环境从环境变量读取
)


@app.on_event("startup")
async def startup():
    """启动时初始化 MCP 连接"""
    await mcp_client.initialize()
    tools = await mcp_client.list_tools()
    print(f"已连接 MCP Server，可用工具：{[t['name'] for t in tools]}")


@app.on_event("shutdown")
async def shutdown():
    """关闭时断开连接"""
    await mcp_client.close()


# ===== 业务接口 =====

class SearchRequest(BaseModel):
    query: str
    project: Optional[str] = None

class TaskRequest(BaseModel):
    project_name: str
    title: str
    priority: str = "medium"


@app.post("/api/search")
async def search(req: SearchRequest):
    """搜索接口 - 调用 MCP Server 的搜索工具"""
    
    result = await mcp_client.call_tool("search_code", {
        "project_name": req.project or "default",
        "keyword": req.query,
    })
    
    return {"data": result}


@app.post("/api/tasks")
async def create_task(req: TaskRequest):
    """创建任务接口 - 调用 MCP Server 的任务工具"""
    
    result = await mcp_client.call_tool("create_task", {
        "project_name": req.project_name,
        "title": req.title,
        "priority": req.priority,
    })
    
    return {"data": result}


@app.get("/api/tools")
async def get_available_tools():
    """查看当前可用的 MCP 工具"""
    
    tools = await mcp_client.list_tools()
    return {"tools": tools}


# 运行：uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3.4 实战：Web 后端作为 MCP Server

```python
"""
Web 后端 - MCP Server
把 Web 项目的功能暴露为 MCP 工具，给 AI 应用调用
"""

import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Any


app = FastAPI(title="MCP Server Demo")


# ===== 你的业务逻辑 =====

class BusinessLogic:
    """业务逻辑层（和 MCP 无关）"""
    
    @staticmethod
    async def query_orders(user_id: str, status: str = None) -> list:
        """查询订单"""
        # 实际项目中：查数据库
        return [
            {"id": "ORD-001", "user": user_id, "amount": 299.0, "status": "paid"},
            {"id": "ORD-002", "user": user_id, "amount": 158.0, "status": "pending"},
        ]
    
    @staticmethod
    async def get_user_info(user_id: str) -> dict:
        """查询用户信息"""
        # 实际项目中：查数据库
        return {
            "id": user_id,
            "name": "张三",
            "level": "VIP",
            "orders_count": 42,
        }
    
    @staticmethod
    async def cancel_order(order_id: str, reason: str) -> dict:
        """取消订单"""
        # 实际项目中：写数据库
        return {
            "order_id": order_id,
            "status": "cancelled",
            "reason": reason,
            "refund_amount": 299.0,
        }


biz = BusinessLogic()


# ===== MCP 协议层 =====

def mcp_response(req_id: int, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}

def mcp_error(req_id: int, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


# 工具注册表
TOOLS = [
    {
        "name": "query_orders",
        "description": "查询用户订单",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "用户ID"},
                "status": {"type": "string", "description": "订单状态过滤", "default": None}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "get_user_info",
        "description": "查询用户信息",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "用户ID"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "cancel_order",
        "description": "取消订单（危险操作，需要确认）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "订单ID"},
                "reason": {"type": "string", "description": "取消原因"}
            },
            "required": ["order_id", "reason"]
        }
    }
]

# 工具处理函数映射
TOOL_HANDLERS = {
    "query_orders": lambda args: biz.query_orders(args["user_id"], args.get("status")),
    "get_user_info": lambda args: biz.get_user_info(args["user_id"]),
    "cancel_order": lambda args: biz.cancel_order(args["order_id"], args["reason"]),
}


@app.post("/mcp")
async def handle_mcp(request: Request):
    """处理 MCP 请求"""
    
    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})
    req_id = body.get("id")
    
    # 1. 初始化握手
    if method == "initialize":
        return mcp_response(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "order-management-mcp",
                "version": "1.0.0"
            }
        })
    
    # 2. 初始化确认
    if method == "notifications/initialized":
        return JSONResponse(content={})
    
    # 3. 工具列表
    if method == "tools/list":
        return mcp_response(req_id, {"tools": TOOLS})
    
    # 4. 工具调用
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            return mcp_error(req_id, -32601, f"未知工具：{tool_name}")
        
        try:
            result = await handler(arguments)
            return mcp_response(req_id, {
                "content": [
                    {"type": "text", "text": json.dumps(result, ensure_ascii=False)}
                ]
            })
        except Exception as e:
            return mcp_error(req_id, -32603, f"工具执行失败：{str(e)}")
    
    return mcp_error(req_id, -32601, f"未知方法：{method}")


# ===== 健康检查 =====

@app.get("/health")
async def health():
    return {"status": "ok", "tools_count": len(TOOLS)}


# 运行：uvicorn main:app --host 0.0.0.0 --port 8080
```

**Claude Desktop 配置远程 MCP Server**：

```json
{
  "mcpServers": {
    "order-management": {
      "url": "https://your-api.com/mcp"
    }
  }
}
```

这样 Claude Desktop 就能直接查询订单、取消订单了。

---

## 四、原理对比：本地 vs Web

### 4.1 通信方式对比

```
本地模式（stdio）：

  AI 应用进程                    MCP Server 进程
  ┌──────────┐   stdin（写）    ┌──────────┐
  │          │ ──────────────→ │          │
  │  stdout  │ ←────────────── │  stdout  │
  │  （读）   │   stdout（写）   │  （输出）  │
  └──────────┘                  └──────────┘
  
  数据流：AI 应用 → pipe → MCP Server → pipe → AI 应用
  特点：操作系统级管道，零网络延迟，进程同生命周期


Web 模式（HTTP/SSE）：

  Web 后端                        MCP Server
  ┌──────────┐   HTTP POST       ┌──────────┐
  │          │ ──────────────→ │          │
  │          │ ←────────────── │          │
  │          │   HTTP Response  │          │
  └──────────┘                  └──────────┘
  
  数据流：Web 后端 → 网络请求 → MCP Server → 网络响应 → Web 后端
  特点：需要网络，独立部署，需要认证，可跨机器
```

### 4.2 生命周期对比

```python
"""
本地模式的 MCP Server 生命周期
"""

# 1. AI 应用启动时，自动拉起 MCP Server
import subprocess

mcp_process = subprocess.Popen(
    ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    stdin=subprocess.PIPE,   # AI 应用写请求
    stdout=subprocess.PIPE,  # AI 应用读响应
    stderr=subprocess.PIPE,
)

# 2. 通过管道通信
request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
mcp_process.stdin.write(f"{request}\n".encode())
mcp_process.stdin.flush()

response = mcp_process.stdout.readline().decode()
print(json.loads(response))

# 3. AI 应用关闭时，MCP Server 也关闭
mcp_process.terminate()


"""
Web 模式的 MCP Server 生命周期
"""

# 1. MCP Server 独立部署，长期运行
# uvicorn mcp_server:app --host 0.0.0.0 --port 8080

# 2. Web 后端按需连接
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post("http://mcp-server:8080/mcp", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    })
    print(response.json())

# 3. Web 后端关闭不影响 MCP Server
# MCP Server 独立运行，可以被多个 Web 后端调用
```

### 4.3 完整对比表

| 维度 | 本地模式（stdio） | Web 模式（HTTP/SSE） |
|------|-------------------|---------------------|
| **通信** | 操作系统管道 | HTTP 网络请求 |
| **延迟** | 微秒级 | 毫秒~秒级 |
| **认证** | 不需要 | API Key / OAuth |
| **并发** | 单用户 | 多用户 |
| **部署** | 随 AI 应用启停 | 独立部署，长期运行 |
| **发现** | 配置文件声明 | URL + 自动发现 |
| **适用** | 个人工具 | 团队/生产环境 |
| **错误处理** | 进程崩溃 = 通信断 | 需要重试/超时/熔断 |
| **监控** | 日志文件 | APM + 健康检查 |
| **多实例** | 不支持 | 负载均衡 |

---

## 五、SSE 模式深入

SSE（Server-Sent Events）是 MCP 的流式通信模式，适合长时间运行的工具。

### 5.1 为什么需要 SSE

```
普通 HTTP：请求 → 等待 → 一次性返回
  问题：工具执行要 30 秒 → HTTP 超时

SSE：请求 → 持续推送进度 → 最终返回结果
  优势：不会超时，用户能看到进度
```

### 5.2 SSE MCP Server 实现

```python
"""
SSE 模式的 MCP Server
适合：执行时间长的工具（数据分析、批量处理）
"""

import json
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse


app = FastAPI()


@app.get("/sse")
async def sse_endpoint():
    """SSE 端点"""
    
    async def event_stream():
        # 1. 发送初始化信息
        yield f"data: {json.dumps({'type': 'endpoint', 'endpoint': '/mcp'})}\n\n"
        
        # 保持连接
        while True:
            await asyncio.sleep(30)
            yield f": keepalive\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/mcp")
async def handle_mcp_sse(request):
    """处理 MCP 请求（支持流式响应）"""
    
    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})
    
    if method == "tools/call":
        tool_name = params.get("name")
        
        if tool_name == "long_running_analysis":
            # 流式返回进度
            async def stream_result():
                for i in range(5):
                    progress = {
                        "type": "progress",
                        "message": f"分析中... {i+1}/5",
                        "percentage": (i + 1) * 20
                    }
                    yield f"data: {json.dumps(progress)}\n\n"
                    await asyncio.sleep(2)
                
                final = {
                    "type": "result",
                    "content": [{"type": "text", "text": "分析完成：共发现 3 个异常模式"}]
                }
                yield f"data: {json.dumps(final)}\n\n"
            
            return StreamingResponse(
                stream_result(),
                media_type="text/event-stream"
            )
```

---

## 六、生产环境部署

### 6.1 Docker 部署 MCP Server

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s \
  CMD curl -f http://localhost:8080/health || exit 1

# 启动
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  mcp-server:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - API_KEY=${MCP_API_KEY}
    depends_on:
      - db
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

### 6.2 认证中间件

```python
"""
MCP Server 认证中间件
生产环境必须加，否则任何人都能调用你的工具
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
import os
import time
import hashlib
import hmac


API_KEY = os.environ.get("MCP_API_KEY", "")
ALLOWED_ORIGINS = os.environ.get("MCP_ALLOWED_ORIGINS", "*").split(",")


# API Key 认证
async def verify_api_key(request: Request, call_next):
    path = request.url.path
    
    # 健康检查不需要认证
    if path == "/health":
        return await call_next(request)
    
    # 检查 API Key
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing API Key")
    
    key = auth_header.replace("Bearer ", "")
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    return await call_next(request)


# 速率限制（简单版）
request_counts = {}

async def rate_limit(request: Request, call_next):
    client_ip = request.client.host
    now = int(time.time() / 60)  # 按分钟计数
    
    key = f"{client_ip}:{now}"
    request_counts[key] = request_counts.get(key, 0) + 1
    
    if request_counts[key] > 60:  # 每分钟最多 60 次
        raise HTTPException(status_code=429, detail="Too many requests")
    
    # 清理旧记录
    old_keys = [k for k in request_counts if int(k.split(":")[1]) < now - 5]
    for k in old_keys:
        del request_counts[k]
    
    return await call_next(request)


# 创建带中间件的 App
app = FastAPI(
    middleware=[
        Middleware(verify_api_key),
        Middleware(rate_limit),
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

---

## 七、踩坑记录

| 坑 | 症状 | 解决方法 |
|------|------|----------|
| stdio 模式卡死 | MCP Server 不响应 | 检查 stdout 是否被缓冲，加 `sys.stdout.flush()` |
| HTTP 超时 | 长时间工具执行失败 | 用 SSE 模式，或加大超时时间 |
| 工具列表为空 | AI 应用看不到工具 | 检查 `list_tools()` 返回格式是否正确 |
| 编码问题 | 中文返回乱码 | 确保 UTF-8 编码，JSON 加 `ensure_ascii=False` |
| 认证失败 | API Key 传了但还是 401 | 检查 Bearer 前缀、环境变量是否生效 |
| 并发冲突 | 多用户同时调用同一工具 | 加锁或用队列，注意共享状态 |
| MCP Server 崩溃 | AI 应用报错"连接断开" | 加进程守护（systemd / supervisor），本地模式加自动重启 |
| JSON-RPC id 不一致 | 请求和响应对不上 | 严格用递增 id，不要随机生成 |

---

## 八、决策树：什么时候用什么模式

```
你要做什么？
│
├── 个人用，本地 AI 工具（Claude Desktop / OpenClaw）
│   └── 用 stdio 模式
│       ├── 现成的 MCP Server → npm install + 配置
│       └── 自定义工具 → Python/TS 写 Server + 配置
│
├── Web 项目调用外部 MCP Server 的工具
│   └── 用 HTTP 模式（Client）
│       ├── 工具执行快（<5s）→ 普通 HTTP POST
│       └── 工具执行慢（>5s）→ SSE 流式
│
├── 把 Web 项目的功能暴露给 AI 应用
│   └── 用 HTTP 模式（Server）
│       ├── 内网使用 → 简单 API Key 认证
│       └── 公网使用 → API Key + 速率限制 + HTTPS
│
└── 既要本地用又要 Web 用
    └── 写一个 MCP Server，同时支持 stdio 和 HTTP
        ├── stdio 入口：if __name__ == "__main__": stdio_server()
        └── HTTP 入口：uvicorn + FastAPI 路由
```

---

## 总结

1. **MCP 本质是 JSON-RPC 2.0 协议**，不管本地还是 Web，通信内容一样
2. **本地用 stdio**，AI 应用自动拉起 MCP Server 进程，零网络延迟
3. **Web 用 HTTP/SSE**，MCP Server 独立部署，需要认证和监控
4. **90% 的场景用现成的 MCP Server 就够了**，自定义 Server 只在需要时写
5. **生产环境必须加认证**，API Key 是最低要求
6. **长耗时工具用 SSE**，避免 HTTP 超时

MCP 的设计很克制，只解决"AI 怎么调用工具"这一个问题。也正因为克制，它才可能成为标准。
