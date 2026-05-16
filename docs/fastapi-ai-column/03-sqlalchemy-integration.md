# 数据库集成：SQLAlchemy + MySQL/PostgreSQL

> **文章信息**  
> - 标题：数据库集成：SQLAlchemy + MySQL/PostgreSQL  
> - 字数：4800字  
> - 预估阅读时间：22分钟  
> - 难度：⭐⭐☆☆☆

---

## 一、为什么选择SQLAlchemy？

在Python ORM领域，SQLAlchemy是当之无愧的首选。根据2025年JetBrains开发者调查，SQLAlchemy在Python Web项目中的使用率超过60%，主要原因：

1. **异步原生支持**：SQLAlchemy 2.0+完整支持asyncio，async/await语法
2. **类型提示完善**：SQLAlchemy 2.0强化了类型提示，IDE支持更好
3. **多数据库支持**：MySQL、PostgreSQL、SQLite、Oracle等只需修改连接字符串
4. **性能优秀**：连接池、预编译语句、批量操作等优化到位

本篇文章将带你在FastAPI中集成SQLAlchemy，实现完整的CRUD操作。

## 二、环境准备

### 2.1 安装依赖

```bash
# 安装SQLAlchemy和异步数据库驱动
uv pip install sqlalchemy[asyncio] asyncpg aiomysql aiosqlite

# 安装数据库迁移工具
uv pip install alembic

# 验证安装
python -c "import sqlalchemy; print(sqlalchemy.__version__)"
# 输出：2.0.0 或更高版本
```

### 2.2 数据库驱动对比

| 数据库 | 驱动 | 特点 | 适用场景 |
|--------|------|------|----------|
| PostgreSQL | asyncpg | 性能最高，支持所有PG特性 | 高并发生产环境 |
| MySQL | aiomysql | 异步支持，社区活跃 | MySQL生产环境 |
| SQLite | aiosqlite | 无需安装，嵌入使用 | 开发/测试/嵌入式 |

> **推荐**：开发环境使用SQLite，生产环境使用PostgreSQL（性能比MySQL好30-50%）。

## 三、数据库配置

### 3.1 连接配置

创建`app/database.py`：

```python
"""数据库配置"""
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine, StaticPool
from typing import AsyncGenerator
import os


# 模型基类
class Base(DeclarativeBase):
    """数据库模型基类"""
    pass


# 数据库URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./data.db"  # 默认SQLite
)


# 创建引擎
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "false").lower() == "true",  # SQL日志
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_pre_ping=True,  # 连接前ping
)


# 创建会话工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不自动过期
)


# 同步引擎（用于创建表）
sync_engine = create_engine(
    DATABASE_URL.replace("+aiosqlite", "").replace("asyncpg", "").replace("aiomysql", ""),
    echo=False,
    poolclass=StaticPool,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

### 3.2 使用环境变量

创建`.env`文件：

```bash
# 开发环境
DATABASE_URL=sqlite+aiosqlite:///./data.db
DEBUG=true

# PostgreSQL��产环境
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# MySQL生产环境
# DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/dbname
```

## 四、ORM模型定义

### 4.1 基础模型

创建`app/models/user.py`：

```python
"""用户模型"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 唯一字段
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    
    # 必填字段
    hashed_password = Column(String(255), nullable=False)
    
    # 可选字段
    full_name = Column(String(100))
    bio = Column(Text)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关系
    items = relationship("Item", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Item(Base):
    """商品表"""
    __tablename__ = "items"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 外键
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 必填字段
    name = Column(String(100), nullable=False, index=True)
    price = Column(Integer, nullable=False)  # 以分为单位
    
    # 可选字段
    description = Column(Text)
    image_url = Column(String(500))
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关系
    owner = relationship("User", back_populates="items")
    
    def __repr__(self):
        return f"<Item(id={self.id}, name='{self.name}')>"
```

### 4.2 Pydantic模型

创建`app/schemas/user.py`：

```python
"""Pydantic schemas"""
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


# 用户创建
class UserCreate(BaseModel):
    """用户创建请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


# 用户更新
class UserUpdate(BaseModel):
    """用户更新请求"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None


# 用户响应
class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# 商品创建
class ItemCreate(BaseModel):
    """商品创建请求"""
    name: str = Field(..., min_length=1, max_length=100)
    price: int = Field(..., ge=0, description="价格（单位：分）")
    description: Optional[str] = None
    image_url: Optional[str] = None


# 商品更新
class ItemUpdate(BaseModel):
    """商品更新请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    image_url: Optional[str] = None


# 商品响应
class ItemResponse(BaseModel):
    """商品响应"""
    id: int
    owner_id: int
    name: str
    price: int
    description: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# 带用户信息的商品响应
class ItemWithOwnerResponse(ItemResponse):
    """带用户信息的商品响应"""
    owner: Optional[UserResponse] = None
