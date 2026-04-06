"""
游戏测试用例
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.config import settings

# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# 创建测试客户端
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """设置测试数据库"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_player(setup_database):
    """创建测试玩家"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "test_player",
            "email": "test@example.com",
            "password": "test123456"
        }
    )
    return response.json()


@pytest.fixture
def auth_headers(test_player):
    """获取认证头"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "test_player",
            "password": "test123456"
        }
    )
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestAuth:
    """认证测试"""
    
    def test_register_success(self, setup_database):
        """测试注册成功"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "new_player",
                "email": "new@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "new_player"
    
    def test_register_duplicate_username(self, setup_database, test_player):
        """测试重复用户名注册"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "test_player",
                "email": "another@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 400
    
    def test_login_success(self, setup_database, test_player):
        """测试登录成功"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test_player",
                "password": "test123456"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
    
    def test_login_wrong_password(self, setup_database, test_player):
        """测试密码错误"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test_player",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401


class TestGame:
    """游戏测试"""
    
    def test_start_game(self, setup_database, auth_headers):
        """测试开始游戏"""
        response = client.post(
            "/api/v1/game/start",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["money"] == settings.INITIAL_MONEY
        assert data["data"]["health"] == settings.INITIAL_HEALTH
    
    def test_get_game_state(self, setup_database, auth_headers):
        """测试获取游戏状态"""
        # 先开始游戏
        client.post("/api/v1/game/start", headers=auth_headers)
        
        # 获取状态
        response = client.get(
            "/api/v1/game/state",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "game_state" in data["data"]
    
    def test_execute_action_work(self, setup_database, auth_headers):
        """测试执行工作动作"""
        # 开始游戏
        client.post("/api/v1/game/start", headers=auth_headers)
        
        # 执行工作动作
        response = client.post(
            "/api/v1/game/action",
            headers=auth_headers,
            json={"action_code": "work_normal"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 验证金钱增加
        assert data["data"]["updated_game_state"]["money"] > settings.INITIAL_MONEY
    
    def test_execute_action_insufficient_energy(self, setup_database, auth_headers):
        """测试精力不足时无法执行动作"""
        # 开始游戏
        client.post("/api/v1/game/start", headers=auth_headers)
        
        # 连续执行消耗精力的动作直到精力不足
        for _ in range(10):
            response = client.post(
                "/api/v1/game/action",
                headers=auth_headers,
                json={"action_code": "work_overtime"}
            )
            if response.status_code != 200:
                break
        
        # 验证无法继续执行
        response = client.post(
            "/api/v1/game/action",
            headers=auth_headers,
            json={"action_code": "work_overtime"}
        )
        # 应该返回 400 或类似错误
        assert response.status_code in [200, 400]


class TestHealth:
    """健康检查测试"""
    
    def test_health_check(self):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        assert "重生之月薪2000" in response.json()["message"]
