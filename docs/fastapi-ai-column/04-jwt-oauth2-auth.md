# 认证与权限：JWT + OAuth2完整实现

> **文章信息**  
> - 标题：认证与权限：JWT + OAuth2完整实现  
> - 字数：4500字  
> - 预估阅读时间：20分钟  
> - 难度：⭐⭐⭐☆☆

---

## 一、为什么需要认证？

在AI应用开发中，API安全性至关重要。根据OWASP Top 10（2023），身份验证相关漏洞排名前三。对于FastAPI应用，你需要：

1. **用户身份识别**：知道请求来自哪个用户
2. **会话管理**：无状态的JWT比session更易扩展
3. **权限控制**：不同用户有不同操作权限
4. **API安全**：防止未授权访问

本文将带你实现完整的JWT认证系统，包括登录、受保护路由、Token刷新和RBAC权限控制。

## 二、环境准备

### 2.1 安装依赖

```bash
# 安装认证相关库
uv pip install python-jose[cryptography] passlib[bcrypt] python-multipart

# python-jose: JWT编码/解码
# passlib: 密码哈希
# python-multipart: 文件上传（FastAPI内置）

# 验证安装
python -c "from jose import jwt; print(jwt.__version__)"
```

### 2.2 密码哈希对比

| 算法 | 速度 | 安全性 | 内存占用 | 推荐场景 |
|------|------|--------|----------|----------|
| bcrypt | 中等 | ★★★★★ | 128MB | 生产环境首选 |
| argon2 | 慢 | ★★★★★ | 可配置 | 高安全场景 |
| scrypt | 慢 | ★★★★☆ | 可配置 | 兼容旧系统 |
| PBKDF2 | 中等 | ★★★☆☆ | 固定 | 兼容旧系统 |

> **推荐**：bcrypt是当前最佳平衡，argon2是未来趋势。

## 三、配置与模型

### 3.1 配置

创建`app/config.py`：

```python
"""认证配置"""
from pydantic_settings import BaseSettings
from typing import Optional
from datetime import timedelta


class AuthSettings(BaseSettings):
    """认证配置"""
    
    # JWT配置
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30  # 访问令牌30分钟
    jwt_refresh_token_expire_days: int = 7   # 刷新令牌7天
    
    # OAuth2配置
    oauth2_scheme_name: str = "bearer"
    
    # 密码配置
    password_min_length: int = 6
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


auth_settings = AuthSettings()
```

### 3.2 用户模型

```python
"""认证相关模型"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """用户角色"""
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


# Token模型
class Token(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Token载荷"""
    sub: str  # 用户ID
    exp: int  # 过期时间
    type: str = "access"  # token类型


class TokenRefreshRequest(BaseModel):
    """Token刷新请求"""
    refresh_token: str


# 登录请求
class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


# 用户创建请求（带角色）
class UserCreate(BaseModel):
    """用户创建请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.USER
```

### 3.3 密码���希工具

```python
"""密码工具"""
from passlib.context import CryptContext

# 密码上下文（bcrypt）
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


# 测试
if __name__ == "__main__":
    password = "Password123"
    hashed = hash_password(password)
    print(f"哈希后: {hashed}")
    print(f"验证成功: {verify_password(password, hashed)}")
    print(f"验证失败: {verify_password('wrong', hashed)}")
```

## 四、JWT令牌

### 4.1 令牌创建

```python
"""JWT令牌创建"""
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
from app.config import auth_settings


def create_access_token(
    user_id: int,
    username: str,
    role: str = "user",
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=auth_settings.jwt_access_token_expire_minutes
        )
    
    to_encode = {
        "sub": str(user_id),  # 用户ID
        "username": username,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        auth_settings.jwt_secret_key,
        algorithm=auth_settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(user_id: int) -> str:
    """创建刷新令牌"""
    expire = datetime.utcnow() + timedelta(
        days=auth_settings.jwt_refresh_token_expire_days
    )
    
    to_encode = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        auth_settings.jwt_secret_key,
        algorithm=auth_settings.jwt_algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """解码令牌"""
    try:
        payload = jwt.decode(
            token,
            auth_settings.jwt_secret_key,
            algorithms=[auth_settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        raise ValueError(f"令牌解析失败: {str(e)}")


def verify_token_type(token: str, expected_type: str) -> bool:
    """验证令牌类型"""
    try:
        payload = decode_token(token)
        return payload.get("type") == expected_type
    except ValueError:
        return False
```

### 4.2 令牌验证

