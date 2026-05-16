# FastAPI + AI Agent工具调用实战

> **文章信息**：标题《FastAPI + AI Agent工具调用实战》| 字数：约4000字 | 预估阅读时间：15分钟

---

## 1. AI Agent架构概述

AI Agent（智能体）是能够自主完成复杂任务的AI系统。与普通LLM对话不同，Agent有：

- **规划能力**：分解任务、制定执行计划
- **工具调用**：调用外部API、搜索、计算等
- **记忆**：保存对话历史、上下文
- **反思**：检查结果，决定是否重试

一个典型的Agent执行流程：

```
用户请求 → 规划(Plan) → 执行(Act) → 观察(Observe) → 决策(Decide) → 输出
```

---

## 2. MCP协议详解

MCP（Model Context Protocol）是Anthropic提出的标准化协议，让AI模型与外部工具通信。

**为什么需要MCP？**
- 统一工具定义格式
- 支持多工具协同
- 安全性（工具权限控制）
- 可扩展（新增工具无需改代码）

**MCP核心概念**：

| 概念 | 说明 |
|------|------|
| Host | 调用工具的AI应用（如Claude Desktop） |
| Server | 提供工具的服务（如文件系统、数据库） |
| Tool | 具体操作（read_file、search、query_db） |
| Resource | AI可读取的数据（文档、配置） |

---

## 3. 用FastAPI实现MCP Server

### 3.1 项目结构

```bash
fastapi-mcp-server/
├── main.py              # FastAPI主入口
├── mcp_server.py        # MCP Server核心
├── tools/               # 工具定义
│   ├── __init__.py
│   ├── calculator.py
│   ├── weather.py
│   └── search.py
├── models.py            # Pydantic模型
├── config.py            # 配置
└── requirements.txt
```

### 3.2 安装依赖

```bash
pip install fastapi uvicorn pydantic httpx python-dotenv
```

### 3.3 工具定义

```python
# tools/__init__.py
from .calculator import calculator_tool
from .weather import weather_tool
from .search import search_tool

__all__ = [calculator_tool, weather_tool, search_tool]
```

```python
# tools/calculator.py
from typing import Annotated, Any
from pydantic import BaseModel, Field

class CalculatorInput(BaseModel):
    """计算器输入"""
    expression: str = Field(..., description="数学表达式，如 '2+3*5'")

def calculate(a: float, b: float, operator: str) -> float:
    """执行数学计算"""
    if operator == "+":
        return a + b
    elif operator == "-":
        return a - b
    elif operator == "*":
        return a * b
    elif operator == "/":
        if b == 0:
            raise ValueError("除数不能为0")
        return a / b
    else:
        raise ValueError(f"未知运算符: {operator}")

calculator_tool = {
    "name": "calculate",
    "description": "执行数学计算，支持加减乘除",
    "input_schema": {
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "第一个数"},
            "b": {"type": "number", "description": "第二个数"},
            "operator": {"type": "string", "enum": ["+", "-", "*", "/"], "description": "运算符"}
        },
        "required": ["a", "b", "operator"]
    },
    "handler": calculate
}
```

```python
# tools/weather.py
import httpx
from typing import Any

async def get_weather(city: str) -> dict:
    """获取城市天气（模拟）"""
    # 实际项目中使用真实天气API
    weather_data = {
        "北京": {"temp": 22, "condition": "晴", "humidity": 45},
        "上海": {"temp": 25, "condition": "多云", "humidity": 60},
        "深圳": {"temp": 28, "condition": "雨", "humidity": 80},
    }
    
    result = weather_data.get(city, {"temp": 20, "condition": "未知", "humidity": 50})
    return {
        "city": city,
        "temperature": result["temp"],
        "condition": result["condition"],
        "humidity": result["humidity"]
    }

weather_tool = {
    "name": "get_weather",
    "description": "获取指定城市的天气信息",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称，如'北京'"}
        },
        "required": ["city"]
    },
    "handler": get_weather
}
```

