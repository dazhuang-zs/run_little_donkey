# FastAPI快速入门：环境搭建+第一个接口

> **文章信息**  
> - 标题：FastAPI快速入门：环境搭建+第一个接口  
> - 字数：4200字  
> - 预估阅读时间：18分钟  
> - 难度：⭐☆☆☆☆

---

## 一、为什么选择FastAPI？

在2026年的Python Web框架生态中，FastAPI已经成为继Django之后最受欢迎的框架。根据JetBrains开发者调查，FastAPI在AI工程领域的采用率超过70%（数据来源：JetBrains Developer Ecosystem 2025），主要原因有三：

1. **自动生成API文档**：启动服务即拥有Swagger UI和ReDoc，无需手动编写文档
2. **基于类型提示的验证**：Pydantic深度集成，数据验证和序列化的代码量减少60%
3. **异步原生支持**：基于Starlette，同步/异步代码写法一致，性能对标Node.js和Go

本文将带你从零搭建FastAPI开发环境，完成第一个接口，并配置完整的开发工作流。

## 二、环境准备

### 2.1 Python版本选择

FastAPI 0.115+ 支持Python 3.10+。推荐使用Python 3.12或3.13，因为：

- PEP 709：尾调用优化，递归性能提升
- 内置typing.Concatenate类型注解，支持更复杂的函数类型
- 性能提升：3.12比3.11快15-25%（来源：Python 3.12 Release Notes）

### 2.2 虚拟环境创建

有两种方式创建虚拟环境：

**方式1：uv（推荐）**
```bash
# 安装uv（如果未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建项目目录
mkdir fastapi-ai-column && cd fastapi-ai-column

# 使用uv创建虚拟环境（自动生成pyproject.toml）
uv venv --python 3.12

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\Activate.ps1  # Windows PowerShell
# 或 .venv\Scripts\activate.bat  # Windows CMD
```

**方式2：venv（标准库）**
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

| 特性 | uv | venv |
|------|-----|------|
| 创建速度 | 秒级 | 10-30秒 |
| 依赖安装 | 并行+缓存 | 单线程 |
| 锁文件支持 | uv.lock | 无 |
| 跨平台 | ★★★★★ | ★★★★☆ |

### 2.3 安装FastAPI和Uvicorn

```bash
# 安装FastAPI和uvicorn（带热重载版本）
uv pip install fastapi uvicorn[standard]

# 验证安装
python -c "import fastapi; print(fastapi.__version__)"
# 输出：0.115.0 或更高版本
```

> **版本说明**：到2026年5月，FastAPI最新稳定版为0.115.x。如果你想体验最新功能，可以使用`uv pip install fastapi --pre`安装预览版。

## 三、第一个API接口

### 3.1 项目结构

```
fastapi-ai-column/
├── .env                    # 环境变量
├── .env.example            # 环境变量模板
├── app/
│   ├── __init__.py
│   ├── main.py             # 主应用入口
│   ├── config.py          # 配置管理
│   └── routers/
│       ├── __init__.py
│       └── hello.py       # 示例路由
├── tests/                  # 测试目录
├── pyproject.toml         # 项目配置（uv生成）
└── uv.lock               # 依赖锁文件（uv生成）
```

### 3.2 最小可运行应用

创建`app/main.py`：

```python
"""
FastAPI最小应用 - Hello World
"""
from fastapi import FastAPI

app = FastAPI(
    title="FastAPI AI助手",
    description="AI应用后端服务",
    version="1.0.0",
    docs_url="/docs",        # Swagger UI地址
    redoc_url="/redoc"       # ReDoc地址
)


@app.get("/")
async def root():
    """根路径返回欢迎信息"""
    return {
        "message": "欢迎��用FastAPI AI助手",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "fastapi-ai-column"
    }
```

### 3.3 运行应用

**方式1：命令行运行（推荐开发使用）**
```bash
# 基本启动
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 带热重载的启动（开发环境）
uvicorn app.main:app --reload --port 8000

# 指定workers数量
uvicorn app.main:app --workers 4
```

