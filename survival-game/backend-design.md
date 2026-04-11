# 《重生之月薪2000》后端系统详细设计文档

> 版本：v1.0
> 日期：2026-04-06
> 作者：AI Assistant
> 技术栈：Python 3.10+ + FastAPI + SQLite/PostgreSQL

---

## 目录
1. [系统架构详细设计](#系统架构详细设计)
2. [数据库表结构设计](#数据库表结构设计)
3. [API 接口详细设计](#api-接口详细设计)
4. [核心类设计](#核心类设计)
5. [游戏引擎流程设计](#游戏引擎流程设计)
6. [事件系统设计](#事件系统设计)
7. [技术选型说明](#技术选型说明)
8. [部署与运维](#部署与运维)

---

## 系统架构详细设计

### 1.1 总体架构

系统采用分层架构，分为展示层、应用层、领域层和数据层：

```
┌─────────────────────────────────────────────────────────┐
│                   展示层 (Presentation Layer)            │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Web 前端 (HTML/CSS/JS)              │   │
│  └───────────────────────┬─────────────────────────┘   │
└──────────────────────────┼──────────────────────────────┘
                           │ HTTP/JSON + WebSocket
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   应用层 (Application Layer)             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐         │
│  │   Auth     │ │    Game    │ │  Events    │         │
│  │ Controller │ │ Controller │ │ Controller │         │
│  └────────────┘ └────────────┘ └────────────┘         │
│                                                        │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐         │
│  │  Player    │ │  Action    │ │  Ending    │         │
│  │  Service   │ │  Service   │ │  Service   │         │
│  └────────────┘ └────────────┘ └────────────┘         │
└──────────────────────────┼──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   领域层 (Domain Layer)                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │         游戏引擎 (Game Engine)                   │   │
│  │  • 游戏状态管理                                 │   │
│  │  • 资源计算                                     │   │
│  │  • 条件检查                                     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │         事件引擎 (Event Engine)                  │   │
│  │  • 事件触发                                     │   │
│  │  • 选择处理                                     │   │
│  │  • 随机事件生成                                 │   │
│  └─────────────────────────────────────────────────┘   │
└──────────────────────────┼──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   数据层 (Data Layer)                   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐         │
│  │   Player   │ │    Game    │ │   Event    │         │
│  │ Repository │ │ Repository │ │ Repository │         │
│  └────────────┘ └────────────┘ └────────────┘         │
│                                                        │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐         │
│  │   Action   │ │  Ending    │ │  Leader-    │         │
│  │ Repository │ │ Repository │ │  board Repo │         │
│  └────────────┘ └────────────┘ └────────────┘         │
└──────────────────────────┼──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   数据存储 (Data Storage)                │
│  ┌─────────────────────────────────────────────────┐   │
│  │        SQLite (开发) / PostgreSQL (生产)         │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Redis (缓存，可选)                       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

#### 1.2.1 核心模块

1. **认证模块 (Auth)**
   - 玩家注册/登录
   - JWT Token 管理
   - 会话管理

2. **游戏模块 (Game)**
   - 游戏状态管理
   - 资源计算与更新
   - 行动执行与验证
   - 结局判断

3. **事件模块 (Events)**
   - 事件池管理
   - 事件触发逻辑
   - 选择处理与影响计算

4. **数据模块 (Data)**
   - 玩家数据持久化
   - 游戏存档管理
   - 排行榜数据

#### 1.2.2 支持模块

1. **配置模块 (Config)**
   - 环境变量管理
   - 数据库配置
   - 游戏参数配置

2. **工具模块 (Utils)**
   - 数值计算工具
   - 随机数生成
   - 日志记录

3. **缓存模块 (Cache)**
   - Redis 缓存管理
   - 热点数据缓存
   - 会话缓存

### 1.3 通信方式

- **HTTP/JSON**: 用于所有 RESTful API 通信
- **WebSocket (可选)**: 用于实时游戏状态更新
- **消息队列 (可选)**: 用于异步事件处理，提高性能

### 1.4 安全性设计

1. **认证授权**: JWT + 访问令牌
2. **数据验证**: Pydantic 模型验证所有输入
3. **SQL 注入防护**: ORM/SQLAlchemy 参数化查询
4. **XSS 防护**: 输出转义
5. **速率限制**: API 请求频率限制
6. **敏感数据加密**: 密码等敏感信息加密存储

---

## 数据库表结构设计

### 2.1 表清单

| 表名 | 说明 |
|------|------|
| players | 玩家账户信息 |
| game_states | 游戏状态（每个玩家的当前游戏数据） |
| events | 事件定义（静态事件库） |
| event_choices | 事件选择项定义 |
| actions | 可执行动作定义 |
| player_actions | 玩家动作执行记录 |
| endings | 游戏结局定义 |
| player_endings | 玩家达成的结局记录 |
| leaderboard | 排行榜数据 |

### 2.2 DDL SQL 语句

以下为 SQLite 兼容的 DDL 语句，PostgreSQL 版本仅需调整自增语法。

```sql
-- 玩家账户表
CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt 加密存储
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    total_games_played INTEGER DEFAULT 0,
    best_score INTEGER DEFAULT 0
);

-- 游戏状态表（每个玩家当前游戏）
CREATE TABLE game_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    day INTEGER DEFAULT 1,                -- 当前天数 (1-30)
    time_of_day VARCHAR(10) DEFAULT 'morning', -- morning, afternoon, evening, night
    money INTEGER DEFAULT 2000,           -- 当前资金
    health INTEGER DEFAULT 100,           -- 健康值 (0-100)
    stress INTEGER DEFAULT 0,             -- 压力值 (0-100)
    hunger INTEGER DEFAULT 0,             -- 饥饿值 (0-100)
    energy INTEGER DEFAULT 100,           -- 精力值 (0-100)
    job_level INTEGER DEFAULT 1,          -- 工作等级
    job_satisfaction INTEGER DEFAULT 50,  -- 工作满意度
    relationship INTEGER DEFAULT 50,      -- 人际关系
    is_game_over BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

-- 事件定义表
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_code VARCHAR(50) UNIQUE NOT NULL,   -- 事件唯一标识
    title VARCHAR(200) NOT NULL,              -- 事件标题
    description TEXT NOT NULL,                 -- 事件描述
    trigger_type VARCHAR(20) NOT NULL,        -- 触发类型：daily, random, conditional
    trigger_condition TEXT,                    -- 触发条件 (JSON)
    min_day INTEGER DEFAULT 1,                -- 最小触发天数
    max_day INTEGER DEFAULT 30,               -- 最大触发天数
    weight INTEGER DEFAULT 10,                -- 随机权重
    is_active BOOLEAN DEFAULT TRUE
);

-- 事件选择项表
CREATE TABLE event_choices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    choice_text VARCHAR(500) NOT NULL,        -- 选择项文本
    effect_money INTEGER DEFAULT 0,           -- 金钱影响
    effect_health INTEGER DEFAULT 0,          -- 健康影响
    effect_stress INTEGER DEFAULT 0,          -- 压力影响
    effect_hunger INTEGER DEFAULT 0,          -- 饥饿影响
    effect_energy INTEGER DEFAULT 0,          -- 精力影响
    effect_job_satisfaction INTEGER DEFAULT 0,-- 工作满意度影响
    effect_relationship INTEGER DEFAULT 0,    -- 人际关系影响
    next_event_id INTEGER,                     -- 触发的下一个事件
    is_ending_trigger BOOLEAN DEFAULT FALSE,  -- 是否触发结局
    ending_id INTEGER,                         -- 关联的结局ID
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (next_event_id) REFERENCES events(id),
    FOREIGN KEY (ending_id) REFERENCES endings(id)
);

-- 动作定义表
CREATE TABLE actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_code VARCHAR(50) UNIQUE NOT NULL,  -- 动作唯一标识
    name VARCHAR(100) NOT NULL,               -- 动作名称
    description TEXT,                          -- 动作描述
    cost_money INTEGER DEFAULT 0,             -- 金钱消耗
    cost_energy INTEGER DEFAULT 0,            -- 精力消耗
    effect_health INTEGER DEFAULT 0,          -- 健康影响
    effect_stress INTEGER DEFAULT 0,          -- 压力影响
    effect_hunger INTEGER DEFAULT 0,          -- 饥饿影响
    effect_job_satisfaction INTEGER DEFAULT 0,-- 工作满意度影响
    effect_relationship INTEGER DEFAULT 0,    -- 人际关系影响
    cooldown_hours INTEGER DEFAULT 0,         -- 冷却时间（小时）
    is_available BOOLEAN DEFAULT TRUE
);

-- 玩家动作执行记录表
CREATE TABLE player_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    game_state_id INTEGER NOT NULL,
    action_id INTEGER NOT NULL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cost_money INTEGER,
    cost_energy INTEGER,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (game_state_id) REFERENCES game_states(id) ON DELETE CASCADE,
    FOREIGN KEY (action_id) REFERENCES actions(id)
);

-- 结局定义表
CREATE TABLE endings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ending_code VARCHAR(50) UNIQUE NOT NULL,  -- 结局唯一标识
    title VARCHAR(200) NOT NULL,              -- 结局标题
    description TEXT NOT NULL,                 -- 结局描述
    condition_type VARCHAR(20) NOT NULL,      -- 条件类型：health, money, stress, etc.
    condition_value INTEGER,                   -- 条件数值
    is_bad_ending BOOLEAN DEFAULT FALSE,      -- 是否为坏结局
    score INTEGER DEFAULT 0                   -- 该结局得分
);

-- 玩家结局记录表
CREATE TABLE player_endings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    game_state_id INTEGER NOT NULL,
    ending_id INTEGER NOT NULL,
    achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    score INTEGER DEFAULT 0,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (game_state_id) REFERENCES game_states(id) ON DELETE CASCADE,
    FOREIGN KEY (ending_id) REFERENCES endings(id)
);

-- 排行榜表
CREATE TABLE leaderboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    username VARCHAR(50) NOT NULL,
    ending_id INTEGER NOT NULL,
    ending_title VARCHAR(200) NOT NULL,
    score INTEGER NOT NULL,
    total_days INTEGER NOT NULL,              -- 存活天数
    achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (ending_id) REFERENCES endings(id)
);