```

### 4.3 关系定义

```python
"""关系定义详解"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Category(Base):
    """分类表"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # 一对多关系：一个分类多个商品
    items = relationship("Item", back_populates="category")


class Item(Base):
    """商品表（带分类）"""
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    
    name = Column(String(100), nullable=False, index=True)
    price = Column(Integer, nullable=False)
    description = Column(Text)
    
    # 关系
    owner = relationship("User", back_populates="items")
    category = relationship("Category", back_populates="items")
```

## 五、CRUD操作

### 5.1 CRUD仓储类

创建`app/crud/user.py`：

```python
"""用户CRUD操作"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from typing import Optional, List
import hashlib


def hash_password(password: str) -> str:
    """密码哈希（生产环境应使用bcrypt）"""
    return hashlib.sha256(password.encode()).hexdigest()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """通过ID获取用户"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalars().first()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """通过用户名获取用户"""
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """通过邮箱获取用户"""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalars().first()


async def get_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[User]:
    """获取用户列表"""
    query = select(User).offset(skip).limit(limit)
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """创建用户"""
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        full_name=user.full_name,
    )
    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    return db_user


async def update_user(
    db: AsyncSession,
    user_id: int,
    user_update: UserUpdate
) -> Optional[User]:
    """更新用户"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.flush()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """删除用户"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    await db.delete(user)
    await db.flush()
    return True


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str
) -> Optional[User]:
    """认证用户"""
    user = await get_user_by_username(db, username)
    if not user:
        return None
    
    if user.hashed_password != hash_password(password):
        return None
    
    return user
```

### 5.2 商品CRUD

创建`app/crud/item.py`：

```python
"""商品CRUD操作"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.user import Item, User
from app.schemas.item import ItemCreate, ItemUpdate
from typing import Optional, List


async def get_item_by_id(db: AsyncSession, item_id: int) -> Optional[Item]:
    """通过ID获取商品"""
    result = await db.execute(
        select(Item)
        .options(selectinload(Item.owner))
        .where(Item.id == item_id)
    )
    return result.scalars().first()


async def get_items(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    owner_id: Optional[int] = None,
    category_id: Optional[int] = None
) -> List[Item]:
    """获取商品列表"""
    query = select(Item).offset(skip).limit(limit)
    
    if owner_id is not None:
        query = query.where(Item.owner_id == owner_id)
    
    if category_id is not None:
        query = query.where(Item.category_id == category_id)
    
    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def create_item(
    db: AsyncSession,
    item: ItemCreate,
    owner_id: int
) -> Item:
    """创建商品"""
    db_item = Item(
        owner_id=owner_id,
        name=item.name,
        price=item.price,
        description=item.description,
        image_url=item.image_url,
    )
    db.add(db_item)
    await db.flush()
    await db.refresh(db_item)
    return db_item


async def update_item(
    db: AsyncSession,
    item_id: int,
    item_update: ItemUpdate
) -> Optional[Item]:
    """更新商品"""
    item = await get_item_by_id(db, item_id)
    if not item:
        return None
    
    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    await db.flush()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item_id: int) -> bool:
    """删除商品"""
    item = await get_item_by_id(db, item_id)
    if not item:
        return False
    
    await db.delete(item)
    await db.flush()
    return True
```

### 5.3 FastAPI路由集成

创建`app/routers/users.py`：

```python
"""用户路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.crud import user as crud_user
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
)
from app.models.user import User