启动输出：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Swagger UI available at http://localhost:8000/docs
INFO:     ReDoc available at http://localhost:8000/redoc
```

**方式2：代码内启动（调试用）**
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

> **踩坑记录1**：在Windows的PowerShell中运行`uvicorn --reload`可能会遇到`Permission denied`错误。解决方案：使用`uvicorn app.main:app --reload --loop asyncio`明确指定事件循环，或升级到最新版本uvicorn。

## 四、路由装饰器详解

### 4.1 装饰器基础

FastAPI的路由装饰器基于HTTP方法命名，格式为`@app.method(path)`。

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


# GET请求 - 查询
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id, "name": "张三"}


# POST请求 - 创建
class UserCreate(BaseModel):
    name: str
    email: str


@app.post("/users")
async def create_user(user: UserCreate):
    return {"id": 1, **user.model_dump()}


# PUT请求 - 完整更新
@app.put("/users/{user_id}")
async def update_user(user_id: int, user: UserCreate):
    return {"user_id": user_id, **user.model_dump()}


# PATCH请求 - 部分更新
@app.patch("/users/{user_id}")
async def patch_user(user_id: int, user: UserCreate):
    return {"user_id": user_id, **user.model_dump()}


# DELETE请求 - 删除
@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    return {"deleted": user_id}
```

### 4.2 路径参数类型

```python
from fastapi import FastAPI, Path
from typing import Annotated

app = FastAPI()


# 整数类型参数
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id}


# 字符串类型参数
@app.get("/users/{username}")
async def get_user_by_name(username: str):
    return {"username": username}


# 带验证的路径参数（使用Annotated，Python 3.9+）
@app.get("/users/{user_id}")
async def get_user(
    user_id: Annotated[int, Path(gt=0, le=1000, description="用户ID")]
):
    return {"user_id": user_id}
```

### 4.3 查询参数

```python
from fastapi import FastAPI, Query
from typing import Annotated, Optional

app = FastAPI()


# 必选查询参数
@app.get("/search")
async def search(q: str = Query(...)):
    return {"q": q}


# 有默认值的查询参数
@app.get("/items")
async def list_items(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    return {
        "items": [],
        "limit": limit,
        "offset": offset
    }


# 可选查询参数
@app.get("/users")
async def list_users(
    name: Optional[str] = Query(None),
    age: Annotated[int, Query(ge=0, le=150)] = None
):
    filters = {}
    if name:
        filters["name"] = name
    if age is not None:
        filters["age"] = age
    return {"filters": filters}
```

### 4.4 请求体

```python
from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Optional

app = FastAPI()


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    quantity: int = 1


# 单个Body参数
@app.post("/items")
async def create_item(item: Item):
    return item


# 多个Body参数（使用Body显式指定）
@app.post("/items/multiple")
async def create_item_multiple(
    item: Item = Body(...),
    category: str = Body(...)
):
    return {
        "item": item,
        "category": category
    }
```

> **踩坑记录2**：当有两个Body参数时，FastAPI无法自动识别。解决方案有两种：
> 1. 使用Pydantic嵌套模型
> 2. 使用`Body(...)`显式标记每个参数

## 五、交互式文档

### 5.1 Swagger UI

访问 http://localhost:8000/docs，你会看到自动生成的API文档界面。这个文档：

- 可以直接测试API
- 自动填充请求参数
- 显示所有endpoint
- 支持导出OpenAPI规范

### 5.2 ReDoc

访问 http://localhost:8000/redoc，你会看到另一种风格的文档：

- 更清晰的文档导航
- 适合API规范展示
- 不支持直接测试

### 5.3 自定义文档

```python
from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html

app = FastAPI()


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    """自定义Swagger UI"""
    return get_swagger_ui_html(
        title="My API - Swagger UI",
        openapi_url=app.openapi_url
    )


@app.get("/redoc", include_in_schema=False)
async def custom_redoc():
    """自定义ReDoc"""
    return get_redoc_html(
        title="My API - ReDoc",
        openapi_url=app.openapi_url
    )
```

## 六、开发模式配置

### 6.1 环境变量管理

安装配置管理依赖：
```bash
uv pip install pydantic-settings python-dotenv
```

