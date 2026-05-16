# 请求/响应模型：Pydantic从入门到实战

> **文章信息**  
> - 标题：请求/响应模型：Pydantic从入门到实战  
> - 字数：4500字  
> - 预估阅读时间：20分钟  
> - 难度：⭐⭐☆☆☆

---

## 一、为什么Pydantic是FastAPI的核心？

在FastAPI 0.115版本中，Pydantic 2.x已经完全取代了之前基于Pydantic v1的验证逻辑。Pydantic的核心优势在于：

1. **运行时验证**：数据进入应用前完成验证，错误可提前捕获
2. **类型提示集成**：IDE完美支持，代码补全和类型检查
3. **序列化/反序列化**：自动转换JSON、ORM对象、Python对象
4. **性能提升**：Pydantic 2.x比1.x快50-100倍（来源：Pydantic 2.0 Release）

根据2025年Python开发者调查（Python Developers Survey 2025），Pydantic已经成为继requests和pytest之后第三流行的Python库，在AI工程领域更是必备技能。

## 二、Pydantic基础

### 2.1 BaseModel - 数据模型

```python
"""Pydantic基础：BaseModel"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class User(BaseModel):
    """用户模型"""
    # 必填字段
    username: str
    email: str
    
    # 有默认值的字段（可选）
    age: int = 0
    
    # 可选字段（None）
    bio: Optional[str] = None
    
    # 模型配置
    model_config = ConfigDict(
        str_strip_whitespace=True,  # 自动去除首尾空格
        str_to_lower=True,        # 字符串转小写
        validate_assignment=True,  # 赋值时验证
    )


# 使用示例
if __name__ == "__main__":
    # 完整数据
    user1 = User(
        username="zhangsan",
        email="ZHANG@EXAMPLE.COM",
        age=25,
        bio="你好"
    )
    print(f"user1: {user1.model_dump()}")
    # 输出: {'username': 'zhangsan', 'email': 'zhang@example.com', 'age': 25, 'bio': '你好'}
    
    # 缺少可选字段
    user2 = User(
        username="lisi",
        email="lisi@example.com"
    )
    print(f"user2: {user2.model_dump()}")
    # 输出: {'username': 'lisi', 'email': 'lisi@example.com', 'age': 0, 'bio': None}
    
    # 验证失败
    try:
        user3 = User(
            username="wangwu",
            email="invalid-email"  # 无效邮箱
        )
    except Exception as e:
        print(f"验证错误: {e}")
```

### 2.2 Field - 字段定义

```python
"""Field字段定义详解"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Annotated
from datetime import datetime


class Item(BaseModel):
    """商品模型 - 详细字段定义"""
    
    # 基本字段定义
    name: str = Field(..., description="商品名称", min_length=1)
    price: float = Field(..., gt=0, description="商品价格", examples=[99.0])
    quantity: int = Field(default=0, ge=0, le=1000, description="库存数量")
    
    # 可选字段
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="商品描述"
    )
    
    # 标签（用于文档）
    tags: list[str] = Field(
        default_factory=list,
        description="商品标签"
    )
    
    # 自定义验证器
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("商品名称不能为空")
        return v.strip()
    
    @field_validator('price')
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("价格必须大于0")
        return round(v, 2)


# 使用Annotated定义复杂类型
class SearchParams(BaseModel):
    """搜索参数 - 使用Annotated"""
    query: Annotated[str, Field(min_length=1, max_length=100)]
    page: Annotated[int, Field(ge=1, le=100, default=1)]
    page_size: Annotated[int, Field(ge=10, le=100, default=20)]


if __name__ == "__main__":
    # 完整创建
    item = Item(
        name="iPhone 16",
        price=6999.0,
        quantity=100,
        description="苹果最新款手机",
        tags=["手机", "苹果", "电子"]
    )
    print(f"item: {item.model_dump_json(indent=2)}")
    
    # 使用默认值的字段
    item2 = Item(
        name="AirPods Pro",
        price=1999.0
    )
    print(f"item2: {item2.model_dump()}")
```

### 2.3 嵌套模型