```python
"""令牌验证和刷新"""
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from app.config import auth_settings


def verify_access_token(token: str) -> dict:
    """验证访问令牌"""
    try:
        payload = jwt.decode(
            token,
            auth_settings.jwt_secret_key,
            algorithms=[auth_settings.jwt_algorithm],
            options={"verify_exp": True}
        )
        
        # 验证类型
        if payload.get("type") != "access":
            raise ValueError("无效的token类型")
        
        return payload
    
    except ExpiredSignatureError:
        raise ValueError("令牌已过���")
    except JWTError as e:
        raise ValueError(f"令牌验证失败: {str(e)}")


def refresh_access_token(refresh_token: str) -> dict:
    """使用刷新令牌获取新的访问令牌"""
    try:
        payload = jwt.decode(
            refresh_token,
            auth_settings.jwt_secret_key,
            algorithms=[auth_settings.jwt_algorithm],
            options={"verify_exp": True}
        )
        
        # 验证类型
        if payload.get("type") != "refresh":
            raise ValueError("无效的刷新令牌")
        
        return {
            "user_id": int(payload.get("sub")),
            "type": "refresh"
        }
    
    except ExpiredSignatureError:
        raise ValueError("刷新令牌已过期")
    except JWTError as e:
        raise ValueError(f"刷新令牌验证失败: {str(e)}")
```

## 五、OAuth2认证

### 5.1 FastAPI安全依赖

```python
"""OAuth2依赖"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError, ExpiredSignatureError
from typing import Optional

from app.database import get_db
from app.config import auth_settings
from app.models.user import User
from app.crud import user as crud_user


# OAuth2 Bearer方案
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    scheme_name=auth_settings.oauth2_scheme_name,
    auto_error=False,
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户（必须登录）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(
            token,
            auth_settings.jwt_secret_key,
            algorithms=[auth_settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (JWTError, ExpiredSignatureError):
        raise credentials_exception
    
    user = await crud_user.get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选）"""
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token,
            auth_settings.jwt_secret_key,
            algorithms=[auth_settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except (JWTError, ExpiredSignatureError):
        return None
    
    return await crud_user.get_user_by_id(db, int(user_id))
```

### 5.2 角色验证

```python
"""角色验证"""
from fastapi import Depends, HTTPException, status
from functools import wraps
from typing import Callable
from app.models.user import User
from app.schemas.user import UserRole


def require_role(*allowed_roles: UserRole):
    """角色验证装饰器"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不��"
            )
        return current_user
    
    return role_checker


# 使用示例
# @router.delete("/users/{user_id}")
# @require_role(UserRole.ADMIN)
# async def delete_user(user_id: int, ...):
#     ...
```

### 5.3 权限控制守卫

```python
"""权限守卫"""
from fastapi import Depends, HTTPException, status
from typing import List
from app.models.user import User


class Permission:
    """权限定义"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


# 角色权限映射
ROLE_PERMISSIONS = {
    UserRole.USER: [Permission.READ],
    UserRole.MODERATOR: [Permission.READ, Permission.WRITE],
    UserRole.ADMIN: [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN],
}


def check_permission(user: User, permission: str) -> bool:
    """检查用户权限"""
    if user.is_admin:
        return True
    
    role_perms = ROLE_PERMISSIONS.get(user.role, [])
    return permission in role_perms


def require_permission(permission: str):
    """权限验证装饰器"""
    def permission_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 '{permission}' 权限"
            )
        return current_user
    
    return permission_checker


# 使用示例
# @router.post("/items")
# @require_permission(Permission.WRITE)
# async def create_item(...):
#     ...
```

## 六、登录接口

### 6.1 认证路由

创建`app/routers/auth.py`：

```python
"""认证路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.database import get_db
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.auth import (
    Token,
    LoginRequest,
    UserCreate,
    UserResponse,
    TokenRefreshRequest,
)
from app.utils.auth import (
    hash_password,
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_access_token,
    refresh_access_token,
)
from app.config import auth_settings

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    # 检查用户名
    existing = await crud_user.get_user_by_username(db, user_create.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱
    existing = await crud_user.get_user_by_email(db, user_create.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    # 创建用户
    user_data = user_create.model_dump()
    user_data["password"] = hash_password(user_data.pop("password"))
    user_data["role"] = user_create.role.value
    
    db_user = User(**user_data)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """用户登录（OAuth2表单）"""
    # 获取用户
    user = await crud_user.get_user_by_username(db, form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证密码
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    # 创建令牌
    access_token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role.value if hasattr(user, 'role') else "user"
    )
    refresh_token = create_refresh_token(user.id)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=auth_settings.jwt_access_token_expire_minutes * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """刷新Token"""
    # 验证刷新令牌
    result = refresh_access_token(request.refresh_token)
    user_id = result["user_id"]
    
    # 获取用户
    user = await crud_user.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的用户"
        )
    
    # 创建新令牌
    access_token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role.value if hasattr(user, 'role') else "user"
    )
    new_refresh_token = create_refresh_token(user.id)
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=auth_settings.jwt_access_token_expire_minutes * 60
    )


@router.post("/logout")
async def logout():
    """登出（客户端删除token即可，服务端无需处理）"""
    return {"message": "成功登出"}
```

## 七、受保护路由

### 7.1 用户路由