-- 索引
CREATE INDEX idx_game_states_player ON game_states(player_id);
CREATE INDEX idx_event_choices_event ON event_choices(event_id);
CREATE INDEX idx_player_actions_player ON player_actions(player_id);
CREATE INDEX idx_player_endings_player ON player_endings(player_id);
CREATE INDEX idx_leaderboard_score ON leaderboard(score DESC);
```

### 2.3 数据关系说明

- **玩家(players)** 与 **游戏状态(game_states)** 为一对多关系（一个玩家可有多个存档，但当前仅一个活跃状态）
- **事件(events)** 与 **事件选择项(event_choices)** 为一对多关系
- **玩家动作记录(player_actions)** 关联玩家、游戏状态和动作定义
- **结局(endings)** 可通过事件选择或状态条件触发
- **排行榜(leaderboard)** 记录玩家达成的结局及得分

---

## API 接口详细设计

### 3.1 接口概览

| 模块 | 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|------|
| 认证 | 注册 | POST | `/api/auth/register` | 玩家注册 |
| 认证 | 登录 | POST | `/api/auth/login` | 玩家登录 |
| 认证 | 登出 | POST | `/api/auth/logout` | 玩家登出 |
| 认证 | 刷新令牌 | POST | `/api/auth/refresh` | 刷新 JWT Token |
| 玩家 | 获取当前玩家 | GET | `/api/players/me` | 获取当前玩家信息 |
| 游戏 | 获取游戏状态 | GET | `/api/game/state` | 获取当前游戏状态 |
| 游戏 | 开始新游戏 | POST | `/api/game/start` | 开始新游戏 |
| 游戏 | 执行动作 | POST | `/api/game/action` | 执行一个动作 |
| 游戏 | 获取可用动作 | GET | `/api/game/available-actions` | 获取当前可执行动作 |
| 事件 | 获取当前事件 | GET | `/api/events/current` | 获取当前触发的事件 |
| 事件 | 处理事件选择 | POST | `/api/events/choose` | 处理事件选择项 |
| 游戏 | 结束游戏 | POST | `/api/game/end` | 主动结束游戏 |
| 数据 | 获取排行榜 | GET | `/api/leaderboard` | 获取排行榜数据 |
| 数据 | 获取玩家结局记录 | GET | `/api/players/endings` | 获取玩家达成的结局 |

### 3.2 请求/响应格式

#### 3.2.1 认证接口

**注册接口**

```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "player1",
  "email": "player1@example.com",
  "password": "securepassword123"
}
```

响应：
```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "id": 1,
    "username": "player1",
    "email": "player1@example.com",
    "created_at": "2026-04-06T10:30:00Z"
  }
}
```

**登录接口**

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "player1",
  "password": "securepassword123"
}
```

