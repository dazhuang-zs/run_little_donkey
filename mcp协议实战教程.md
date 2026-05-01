# MCP协议实战：从零搭建一个让Claude能"看见"数据库的工具服务

> 这篇文章不讲概念，只讲怎么把MCP跑起来。踩过的坑都写出来了，希望能帮你省点时间。

## 一、为什么需要MCP？

先说个痛点。

我之前想让Claude帮我分析数据库里的数据，只能手动把SQL结果复制粘贴给Claude。数据少还行，数据多了就很蠢。

后来发现Anthropic推出了**MCP（Model Context Protocol）**，本质上是给AI模型装的"USB接口"——你写一个Server，Claude就能直接调你的工具，不用中间人复制粘贴了。

这篇文章就是记录我从零搭建MCP Server的完整过程，包括踩过的坑。

---

## 二、MCP架构长什么样？

一句话概括：**Claude是客户端，你的代码是服务端，中间用JSON-RPC通信。**

```
┌─────────────────┐      JSON-RPC      ┌──────────────────┐
│  Claude Desktop │ ◄───────────────► │   MCP Server     │
│   (MCP Client)  │     stdio/SSE     │  (你的Python代码) │
└─────────────────┘                    └──────────────────┘
                                              │
                                              ▼
                                       ┌──────────────────┐
                                       │  数据库/API/文件  │
                                       └──────────────────┘
```

**三种核心能力：**
- **Tools**：可执行的函数（如执行SQL、调用API）
- **Resources**：只读数据（如文件内容、日志）
- **Prompts**：预定义的提示模板

---

## 三、环境准备

### 3.1 安装Python和uv

MCP官方推荐Python 3.10+，我用的3.12。

```bash
# 安装uv（比pip快的包管理器）
pip install uv

# 验证安装
uv --version
```

### 3.2 安装MCP SDK

```bash
# 官方Python SDK
pip install mcp

# 或者用uv
uv pip install mcp
```

---

## 四、手写第一个MCP Server

我写了一个简单的SQL查询工具，让Claude能直接查询数据库。

### 4.1 项目结构

```
mcp-sql-server/
├── server.py          # MCP Server主文件
├── requirements.txt   # 依赖
└── .env              # 数据库连接信息
```

### 4.2 完整代码

**server.py**

```python
"""
MCP SQL Server - 让Claude能查询数据库
"""
import os
import json
import asyncio
from typing import Any
from contextlib import asynccontextmanager

import asyncpg
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 从环境变量读取数据库配置
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "postgres")
}

# 创建Server实例
server = Server("sql-query-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """告诉Claude有哪些工具可用"""
    return [
        Tool(
            name="execute_sql",
            description="执行SQL查询语句并返回结果。只能执行SELECT语句。",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "要执行的SELECT SQL语句"
                    }
                },
                "required": ["sql"]
            }
        ),
        Tool(
            name="list_tables",
            description="列出数据库中所有表名",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="describe_table",
            description="查看表结构，包括字段名、类型、注释",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "表名"
                    }
                },
                "required": ["table_name"]
            }
        )
    ]


@asynccontextmanager
async def get_db_connection():
    """数据库连接上下文管理器"""
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        await conn.close()


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """处理Claude的工具调用请求"""
    
    try:
        if name == "execute_sql":
            sql = arguments.get("sql", "").strip()
            
            # 安全检查：只允许SELECT
            if not sql.upper().startswith("SELECT"):
                return [TextContent(
                    type="text",
                    text="❌ 安全限制：只允许执行SELECT查询语句"
                )]
            
            async with get_db_connection() as conn:
                rows = await conn.fetch(sql)
                
                # 转换为可读格式
                if not rows:
                    return [TextContent(
                        type="text",
                        text="查询结果为空"
                    )]
                
                # 格式化输出
                columns = list(rows[0].keys())
                result = []
                result.append(" | ".join(columns))
                result.append("-" * 50)
                
                for row in rows[:100]:  # 限制最多100行
                    result.append(" | ".join(str(v) for v in row.values()))
                
                if len(rows) > 100:
                    result.append(f"\n... 共 {len(rows)} 行，仅显示前100行")
                
                return [TextContent(
                    type="text",
                    text="\n".join(result)
                )]
        
        elif name == "list_tables":
            async with get_db_connection() as conn:
                rows = await conn.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                
                table_list = [row["table_name"] for row in rows]
                return [TextContent(
                    type="text",
                    text=f"数据库中的表（共{len(table_list)}个）：\n" + "\n".join(f"- {t}" for t in table_list)
                )]
        
        elif name == "describe_table":
            table_name = arguments.get("table_name", "")
            
            async with get_db_connection() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_name = $1 AND table_schema = 'public'
                    ORDER BY ordinal_position
                """, table_name)
                
                if not rows:
                    return [TextContent(
                        type="text",
                        text=f"❌ 未找到表 '{table_name}'"
                    )]
                
                result = [f"表 `{table_name}` 结构：\n"]
                result.append("字段名 | 类型 | 可空 | 默认值")
                result.append("-" * 50)
                
                for row in rows:
                    result.append(f"{row['column_name']} | {row['data_type']} | {row['is_nullable']} | {row['column_default'] or 'NULL'}")
                
                return [TextContent(
                    type="text",
                    text="\n".join(result)
                )]
        
        else:
            return [TextContent(
                type="text",
                text=f"❌ 未知工具: {name}"
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ 执行出错: {str(e)}"
        )]


async def main():
    """启动MCP Server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
```