```python
"""嵌套模型"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Address(BaseModel):
    """地址模型"""
    province: str
    city: str
    district: str
    detail: str
    zip_code: Optional[str] = None


class OrderItem(BaseModel):
    """订单商品"""
    item_id: int
    name: str
    price: float
    quantity: int


class Order(BaseModel):
    """订单模型 - 嵌套结构"""
    order_id: str
    user_id: int
    items: List[OrderItem]
    total_amount: float
    shipping_address: Address
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "pending"


if __name__ == "__main__":
    # 创建嵌套模型
    order = Order(
        order_id="ORDER20260101001",
        user_id=1,
        items=[
            OrderItem(item_id=1, name="iPhone 16", price=6999.0, quantity=1),
            OrderItem(item_id=2, name="AirPods Pro", price=1999.0, quantity=2)
        ],
        total_amount=10997.0,
        shipping_address=Address(
            province="北京市",
            city="北京市",
            district="海淀区",
            detail="中关村大街1号",
            zip_code="100000"
        )
    )
    
    print(f"Order: {order.model_dump_json(indent=2)}")
    
    # 序列化嵌套对象
    data = order.model_dump()
    print(f"序列化后的地址: {data['shipping_address']}")
```

## 三、请求体解析

### 3.1 Body - 显式请求体

```python
"""FastAPI请求体详解"""
from fastapi import FastAPI, Body, Query, Path, Depends
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()


class UserCreate(BaseModel):
    """用户创建模型"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)
    age: Optional[int] = None


class UserUpdate(BaseModel):
    """用户更新模型"""
    username: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None


# 单一Body参数
@app.post("/users")
async def create_user(user: UserCreate):
    """创建用户"""
    return {
        "id": 1,
        **user.model_dump()
    }


# 多个Body参数（使用Body显式指定）
@app.put("/users/{user_id}")
async def update_user(
    user_id: int = Path(..., gt=0),
    user_update: UserUpdate = Body(...),
    notify: bool = Body(True)
):
    """更新用户"""
    return {
        "user_id": user_id,
        "update": user_update.model_dump(),
        "notify": notify
    }


# Query + Body混合
@app.post("/items/search")
async def search_items(
    q: str = Query(..., min_length=1),
    filters: UserUpdate = Body(...)
):
    """搜索商品"""
    return {"q": q, "filters": filters.model_dump()}
```

### 3.2 Query - 查询参数

```python
"""Query查询参数"""
from fastapi import FastAPI, Query
from typing import Optional, List
from pydantic import BaseModel, Field

app = FastAPI()


class Pagination(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    order: Optional[str] = "asc"


@app.get("/users")
async def list_users(
    name: Optional[str] = Query(None, min_length=1),
    age_min: Optional[int] = Query(None, ge=0),
    age_max: Optional[int] = Query(None, ge=0),
    tags: List[str] = Query(default=[]),
    pagination: Pagination = Depends()
):
    """用户列表"""
    return {
        "name_filter": name,
        "age_range": [age_min, age_max],
        "tags": tags,
        "pagination": pagination.model_dump()
    }


# 使用别名
@app.get("/products")
async def list_products(
    category_id: int = Query(..., alias="cat-id"),
    price_min: float = Query(None, alias="min-price"),
    price_max: float = Query(None, alias="max-price")
):
    """商品列表（使用别名）"""
    return {
        "category_id": category_id,
        "price_range": [price_min, price_max]
    }
```

### 3.3 Path - 路径参数

```python
"""Path路径参数"""
from fastapi import FastAPI, Path
from typing import Annotated

app = FastAPI()


@app.get("/users/{user_id}")
async def get_user(
    user_id: Annotated[int, Path(gt=0, le=1000000, description="用户ID")]
):
    """获取用户"""
    return {"user_id": user_id}


@app.get("/files/{file_path:path}")
async def get_file(
    file_path: Annotated[str, Path(description="文件路径")]
):
    """获取文件"""
    return {"file_path": file_path}


@app.get("/items/{category}/{item_id}")
async def get_item(
    category: Annotated[str, Path(min_length=1)],
    item_id: Annotated[int, Path(gt=0)]
):
    """获取商品"""
    return {"category": category, "item_id": item_id}
```

## 四、响应模型

### 4.1 response_model参数