创建`.env`文件：
```bash
# .env
APP_NAME=FastAPI AI助手
APP_VERSION=1.0.0
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=sqlite+aiosqlite:///./data.db

# API密钥
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

创建`app/config.py`：
```python
"""
配置管理
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # 忽略额外字段
    )
    
    # 应用配置
    app_name: str = "FastAPI AI助手"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///./data.db"
    
    # API配置
    deepseek_api_key: Optional[str] = None
    
    # CORS配置
    cors_origins: list = ["*"]


# 全局配置实例
settings = Settings()
```

### 6.2 使用配置

```python
from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version
)


@app.get("/config")
async def show_config():
    """展示当前配置"""
    return {
        "app_name": settings.app_name,
        "debug": settings.debug,
        "port": settings.port
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
```

> **踩坑记录3**：在`.env`文件中不要使用中文，因为`python-dotenv`在Windows下可能有编码问题。如果必须使用中文，创建`.env`文件时使用UTF-8编码。

### 6.3 生产环境配置

```python
# .env.prod（生产环境）
DEBUG=false
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=warning
```

启动生产模式：
```bash
# 使用生产配置文件
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 或指定配置文件
uvicorn app.main:app --host 0.0.0.0 --port 8000 --env-dir .env.prod
```

## 七、请求/响应模型

### 7.1 响应模型

```python
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

app = FastAPI()


class Item(BaseModel):
    name: str
    price: float


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    name: str
    email: str
    created_at: datetime
    items: Optional[List[Item]] = None
    
    model_config = {"json_schema_extra": {
        "example": {
            "id": 1,
            "name": "张三",
            "email": "zhangsan@example.com",
            "created_at": "2026-01-01T00:00:00",
            "items": [{"name": "商品1", "price": 99.0}]
        }
    }}


class UserCreate(BaseModel):
    """用户创建请求模型"""
    name: str
    email: str
    password: str


@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    """创建用户并返回完整信息"""
    # 这里应该是数据库插入逻辑
    return UserResponse(
        id=1,
        name=user.name,
        email=user.email,
        created_at=datetime.now(),
        items=[]
    )


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """获取用户"""
    return UserResponse(
        id=user_id,
        name="张三",
        email="zhangsan@example.com",
        created_at=datetime.now(),
        items=[]
    )
```

### 7.2 状态码控制

```python
from fastapi import FastAPI, HTTPException, status

app = FastAPI()


@app.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item():
    """创建成功返回201"""
    return {"id": 1}


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    """删除成功返回204"""
    if item_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    # 返回None会产生204状态码
    return None
```

## 八、踩坑记录

### 8.1 Windows/macOS/Linux差异

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 热重载不生效 | Windows文件系统事件延迟 | 升级uvicorn到最新版本 |
| 路径斜杠问题 | Windows与Linux路径分隔符不同 | 使用`pathlib.Path`处理路径 |
| 中文乱码 | Windows CMD默认GBK编码 | 环境变量设置`PYTHONIOENCODING=utf-8` |
| 端口被占用 | 某些服务占用8000端口 | 改用其他端口如8001 |

### 8.2 常见错误

**错误1：端口被占用**
```bash
# 查找占用端口的进程
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# 结束进程
kill -9 <PID>  # macOS/Linux
taskkill /F /PID <PID>  # Windows
```

**错误2：模块导入失败**
```bash
# 检查是否在虚拟环境中
which python  # 应该指向.venv/bin/python

# 重新安装依赖
uv pip install -r requirements.txt
# 或
uv pip install -e .
```

**错误3：CORS跨域问题**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 九、总结

本文我们完成了：

1. ✅ 环境搭建：Python 3.12 + uv虚拟环境 + FastAPI安装
2. ✅ 第一个API：最小可运行应用 + 健康检查
3. ✅ 路由装饰器：GET/POST/PUT/DELETE + 路径/查询/Body参数
4. ✅ 交互式文档：Swagger UI + ReDoc
5. ✅ 开发配置：.env + pydantic-settings

FastAPI的核心优势在于：**用最少的代码，得到最完整的API**。下一篇文章我们将深入学习Pydantic模型，掌握请求/响应数据验证的精髓。

> **下篇预告**：《请求/响应模型：Pydantic从入门到实战》
> - 自定义验证器
> - 嵌套模型
> - 高级用法（computed_field、model_validator）