```python
"""受保护的路由示例"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.crud import user as crud_user
from app.crud import item as crud_item
from app.models.user import User
from app.schemas.user import UserResponse, ItemResponse, ItemCreate, ItemUpdate
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api", tags=["API"])


@router.get("/users/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return current_user


@router.get("/items", response_model=list[ItemResponse])
async def list_my_items(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取我的商品列表"""
    return await crud_item.get_items(db, owner_id=current_user.id)


@router.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_my_item(
    item: ItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建商品"""
    return await crud_item.create_item(db, item, current_user.id)


@router.patch("/items/{item_id}", response_model=ItemResponse)
async def update_my_item(
    item_id: int,
    item_update: ItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新商品"""
    item = await crud_item.get_item_by_id(db, item_id)
    if not item or item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    return await crud_item.update_item(db, item_id, item_update)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除商品"""
    item = await crud_item.get_item_by_id(db, item_id)
    if not item or item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    await crud_item.delete_item(db, item_id)
    return None
```

### 7.2 管理员路由

```python
"""管理员路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.user import UserRole
from app.utils.auth import get_current_user
from app.utils.auth import require_role

router = APIRouter(prefix="/admin", tags=["管理员"])


@router.get("/users", response_model=list[UserResponse])
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """用户列表（管理员）"""
    # 验证角色
    if current_user.role != UserRole.ADMIN and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return await crud_user.get_users(db, skip=skip, limit=limit)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除用户（管理员）"""
    if current_user.role != UserRole.ADMIN and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    success = await crud_user.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return None


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: int,
    role: UserRole,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """修改用户角色（管理员）"""
    if current_user.role != UserRole.ADMIN and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    user = await crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user.role = role.value
    await db.commit()
    await db.refresh(user)
    return user
```

## 八、Token刷新机制

### 8.1 自动刷新

```python
"""自动刷新中间件"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time


class TokenRefreshMiddleware(BaseHTTPMiddleware):
    """Token刷新中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        # 检查token是否即将过期（在响应头中添加）
        # 客户端可以根据此信息决定是否刷新
        response.headers["X-Token-Type"] = "bearer"
        
        return response
```

### 8.2 客户端刷新

```javascript
// 前端刷新技术
class AuthClient {
  constructor() {
    this.accessToken = null;
    this.refreshToken = null;
  }
  
  async refreshToken() {
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh_token: this.refreshToken
      })
    });
    
    if (!response.ok) {
      // 刷新失败，需要重新登录
      this.logout();
      return false;
    }
    
    const data = await response.json();
    this.accessToken = data.access_token;
    this.refreshToken = data.refresh_token;
    return true;
  }
  
  async request(url, options = {}) {
    // 自动刷新逻辑
    if (this.isTokenExpiringSoon()) {
      await this.refreshToken();
    }
    
    // 添加token到请求
    options.headers = {
      ...options.headers,
      'Authorization': `Bearer ${this.accessToken}`
    };
    
    return fetch(url, options);
  }
  
  isTokenExpiringSoon() {
    // 检查token是否将在5分钟内过期
    // 需要解码token检查exp声明
    return true;
  }
}
```

## 九、踩坑记录

### 9.1 常见错误

**错误1：JWT过期时间验证**
```python
# 错误写法（过期的验证方式）
payload = jwt.decode(token, key, algorithms=["HS256"])
# 没有verify_exp选项

# 正确写法
payload = jwt.decode(
    token,
    key,
    algorithms=["HS256"],
    options={"verify_exp": True}  # 显式验证过期
)
```

**错误2：密码哈希**
```python
# 错误写法（不安全）
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()  # 不安全，可被破解

# 正确写法（使用bcrypt）
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password_hash = pwd_context.hash(password)
```

**错误3：Token类型混淆**
```python
# 错误写法
def create_token(user_id):
    return jwt.encode({"sub": str(user_id), ...})  # 没有type

# 正确写法
def create_access_token(user_id):
    return jwt.encode({"sub": str(user_id), "type": "access", ...})

def create_refresh_token(user_id):
    return jwt.encode({"sub": str(user_id), "type": "refresh", ...})
```

### 9.2 安全建议

| 问题 | 解决方案 |
|------|----------|
| Token泄露 | 使用HTTPS，设置短过期时间 |
| CSRF攻击 | 使用SameSite Cookie |
| XSS攻击 | 设置HttpOnly Cookie |
| 重放攻击 | 使用nonce/一次性token |
| 密码暴力破解 | 限流+验证码 |

> **踩坑记录6**：生产环境中，JWT密钥必须使用环境变量或密钥管理系统（AWS Secrets Manager、HashiCorp Vault），不能硬编码！

## 十、总结

本文我们完成了：

1. ✅ JWT令牌创建和解码
2. ✅ OAuth2认证流程
3. ✅ 密码哈希和验证
4. ✅ 受保护路由实现
5. ✅ Token刷新机制
6. ✅ RBAC权限控制
7. ✅ 角色验证装饰器

一套完整的认证系统是AI应用的基础。下一篇文章我们将学习如何调用DeepSeek API搭建智能助手。

> **下篇预告**：《用FastAPI调用DeepSeek API搭智能助手》
> - 流式输出
> - 多轮对话
> - 价格优化