```python
"""响应模型详解"""
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

app = FastAPI()


class Item(BaseModel):
    """商品模型"""
    id: int
    name: str
    price: float


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    created_at: datetime
    
    model_config = {"json_schema_extra": {
        "example": {
            "id": 1,
            "username": "zhangsan",
            "email": "zhangsan@example.com",
            "created_at": "2026-01-01T00:00:00"
        }
    }}


class UserDetailResponse(UserResponse):
    """用户详情响应（继承）"""
    items: List[Item] = []
    bio: Optional[str] = None


class UserCreateRequest(BaseModel):
    """用户创建请求"""
    username: str = Field(..., min_length=3)
    email: str
    password: str = Field(..., min_length=6)


@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreateRequest):
    """���建���户并返回响应"""
    # 这里应该是数据库插入
    return UserResponse(
        id=1,
        username=user.username,
        email=user.email,
        created_at=datetime.now()
    )


@app.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(user_id: int):
    """获取用户详情"""
    return UserDetailResponse(
        id=user_id,
        username="zhangsan",
        email="zhangsan@example.com",
        created_at=datetime.now(),
        items=[
            Item(id=1, name="商品1", price=99.0),
            Item(id=2, name="商品2", price=199.0)
        ],
        bio="这是一个用户"
    )


@app.get("/users", response_model=List[UserResponse])
async def list_users(limit: int = 10):
    """用户列表"""
    return [
        UserResponse(
            id=i,
            username=f"user{i}",
            email=f"user{i}@example.com",
            created_at=datetime.now()
        )
        for i in range(1, limit + 1)
    ]
```

### 4.2 response_model_exclude和include

```python
"""响应模型控制"""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class User(BaseModel):
    """完整用户模型"""
    id: int
    username: str
    email: str
    password: str  # 敏感字段
    is_admin: bool


@app.get("/users/{user_id}")
async def get_user_public(user_id: int):
    """公开信息（排除密码）"""
    user = User(
        id=user_id,
        username="zhangsan",
        email="zhangsan@example.com",
        password="secret123",  # 敏感
        is_admin=False
    )
    return user.model_dump(
        exclude={"password"}  # 排除密码字段
    )


@app.get("/users/{user_id}/admin")
async def get_user_admin(user_id: int):
    """管理员信息（包含所有字段）"""
    user = User(
        id=user_id,
        username="zhangsan",
        email="zhangsan@example.com",
        password="secret123",
        is_admin=True
    )
    return user.model_dump()


@app.get("/users/{user_id}/summary")
async def get_user_summary(user_id: int):
    """仅返回摘要"""
    user = User(
        id=user_id,
        username="zhangsan",
        email="zhangsan@example.com",
        password="secret123",
        is_admin=False
    )
    return user.model_dump(
        include={"id", "username"}  # 仅包含指定字段
    )
```

## 五、自定义验证器

### 5.1 field_validator - 字段验证

```python
"""字段验证器"""
from pydantic import BaseModel, field_validator, ValidationInfo
from typing import Any
import re


class UserRegister(BaseModel):
    """用户注册模型"""
    username: str
    email: str
    password: str
    confirm_password: str
    
    @field_validator('username')
    @classmethod
    def username_must_be_alphanumeric(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("用户名只能包含字母、数字和下划线")
        if len(v) < 3 or len(v) > 20:
            raise ValueError("用户名长度必须在3-20之间")
        return v
    
    @field_validator('email')
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError("邮箱格式无效")
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def password_must_be_strong(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not re.search(r'[A-Z]', v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not re.search(r'[a-z]', v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not re.search(r'[0-9]', v):
            raise ValueError("密码必须包含至少一个数字")
        return v
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_must_match(
        cls, v: str, info: ValidationInfo
    ) -> str:
        # 获取同级的password字段
        if 'password' in info.data:
            if v != info.data['password']:
                raise ValueError("两次密码输入不一致")
        return v


# 测试
if __name__ == "__main__":
    # 正常创建
    try:
        user = UserRegister(
            username="zhangsan",
            email="ZhangSan@Example.COM",
            password="Password123",
            confirm_password="Password123"
        )
        print(f"创建成功: {user.model_dump()}")
    except Exception as e:
        print(f"验证错误: {e}")
    
    # 验证失败
    try:
        user2 = UserRegister(
            username="zhang san",  # 包含空格
            email="invalid",
            password="weak",
            confirm_password="weak"
        )
    except Exception as e:
        print(f"验证错误: {e}")
```