```python
# tools/search.py
from typing import Any

class SearchInput(BaseModel):
    query: str = Field(..., description="搜索关键词")
    limit: int = Field(default=5, description="返回结果数量")

async def web_search(query: str, limit: int = 5) -> dict:
    """模拟网络搜索"""
    # 实际项目中使用真实搜索API
    results = [
        {"title": f"关于'{query}'的结果1", "url": "https://example.com/1", "snippet": "这是搜索结果摘要..."},
        {"title": f"关于'{query}'的结果2", "url": "https://example.com/2", "snippet": "这是搜索结果摘要..."},
        {"title": f"关于'{query}'的结果3", "url": "https://example.com/3", "snippet": "这是搜索结果摘要..."},
    ]
    return {"query": query, "results": results[:limit], "total": len(results)}

search_tool = {
    "name": "web_search",
    "description": "搜索网络信息",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
            "limit": {"type": "integer", "description": "返回结果数量", "default": 5}
        },
        "required": ["query"]
    },
    "handler": web_search
}
```

### 3.4 MCP Server核心

```python
# mcp_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json

from tools import calculator_tool, weather_tool, search_tool

app = FastAPI(title="MCP Server", version="1.0.0")

# 注册所有工具
TOOLS = {
    calculator_tool["name"]: calculator_tool,
    weather_tool["name"]: weather_tool,
    search_tool["name"]: search_tool,
}

class ToolCallRequest(BaseModel):
    """工具调用请求"""
    tool: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="工具参数")

class ToolCallResponse(BaseModel):
    """工具调用响应"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None

class AgentRequest(BaseModel):
    """Agent请求"""
    user_message: str = Field(..., description="用户消息")
    context: Optional[List[Dict[str, str]]] = Field(default=None, description="对话历史")

class AgentResponse(BaseModel):
    """Agent响应"""
    response: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    final_result: Optional[Any] = None

@app.get("/")
async def root():
    return {"message": "MCP Server is running", "version": "1.0.0"}

@app.get("/tools")
async def list_tools():
    """列出所有可用工具"""
    return {
        "tools": [
            {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"]
            }
            for tool in TOOLS.values()
        ]
    }

@app.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    """直接调用单个工具"""
    if request.tool not in TOOLS:
        raise HTTPException(status_code=404, detail=f"工具'{request.tool}'不存在")
    
    tool = TOOLS[request.tool]
    
    try:
        handler = tool["handler"]
        # 判断是否为异步函数
        import asyncio
        if asyncio.iscoroutinefunction(handler):
            result = await handler(**request.arguments)
        else:
            result = handler(**request.arguments)
        
        return ToolCallResponse(success=True, result=result)
    except Exception as e:
        return ToolCallResponse(success=False, error=str(e))

@app.post("/agent", response_model=AgentResponse)
async def agent_invoke(request: AgentRequest):
    """简单Agent调用（规划+执行）"""
    user_msg = request.user_message.lower()
    tool_calls = []
    final_result = None
    
    # 简单意图识别
    if "天气" in user_msg or "weather" in user_msg:
        # 提取城市名（简化版）
        city = user_msg.replace("天气", "").replace("weather", "").strip()
        if not city:
            city = "北京"
        
        try:
            result = await weather_tool["handler"](city=city)
            tool_calls.append({"tool": "get_weather", "args": {"city": city}, "result": result})
            final_result = f"{city}今天天气：{result['condition']}，气温{result['temperature']}°C，湿度{result['humidity']}%"
        except Exception as e:
            return AgentResponse(response=f"查询天气失败：{str(e)}")
    
    elif "搜索" in user_msg or "search" in user_msg or "找" in user_msg:
        query = user_msg.replace("搜索", "").replace("search", "").replace("找", "").strip()
        if not query:
            return AgentResponse(response="请提供搜索关键词")
        
        try:
            result = await search_tool["handler"](query=query, limit=5)
            tool_calls.append({"tool": "web_search", "args": {"query": query}, "result": result})
            
            response_text = f"搜索'{query}'找到{len(result['results'])}条结果：\n"
            for i, r in enumerate(result["results"], 1):
                response_text += f"{i}. {r['title']}\n  {r['snippet']}\n"
            final_result = response_text
        except Exception as e:
            return AgentResponse(response=f"搜索失败：{str(e)}")
    
    elif "计算" in user_msg or "calculate" in user_msg or any(op in user_msg for op in ["+", "-", "*", "/"]):
        # 简单计算器：提取两个数字和运算符
        import re
        numbers = re.findall(r'-?\d+\.?\d*', user_msg)
        operators = [op for op in ["+", "-", "*", "/"] if op in user_msg]
        
        if len(numbers) >= 2 and operators:
            try:
                result = await calculator_tool["handler"](
                    a=float(numbers[0]),
                    b=float(numbers[1]),
                    operator=operators[0]
                )
                tool_calls.append({
                    "tool": "calculate",
                    "args": {"a": numbers[0], "b": numbers[1], "operator": operators[0]},
                    "result": result
                })
                final_result = f"{numbers[0]} {operators[0]} {numbers[1]} = {result}"
            except Exception as e:
                return AgentResponse(response=f"计算失败：{str(e)}")
        else:
            return AgentResponse(response="请提供完整的计算表达式，如：'计算 5 + 3'")
    
    else:
        return AgentResponse(
            response=f"我当前支持以下工具：\n"
                    f"1. 查天气 - 如：'北京天气怎么样'\n"
                    f"2. 搜索信息 - 如：'搜索Python教程'\n"
                    f"3. 数学计算 - 如：'计算 10 / 3'\n"
                    f"请告诉我你想做什么？"
        )
    
    return AgentResponse(
        response=final_result or "处理完成",
        tool_calls=tool_calls,
        final_result=final_result
    )

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy", "tools_count": len(TOOLS)}
```