响应：
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

#### 3.2.2 游戏接口

**获取游戏状态**

```http
GET /api/game/state
Authorization: Bearer {access_token}
```

响应：
```json
{
  "success": true,
  "data": {
    "game_state": {
      "id": 123,
      "player_id": 1,
      "day": 5,
      "time_of_day": "afternoon",
      "money": 1800,
      "health": 85,
      "stress": 40,
      "hunger": 30,
      "energy": 70,
      "job_level": 1,
      "job_satisfaction": 60,
      "relationship": 55,
      "is_game_over": false,
      "created_at": "2026-04-06T10:30:00Z",
      "updated_at": "2026-04-06T11:45:00Z"
    },
    "player": {
      "id": 1,
      "username": "player1",
      "total_games_played": 3,
      "best_score": 1200
    }
  }
}
```

**执行动作**

```http
POST /api/game/action
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "action_code": "work_overtime"
}
```

响应：
```json
{
  "success": true,
  "message": "动作执行成功",
  "data": {
    "action_result": {
      "action_name": "加班",
      "cost_money": 0,
      "cost_energy": 30,
      "effect_money": 500,
      "effect_stress": 20,
      "effect_job_satisfaction": -5
    },
    "updated_game_state": {
      "money": 2300,
      "stress": 60,
      "energy": 40,
      "job_satisfaction": 55
    }
  }
}
```