router = APIRouter(prefix="/users", tags=["用户"])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户"""
    token = credentials.credentials
    # 这里应该是JWT解析
    user = await crud_user.get_user_by_id(db, int(token))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token"
        )
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建用户"""
    # 检查用���名���否存在
    existing = await crud_user.get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否存在
    existing = await crud_user.get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    return await crud_user.create_user(db, user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取用户信息"""
    user = await crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """用户列表"""
    return await crud_user.get_users(db, skip=skip, limit=limit)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户"""
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限"
        )
    
    user = await crud_user.update_user(db, user_id, user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除用户"""
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限"
        )
    
    success = await crud_user.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return None
```

## 六、分页与过滤

### 6.1 基础分页

```python
"""分页实现"""
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from typing import Optional
from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Query(1, ge=1)
    page_size: int = Query(20, ge=1, le=100)


async def paginate(
    db: AsyncSession,
    query,
    page: int = 1,
    page_size: int = 20
) -> PaginatedResponse:
    """通用分页函数"""
    # 获取总数
    count_query = select(User).where()  # 简化
    total = len(await db.execute(count_query))
    
    # 获取分页数据
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().unique().all())
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )
```

### 6.2 高级过滤

```python
"""高级过滤"""
from fastapi import Depends, Query
from sqlalchemy import or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from typing import Optional


async def search_users(
    db: AsyncSession,
    q: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None,
    min_created_at: Optional[datetime] = None,
    max_created_at: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 20
):
    """搜索用户"""
    query = select(User)
    
    # 文本搜索
    if q:
        query = query.where(
            or_(
                User.username.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
                User.full_name.ilike(f"%{q}%")
            )
        )
    
    # 状态过滤
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    if is_admin is not None:
        query = query.where(User.is_admin == is_admin)
    
    # 时间范围
    if min_created_at:
        query = query.where(User.created_at >= min_created_at)
    
    if max_created_at:
        query = query.where(User.created_at <= max_created_at)
    
    # 排序和分页
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().unique().all())
```

## 七、数据库迁移（Alembic）

### 7.1 Alembic配置

```bash
# 初始化Alembic
alembic init alembic

# 生成迁移脚本
alembic revision --autogenerate -m "add users table"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

### 7.2 迁移配置

创建`alembic/env.py`：

```python
"""Alembic环境配置"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.models.user import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线迁移"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """执行迁移"""
    context.configure(connection=connection, target_metadata=target_metadata)
    
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """异步迁移"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    
    await connectable.dispose()


def run_migrations_online() -> None:
    """在线迁移"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## 八、���接���配置

```python
"""连接池配置详解"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

# 开发环境（小型连接池）
engine_dev = create_async_engine(
    "sqlite+aiosqlite:///./data.db",
    echo=True,
    poolclass=NullPool,  # 无连接池
)


# 生产环境（大型连接池）
engine_prod = create_async_engine(
    "postgresql+asyncpg://user:password@localhost:5432/dbname",
    echo=False,
    pool_size=20,  # 基础连接数
    max_overflow=30,  # 溢出连接数
    pool_pre_ping=True,  # 连接前测试
    pool_recycle=3600,  # 连接回收时间（秒）
    pool_timeout=30,  # 获取连接超时
)


# 连接池配置说明
pool_config = {
    "pool_size": 20,  # 基础连接数，并发请求上限
    "max_overflow": 30,  # 额外连接数，极限情况可达50
    "pool_recycle": 3600,  # 1小时回收，避免僵尸连接
    "pool_pre_ping": True,  # 使用前ping，确保连接有效
}


# 预估并发容量
# 假设每个请求平均耗时100ms
# 理论QPS = pool_size / avg_time = 20 / 0.1 = 200 QPS
# 加上溢出 = 50 / 0.1 = 500 QPS
```

## 九、踩坑记录

### 9.1 常见错误

**错误1：异步会话未关闭**
```python
# 错误写法
async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()
    # 会话未关闭，连接泄漏

# 正确写法（使用Depends）
async def get_user(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()
    # 通过依赖注入自动管理生命周期
```

**错误2：relationship未加载**
```python
# 错误写法
result = await db.execute(select(Item).where(Item.id == item_id))
item = result.scalars().first()
print(item.owner.username)  # 可能未加载，报错

# 正确写法（使用selectinload）
result = await db.execute(
    select(Item)
    .options(selectinload(Item.owner))
    .where(Item.id == item_id)
)
item = result.scalars().first()
print(item.owner.username)  # 正常
```

**错误3：事务未提交**
```python
# 错误写法
async def create_user(db: AsyncSession, user: UserCreate):
    db_user = User(username=user.username, ...)
    db.add(db_user)
    return db_user  # 未提交，数据库无数据

# 正确写法
async def create_user(db: AsyncSession = Depends(get_db), user: UserCreate):
    db_user = User(username=user.username, ...)
    db.add(db_user)
    await db.commit()  # 或在Depends中自动commit
    return db_user
```

### 9.2 数据库差异

| 问题 | PostgreSQL | MySQL | 解决方案 |
|------|------------|-------|----------|
| 自增ID | SERIAL | AUTO_INCREMENT | 使用autoincrement=True |
| 大小写 | 敏感 | 敏感 | 表名统一小写 |
| 布尔值 | BOOLEAN | TINYINT(1) | 使用Boolean类型 |
| 时间戳 | TIMESTAMP | DATETIME | 使用DateTime(timezone=True) |

> **踩坑记录5**：在SQLAlchemy 2.0中，查询需要使用`.scalars().first()`获取单条记录，`.scalars().all()`获取列表。老API `.first()` 已废弃。

## 十、总结

本文我们完成了：

1. ✅ 数据库配置：SQLAlchemy异步引擎
2. ✅ ORM模型：用户和商品表定义
3. ✅ Pydantic模型：请求/响应schemas
4. ✅ CRUD操作：完整的增删改查
5. ✅ FastAPI集成：路由和依赖注入
6. ✅ 分页过滤：通用分页实现
7. ✅ Alembic迁移：数据库版本管理
8. ✅ 连接池配置：性能和并发优化

SQLAlchemy是FastAPI应用数据层的核心，它让数据库操作变得优雅且安全。下一篇文章我们将学习认证与权限：JWT + OAuth2完整实现。

> **下篇预告**：《认证与权限：JWT + OAuth2完整实现》
> - JWT令牌
> - OAuth2密码模式
> - RBAC权限控制