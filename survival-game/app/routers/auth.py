"""
认证路由
处理用户注册、登录、令牌刷新等
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.crud.player import crud_player
from app.database import get_db
from app.models.player import PlayerCreate, Player, Token

router = APIRouter()

# OAuth2 配置
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

# JWT 工具函数
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_player(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取当前认证玩家"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_type: str = payload.get("type")
        if token_type == "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    player = crud_player.get(db, int(user_id))
    if player is None:
        raise credentials_exception
    return player


async def get_current_active_player(
    current_player = Depends(get_current_player)
):
    """获取当前活跃玩家"""
    if not current_player.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_player


# 路由
@router.post("/register", response_model=Player, status_code=status.HTTP_201_CREATED)
async def register(
    player_in: PlayerCreate,
    db: Session = Depends(get_db)
):
    """用户注册"""
    # 检查用户名是否已存在
    db_player = crud_player.get_by_username(db, username=player_in.username)
    if db_player:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    if player_in.email:
        db_player = crud_player.get_by_email(db, email=player_in.email)
        if db_player:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )

    # 创建用户
    player = crud_player.create(db, player_in)
    return player


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    player = crud_player.authenticate(db, form_data.username, form_data.password)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not player.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")

    # 更新最后登录时间
    crud_player.update_last_login(db, player)

    # 创建令牌
    access_token = create_access_token(data={"sub": str(player.id)})
    refresh_token = create_refresh_token(data={"sub": str(player.id)})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """刷新访问令牌"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="刷新令牌无效",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    player = crud_player.get(db, int(user_id))
    if player is None or not player.is_active:
        raise credentials_exception

    # 创建新令牌
    access_token = create_access_token(data={"sub": str(player.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(player.id)})

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=Player)
async def read_players_me(
    current_player = Depends(get_current_active_player)
):
    """获取当前用户信息"""
    return current_player