#### 3.2.3 事件接口

**获取当前事件**

```http
GET /api/events/current
Authorization: Bearer {access_token}
```

响应：
```json
{
  "success": true,
  "data": {
    "event": {
      "id": 45,
      "event_code": "rent_increase",
      "title": "房租涨价",
      "description": "房东通知下个月房租要涨300元...",
      "choices": [
        {
          "id": 101,
          "choice_text": "接受涨价，继续住",
          "effect_money": -300,
          "effect_stress": 10
        },
        {
          "id": 102,
          "choice_text": "寻找更便宜的房子",
          "effect_money": 0,
          "effect_energy": -20,
          "effect_stress": 5
        },
        {
          "id": 103,
          "choice_text": "和房东谈判",
          "effect_money": -150,
          "effect_stress": -5,
          "effect_relationship": 5
        }
      ]
    }
  }
}
```

**处理事件选择**

```http
POST /api/events/choose
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "choice_id": 102
}
```

响应：
```json
{
  "success": true,
  "message": "选择处理成功",
  "data": {
    "effects": {
      "money": 0,
      "energy": -20,
      "stress": 5
    },
    "next_event": null,
    "triggered_ending": null
  }
}
```

#### 3.2.4 数据接口

**获取排行榜**

```http
GET /api/leaderboard
Query参数：
- limit: 10 (默认)
- offset: 0 (默认)
- ending_type: "good" (可选)
```

响应：
```json
{
  "success": true,
  "data": {
    "leaderboard": [
      {
        "rank": 1,
        "player_id": 42,
        "username": "survival_master",
        "ending_title": "财务自由",
        "score": 9500,
        "total_days": 30,
        "achieved_at": "2026-04-05T14:20:00Z"
      },
      {
        "rank": 2,
        "player_id": 18,
        "username": "thrifty_gamer",
        "ending_title": "稳健生活",
        "score": 8200,
        "total_days": 28,
        "achieved_at": "2026-04-04T09:15:00Z"
      }
    ],
    "pagination": {
      "total": 150,
      "limit": 10,
      "offset": 0
    }
  }
}
```

### 3.3 错误响应格式

所有接口错误统一格式：

```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "用户名或密码错误",
    "details": {}
  }
}
```

常见错误码：
- `VALIDATION_ERROR`: 参数验证失败
- `AUTH_REQUIRED`: 需要认证
- `INVALID_TOKEN`: Token无效
- `GAME_NOT_FOUND`: 游戏不存在
- `ACTION_NOT_AVAILABLE`: 动作不可用
- `EVENT_NOT_FOUND`: 事件不存在
- `INSUFFICIENT_RESOURCES`: 资源不足