---

## 4. 主入口文件

```python
# main.py
from mcp_server import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 5. 测试MCP Server

### 5.1 启动服务

```bash
cd fastapi-mcp-server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5.2 测试端点

```bash
# 1. 查看所有工具
curl http://localhost:8000/tools

# 2. 直接调用天气工具
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool": "get_weather", "arguments": {"city": "上海"}}'

# 3. Agent调用（查天气）
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"user_message": "上海天气怎么样"}'

# 4. Agent调用（搜索）
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"user_message": "搜索Python FastAPI教程"}'

# 5. Agent调用（计算）
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"user_message": "计算 128 + 456"}'
```

### 5.3 Swagger文档

打开 http://localhost:8000/docs 查看交互式API文档。

---

## 6. 与DeepSeek/Qwen集成

上面是一个简化版Agent。生产环境中，可以用DeepSeek作为大脑来驱动这个Agent：

```python
# agent_with_deepseek.py
import httpx
import os
from typing import List, Dict, Any

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

SYSTEM_PROMPT = """你是一个智能助手，可以调用以下工具：
- get_weather(city): 获取城市天气
- web_search(query, limit): 搜索网络信息
- calculate(a, operator, b): 执行数学计算

当需要使用工具时，在回复中明确说明工具名称和参数。"""

async def deepseek_chat(messages: List[Dict], tools: List[Dict]) -> str:
    """调用DeepSeek API"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "tools": tools,
                "temperature": 0.7
            },
            timeout=30.0
        )
        result = response.json()
        return result["choices"][0]["message"]

# 工具定义（符合OpenAI tool calling格式）
openai_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索网络信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "limit": {"type": "integer", "description": "返回数量", "default": 5}
                },
                "required": ["query"]
            }
        }
    }
]

async def agent_loop(user_message: str):
    """Agent主循环"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
    
    while True:
        response = await deepseek_chat(messages, openai_tools)
        
        # 检查是否需要调用工具
        if response.get("tool_calls"):
            # 执行工具
            for tool_call in response["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                args = tool_call["function"]["arguments"]
                
                # 调用工具
                from mcp_server import TOOLS
                tool = TOOLS.get(tool_name)
                if tool:
                    import asyncio
                    if asyncio.iscoroutinefunction(tool["handler"]):
                        result = await tool["handler"](**args)
                    else:
                        result = tool["handler"](**args)
                    
                    messages.append(response)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": str(result)
                    })
        else:
            # 最终回复
            return response["content"]
```