**requirements.txt**

```
mcp>=1.0.0
asyncpg>=0.29.0
python-dotenv>=1.0.0
```

**.env**

```
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=your_database
```

---

## 五、踩过的坑

### 5.1 坑一：stdio模式下不能print调试

MCP通过stdin/stdout通信，如果你在代码里用`print()`，会污染JSON-RPC消息流，导致连接中断。

**解决方案：写日志到文件**

```python
import logging

logging.basicConfig(
    filename='/tmp/mcp-server.log',
    level=logging.DEBUG
)

# 用logging代替print
logging.debug(f"收到请求: {name}")
```

### 5.2 坑二：异步函数必须用async

MCP SDK是异步的，所有工具函数必须是`async def`，不然会报错。

```python
# ❌ 错误
@server.call_tool()
def call_tool(name, arguments):  # 少了async
    ...

# ✅ 正确
@server.call_tool()
async def call_tool(name, arguments):  # 必须async
    ...
```

### 5.3 坑三：Tool的inputSchema必须符合JSON Schema规范

```python
# ❌ 错误：缺少type
inputSchema={
    "properties": {
        "sql": {"description": "SQL语句"}
    }
}

# ✅ 正确：完整的JSON Schema
inputSchema={
    "type": "object",
    "properties": {
        "sql": {
            "type": "string",
            "description": "要执行的SQL语句"
        }
    },
    "required": ["sql"]
}
```

### 5.4 坑四：Claude Desktop配置文件路径

不同系统的配置文件位置不同：

| 系统 | 配置文件路径 |
|------|-------------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

---

## 六、配置Claude Desktop

编辑配置文件 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "sql-query": {
      "command": "python",
      "args": ["/绝对路径/mcp-sql-server/server.py"],
      "env": {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_USER": "postgres",
        "DB_PASSWORD": "your_password",
        "DB_NAME": "your_database"
      }
    }
  }
}
```

**重要：**
- `args`里的路径必须是绝对路径
- 环境变量在这里传，不要写死在代码里

配置完重启Claude Desktop，在对话框右下角会出现一个🔧图标，表示MCP工具已加载。

---

## 七、实际使用效果

现在我可以直接跟Claude说：

> "帮我查一下users表最近一周注册的用户数量"

Claude会自动：
1. 调用`list_tables`确认表存在
2. 调用`describe_table`查看表结构
3. 调用`execute_sql`执行查询
4. 把结果整理成自然语言告诉我

整个过程我不用写一行SQL，也不用复制粘贴数据。

---

## 八、进阶：支持更多数据源

MCP的魅力在于统一接口。你可以给Claude接任何数据源：

```python
# 示例：接Redis
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="redis_get",
            description="从Redis获取key的值",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string"}
                },
                "required": ["key"]
            }
        )
    ]

# 示例：接企业API
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="search_docs",
            description="搜索内部文档系统",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"}
                },
                "required": ["query"]
            }
        )
    ]
```

---

## 九、总结

MCP解决的问题很简单：**让AI模型能直接访问你的数据源和工具**，不用人来当传声筒。

**核心要点：**
1. MCP是标准的Client-Server架构，用JSON-RPC通信
2. 一个Server可以暴露多个Tool，每个Tool是一个函数
3. stdio模式最简单，但别用print调试
4. 生产环境注意安全：限制SQL类型、控制权限

**下一步：**
- 把常用工具都封装成MCP Server（如调用内部API、查日志、发消息）
- 结合Claude Code CLI，让AI能自己写代码、调试、部署

---

**完整代码已上传GitHub：** [github.com/dazhuang-zs/mcp-sql-server](https://github.com/dazhuang-zs/mcp-sql-server)

有问题欢迎评论区交流。

---

> 作者：dazhuang-zs  
> CSDN: weixin_43726381  
> 时间：2026年4月