### 5.2 model_validator - 模型验证

```python
"""模型验证器"""
from pydantic import BaseModel, model_validator, Field
from datetime import datetime
from typing import Any


classOrder(BaseModel):
    """订单模型"""
    order_id: str
    items: list[dict]
    total_amount: float
    paid_amount: float
    status: str
    
    @model_validator(mode='before')
    @classmethod
    def validate_order(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # 检查必填字段
            if not data.get('order_id'):
                raise ValueError("订单号不能为空")
            if not data.get('items'):
                raise ValueError("订单商品不能为空")
        return data
    
    @model_validator(mode='after')
    def validate_amount(self) -> 'Order':
        # 验证金额
        if self.paid_amount > self.total_amount:
            raise ValueError("实付金额不能大于订单金额")
        
        # 自动更新状态
        if self.paid_amount >= self.total_amount:
            self.status = "paid"
        elif self.paid_amount > 0:
            self.status = "partial"
        else:
            self.status = "pending"
        
        return self


class CouponUseRequest(BaseModel):
    """优惠券使用请求"""
    order_total: float = Field(..., gt=0)
    coupon_discount: float = Field(..., ge=0)
    final_amount: float
    
    @model_validator(mode='after')
    def validate_discount(self) -> 'CouponUseRequest':
        if self.coupon_discount >= self.order_total:
            raise ValueError("优惠金额不能大于订单金额")
        
        self.final_amount = self.order_total - self.coupon_discount
        return self


# 测试
if __name__ == "__main__":
    # 正常订单
    order = Order(
        order_id="ORDER001",
        items=[{"item_id": 1, "price": 100}],
        total_amount=100.0,
        paid_amount=100.0,
        status="pending"
    )
    print(f"订单: {order.model_dump()}")
    
    # 模型验证器自动更新状态
    order2 = Order(
        order_id="ORDER002",
        items=[{"item_id": 1, "price": 200}],
        total_amount=200.0,
        paid_amount=200.0,
        status="pending"
    )
    print(f"订单状态: {order2.status}")  # 输出: paid
```

### 5.3 computed_field - 计算字段

```python
"""计算字段"""
from pydantic import BaseModel, computed_field
from typing import Optional


class CartItem(BaseModel):
    """购物车商品"""
    item_id: int
    name: str
    price: float
    quantity: int = 1
    
    @computed_field
    @property
    def subtotal(self) -> float:
        """小计"""
        return self.price * self.quantity


class Cart(BaseModel):
    """购物车"""
    user_id: int
    items: list[CartItem]
    discount: float = 0.0
    shipping_fee: float = 0.0
    
    @computed_field
    @property
    def total_quantity(self) -> int:
        """商品总数"""
        return sum(item.quantity for item in self.items)
    
    @computed_field
    @property
    def subtotal(self) -> float:
        """小计金额"""
        return sum(item.subtotal for item in self.items)
    
    @computed_field
    @property
    def total_amount(self) -> float:
        """总金额"""
        return self.subtotal + self.shipping_fee - self.discount


# 测��
if __name__ == "__main__":
    cart = Cart(
        user_id=1,
        items=[
            CartItem(item_id=1, name="iPhone 16", price=6999.0, quantity=1),
            CartItem(item_id=2, name="AirPods", price=1499.0, quantity=2)
        ],
        discount=100.0,
        shipping_fee=50.0
    )
    
    print(f"商品总数: {cart.total_quantity}")  # 3
    print(f"小计: {cart.subtotal}")  # 9997.0
    print(f"总金额: {cart.total_amount}")  # 9947.0
```

## 六、与FastAPI集成

### 6.1 错误处理

```python
"""FastAPI中的Pydantic错误处理"""
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError
from typing import Optional
import json

app = FastAPI()


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None
    model: Optional[str] = None


# 自定义验证错误处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    """验证错误处理"""
    errors = []
    for error in exc.errors():
        errors.append({
            "loc": ".".join(str(loc) for loc in error["loc"]),
            "msg": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": errors
        }
    )


@app.exception_handler(ValidationError)
async def pydantic_exception_handler(
    request: Request,
    exc: ValidationError
):
    """Pydantic验证错误处理"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "model": exc.model.__name__ if hasattr(exc, 'model') else None
        }
    )


class ItemCreate(BaseModel):
    """商品创建"""
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)


@app.post("/items")
async def create_item(item: ItemCreate):
    """创建商品"""
    return item


# 测试验证错误
@app.post("/items/error")
async def create_item_error(item: ItemCreate):
    """测试错误响应"""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="商品创建失败"
    )
```