---

## 7. 多工具协同示例

一个更复杂的场景：用户问"北京今天热吗？顺便搜一下有什么好玩的"。

```python
async def multi_tool_example():
    """多工具协同示例"""
    # 1. 先查天气
    weather = await weather_tool["handler"](city="北京")
    
    # 2. 根据天气决定搜索关键词
    if weather["temp"] > 25:
        search_query = "北京室内活动推荐"
    else:
        search_query = "北京户外景点推荐"
    
    # 3. 执行搜索
    search_results = await search_tool["handler"](query=search_query, limit=3)
    
    # 4. 整合结果
    return {
        "weather": weather,
        "suggestions": search_results["results"],
        "summary": f"北京今天{weather['condition']}，气温{weather['temperature']}°C。推荐：{search_results['results'][0]['title']}"
    }
```

---

## 8. 踩坑记录

### 坑1：异步工具与同步工具混用

**问题**：定义工具时没注意`handler`可能是异步也可能是同步，调用时会出错。

**解决**：统一用`asyncio.iscoroutinefunction()`检查，如果是同步函数就直接调用，如果是异步函数就用`await`调用。

```python
import asyncio

if asyncio.iscoroutinefunction(handler):
    result = await handler(**args)
else:
    result = handler(**args)
```

### 坑2：工具参数验证失败

**问题**：传入的参数格式不对（如少了必需字段），但只返回了通用错误。

**解决**：在调用前用Pydantic验证参数：

```python
from pydantic import ValidationError

try:
    validated = tool["input_schema"].parse_obj(arguments)
    result = await handler(**validated.dict())
except ValidationError as e:
    return {"error": f"参数错误: {e}"}
```

### 坑3：工具调用死循环

**问题**：Agent在某些情况下会反复调用同一工具（如工具返回结果不完整）。

**解决**：添加最大调用次数限制和结果验证：

```python
MAX_TOOL_CALLS = 5
call_count = 0

while call_count < MAX_TOOL_CALLS:
    call_count += 1
    response = await agent_step()
    if response["done"]:
        break
    
    # 验证工具返回是否有效
    if not is_valid_result(response["result"]):
        break
```

### 坑4：DeepSeek API超时

**问题**：工具调用涉及网络请求，可能超时。

**解决**：设置合理的超时时间，并提供重试：

```python
async def call_with_retry(func, max_retries=3, timeout=10):
    for i in range(max_retries):
        try:
            return await asyncio.wait_for(func(), timeout=timeout)
        except asyncio.TimeoutError:
            if i == max_retries - 1:
                raise
            continue
```

### 坑5：工具权限控制

**问题**：生产环境中，Agent可能会执行危险操作（如删除文件）。

**解决**：添加权限白名单和操作日志：

```python
ALLOWED_TOOLS = ["get_weather", "web_search", "calculate"]
DENIED_TOOLS = ["delete_file", "exec_command"]

def check_tool_permission(tool_name: str) -> bool:
    if tool_name in DENIED_TOOLS:
        return False
    if tool_name not in ALLOWED_TOOLS:
        return False
    return True
```

---

## 9. 总结

本文介绍了如何用FastAPI实现一个MCP Server，并构建简单的AI Agent系统：

1. **MCP协议**：标准化的工具调用协议，让AI与外部服务解耦
2. **工具定义**：统一的工具格式，支持同步/异步handler
3. **Agent循环**：Plan → Act → Observe → Decide
4. **多工具协同**：根据任务自动选择合适的工具组合
5. **与DeepSeek集成**：用大模型作为Agent的大脑

**进阶方向**：
- 添加记忆系统（保存对话历史）
- 实现更复杂的规划算法（ReAct、CoT）
- 添加自我反思能力（检查结果是否正确）
- 支持更多工具（数据库查询、文件操作等）
- 添加安全审计和权限控制