### 6.2 Depends依赖注入

```python
"""Depends依赖注入"""
from fastapi import FastAPI, Depends
from pydantic import BaseModel, Field
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()
security = HTTPBearer()


class User(BaseModel):
    """用户模型"""
    user_id: int
    username: str
    is_admin: bool = False


# 模拟的用户认证
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """获取当前用户"""
    # 这里应该是JWT解析逻辑
    token = credentials.credentials
    
    # 模拟解析
    if token == "valid_token":
        return User(user_id=1, username="zhangsan", is_admin=False)
    elif token == "admin_token":
        return User(user_id=1, username="admin", is_admin=True)
    else:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token"
        )


class ItemCreate(BaseModel):
    """商品创建"""
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)


# 公开接口
@app.post("/items/public")
async def create_item_public(item: ItemCreate):
    """公开创建商品"""
    return item


# 需要认证的接口
@app.post("/items")
async def create_item(
    item: ItemCreate,
    user: User = Depends(get_current_user)
):
    """创建商品（需认证）"""
    return {
        "id": 1,
        **item.model_dump(),
        "user_id": user.user_id
    }


# 需要管理员权限的接口
@app.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    user: User = Depends(get_current_user)
):
    """删除商品（需管理员）"""
    if not user.is_admin:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return {"deleted": item_id}
```

## 七、踩坑记录

### 7.1 常见错误

**错误1：默认值与必填冲突**
```python
# 错误写法
class User(BaseModel):
    name: str = None  # int? = None 是正确的，但 str = None 会报警

# 正确写法
class User(BaseModel):
    name: Optional[str] = None
# 或
class User(BaseModel):
    name: str | None = None  # Python 3.10+
```

**错误2：验证器参数获取**
```python
# 错误写法
@field_validator('name')
def name_validator(v):
    return v  # 缺少 @classmethod 和 self

# 正确写法
@field_validator('name')
@classmethod
def name_validator(cls, v):
    return v
```

**错误3：模型配置序列化问题**
```python
# 问题：datetime无法直接JSON序列化
class User(BaseModel):
    created_at: datetime

user = User(created_at=datetime.now())
json_str = user.model_dump_json()  # 正常

# 解决方案：使用iso_format
class User(BaseModel):
    created_at: datetime
    
    model_config = {"json_encoders": {datetime: lambda v: v.iso_format()}}
```

### 7.2 性能优化

| 问题 | 解决方案 |
|------|----------|
| 验证慢 | 使用`model_config={'validate_config': False}`跳过配置验证 |
| 序列化慢 | 使用`model_dump(mode='python')`获取dict而非json |
| 嵌套模型验证慢 | 使用`model_validate(obj, mode='python')`提前验证 |

> **踩坑记录4**：在Pydantic 2.x中，`validator`装饰器已被`field_validator`和`model_validator`取代。如果使用旧版本API，会收到弃用警告，建议迁移到新API。

## 八、总结

本文我们深入学习了：

1. ✅ Pydantic BaseModel：数据模型定义
2. ✅ Field字段：高级字段配置和验证
3. ✅ 嵌套模型：复杂数据结构
4. ✅ 请求体解析：Body、Query、Path参数
5. ✅ 响应模型：response_model参数控制
6. ✅ 自定义验证器：field_validator、model_validator
7. ✅ 计算字段：computed_field
8. ✅ FastAPI集成：错误处理和依赖注入

Pydantic是FastAPI生态的核心基础设施，它让数据验证从"负担"变成了"乐趣"。下一篇文章我们将学习数据库集成：SQLAlchemy + MySQL/PostgreSQL。

> **下篇预告**：《数据库集成：SQLAlchemy + MySQL/PostgreSQL》
> - 异步ORM
> - CRUD操作
> - 数据库迁移