# 小红书数据平台 - Web 架构设计文档

> 作者：Dwight (AI Assistant)  
> 日期：2026-04-11  
> 目标：设计安全的 Web 平台，整合 spider-xhs 爬虫能力，提供可视化数据展示

---

## 目录

1. [现状分析](#1-现状分析)
2. [安全性设计](#2-安全性设计)
3. [系统架构](#3-系统架构)
4. [Web 界面设计](#4-web-界面设计)
5. [数据存储设计](#5-数据存储设计)
6. [API 设计](#6-api-设计)
7. [部署方案](#7-部署方案)
8. [开发路线图](#8-开发路线图)

---

## 1. 现状分析

### 1.1 现有组件

```
spider-xhs/
├── main.py                 # CLI 入口
├── apis/
│   └── xhs_pc_apis.py      # 核心爬虫 API (20+ 接口)
├── xhs_utils/
│   ├── xhs_util.py         # 签名生成、反爬机制
│   ├── cookie_util.py      # Cookie 解析
│   └── data_util.py        # 数据处理
└── static/
    └── *.js                # 反爬签名 JS (69441 行)

comment-insight/
├── backend/app/
│   ├── main.py             # FastAPI 入口
│   ├── analyzer.py         # LLM 评论分析
│   ├── scraper.py          # 爬虫封装
│   └── templates/          # Jinja2 模板
└── backend/requirements.txt
```

### 1.2 核心功能映射

| spider-xhs 功能 | XHS API | 用途 |
|-----------------|---------|------|
| 获取笔记详情 | `/api/sns/web/v1/feed` | 查看笔记内容 |
| 获取笔记评论 | `/api/sns/web/v2/comment/page` | 评论分析 |
| 获取用户笔记 | `/api/sns/web/v1/user_posted` | 用户画像 |
| 获取用户喜欢 | `/api/sns/web/v1/note/like/page` | 兴趣分析 |
| 搜索笔记 | `/api/sns/web/v1/search/notes` | 话题研究 |
| 搜索用户 | `/api/sns/web/v1/search/usersearch` | KOL 查找 |
| 无水印视频 | 网页爬取 | 内容下载 |
| 无水印图片 | URL 转换 | 内容下载 |

### 1.3 当前痛点

| 问题 | 描述 |
|------|------|
| Cookie 管理混乱 | Cookie 明文存储，安全风险高 |
| 无 Web 界面 | 只能通过 CLI 或代码调用 |
| 数据不持久 | 每次爬取结果不保存，无法对比分析 |
| 反爬风险 | 直接暴露爬虫代码，易被封禁 |
| 无权限控制 | 任何人都可以使用，无法区分用户 |

---

## 2. 安全性设计

### 2.1 安全威胁模型

```
┌──────────────────────────────────────────────────────────────┐
│                        威胁向量                               │
├──────────────────────────────────────────────────────────────┤
│ 1. Cookie 泄露      → 攻击者获取用户登录态                    │
│ 2. API 密钥泄露     → 被滥用或耗尽配额                        │
│ 3. XSS 攻击        → 在数据展示区注入恶意代码                 │
│ 4. CSRF            → 诱导用户执行非预期操作                   │
│ 5. 反爬封禁        → IP/账号被小红书封禁                     │
│ 6. 数据泄露        → 爬取的评论数据被公开                     │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 安全设计方案

#### 2.2.1 Cookie 安全

**现状问题：**
```python
# 当前代码直接存储明文 Cookie
COOKIES=''  # spider-xhs/.env
```

**改进方案：**

```
┌─────────────────────────────────────────────────────────────┐
│                    Cookie 安全架构                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   用户浏览器                                                 │
│       │                                                     │
│       ▼                                                     │
│   ┌─────────────────┐                                      │
│   │  OAuth 代理      │  ← 不存储真实 Cookie                  │
│   │  (小红书扫码登录) │                                      │
│   └────────┬────────┘                                      │
│            │ 生成临时 Token                                 │
│            ▼                                                │
│   ┌─────────────────┐                                      │
│   │  Token 存储      │  ← 服务端加密存储                      │
│   │  (AES-256 加密)  │                                      │
│   └────────┬────────┘                                      │
│            │                                               │
│            ▼                                                │
│   ┌─────────────────┐                                      │
│   │  请求时解密      │  ← 每次请求动态解密                    │
│   │  + 请求头注入    │                                      │
│   └─────────────────┘                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**实现要点：**

| 层级 | 技术方案 |
|------|----------|
| 传输层 | HTTPS 强制，HSTS 头 |
| 存储层 | Cookie 加密（AES-256-GCM）存储在数据库 |
| 传输层 | Cookie 仅在后端内部传递，不暴露给前端 |
| 有效期 | Token 有效期 7 天，自动刷新 |
| 隔离 | 不同用户使用不同 Cookie，隔离风险 |

#### 2.2.2 API 鉴权

```python
# JWT + RBAC 鉴权
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

class Role:
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"  # 只读权限

# 权限矩阵
PERMISSIONS = {
    "view_notes": [Role.ADMIN, Role.USER, Role.VIEWER],
    "scrape_notes": [Role.ADMIN, Role.USER],
    "manage_cookies": [Role.ADMIN],
    "export_data": [Role.ADMIN, Role.USER],
}

def require_permission(permission: str):
    async def dependency(credentials: HTTPAuthorizationCredentials = Security(security)):
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        role = payload.get("role", Role.VIEWER)
        if permission not in PERMISSIONS or role not in PERMISSIONS[permission]:
            raise HTTPException(status_code=403, detail="权限不足")
        
        return payload
    return dependency
```

#### 2.2.3 速率限制（Rate Limiting）

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/scrape")
@limiter.limit("10/minute")  # 每分钟 10 次
@require_permission("scrape_notes")
async def scrape_note(request: Request):
    """爬取笔记（速率限制）"""
    pass

@app.post("/api/batch-scrape")
@limiter.limit("2/minute")  # 批量爬取更严格
@require_permission("scrape_notes")
async def batch_scrape(request: Request):
    """批量爬取"""
    pass
```

#### 2.2.4 反爬保护措施

| 措施 | 实现 |
|------|------|
| IP 轮换 | 代理池（可选，高级功能） |
| 请求间隔 | 随机延迟 1-3 秒 |
| User-Agent 轮换 | UA 池随机选择 |
| 失败重试 | 指数退避策略 |
| 封禁检测 | 自动暂停 + 告警 |

---

## 3. 系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                           用户层                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Web UI    │  │  移动端 H5  │  │   API 文档  │  │   CLI 工具  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
└─────────┼────────────────┼────────────────┼────────────────┼────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          网关层 (API Gateway)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  鉴权中间件  │  │  限流中间件  │  │  日志中间件  │  │  缓存中间件  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
└─────────┼────────────────┼────────────────┼────────────────┼────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          业务层 (Service Layer)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  笔记服务    │  │  评论服务    │  │  用户服务    │  │  搜索服务    │ │
│  │ NoteService  │  │CommentService│  │ UserService  │  │SearchService │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                │                │                │         │
│         └────────────────┴────────────────┴────────────────┘         │
│                                 │                                   │
│                                 ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      爬虫调度层                               │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐ │   │
│  │  │  Cookie   │  │  签名     │  │  请求     │  │  重试     │ │   │
│  │  │  管理器    │  │  生成器    │  │  调度器   │  │  策略     │ │   │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘ │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          数据层 (Data Layer)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   SQLite    │  │   Redis     │  │   文件存储   │  │   搜索索引   │ │
│  │  (主数据库)  │  │  (缓存)     │  │  (媒体文件)  │  │  (Meilisearch│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      外部服务 (External Services)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   小红书 API │  │   LLM API   │  │   OSS 服务   │                 │
│  │  (edith.xhs)│  │(OpenAI/Claude)│ │  (媒体存储)  │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 目录结构设计

```
spider-xhs/
├── src/                          # 源代码
│   ├── api/                      # API 层
│   │   ├── __init__.py
│   │   ├── routes/               # 路由
│   │   │   ├── notes.py          # 笔记相关 API
│   │   │   ├── comments.py       # 评论相关 API
│   │   │   ├── users.py          # 用户相关 API
│   │   │   └── search.py         # 搜索 API
│   │   ├── deps.py               # 依赖注入
│   │   └── schemas.py            # Pydantic 模型
│   │
│   ├── core/                     # 核心模块
│   │   ├── __init__.py
│   │   ├── config.py             # 配置管理
│   │   ├── security.py           # 安全相关
│   │   ├── auth.py               # 认证授权
│   │   └── rate_limiter.py       # 限流
│   │
│   ├── services/                 # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── note_service.py        # 笔记服务
│   │   ├── comment_service.py     # 评论服务
│   │   ├── user_service.py        # 用户服务
│   │   ├── search_service.py      # 搜索服务
│   │   └── analysis_service.py    # 分析服务 (LLM)
│   │
│   ├── crawler/                  # 爬虫核心（重构自 spider-xhs）
│   │   ├── __init__.py
│   │   ├── client.py             # 爬虫客户端
│   │   ├── cookie_manager.py     # Cookie 管理
│   │   ├── signer.py             # 签名生成
│   │   └── proxies.py            # 代理管理
│   │
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── database.py           # 数据库连接
│   │   ├── note.py               # 笔记模型
│   │   ├── comment.py            # 评论模型
│   │   ├── user.py               # 用户模型
│   │   └── analysis.py           # 分析结果模型
│   │
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       ├── cache.py              # 缓存工具
│       └── helpers.py            # 辅助函数
│
├── static/                       # 静态资源
│   ├── js/                       # JS 签名文件（保留原有用）
│   └── ...
│
├── templates/                    # 前端模板
│   ├── base.html
│   ├── dashboard.html            # 数据看板
│   ├── notes.html                # 笔记列表
│   ├── note_detail.html          # 笔记详情
│   └── analysis.html             # 分析结果
│
├── tests/                        # 测试
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── migrations/                   # 数据库迁移
│
├── config/                      # 配置文件
│   ├── settings.yaml            # 主配置
│   └── logging.yaml             # 日志配置
│
├── scripts/                      # 脚本
│   ├── init_db.py               # 初始化数据库
│   └── seed_data.py             # 种子数据
│
├── main.py                       # 应用入口
├── requirements.txt              # Python 依赖
├── Dockerfile                    # Docker 配置
├── docker-compose.yml            # Docker Compose
└── README.md
```

---

## 4. Web 界面设计

### 4.1 功能选择界面

```
┌─────────────────────────────────────────────────────────────────────┐
│  🔍 小红书数据平台                              [用户] ▼  设置 ⚙️   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │             │  │             │  │             │  │             ││
│  │   📝        │  │   💬        │  │   👤        │  │   🔎        ││
│  │   笔记分析   │  │   评论洞察   │  │   用户画像   │  │   话题搜索   ││
│  │             │  │             │  │             │  │             ││
│  │  分析单篇    │  │  提取有价值的 │  │  了解博主    │  │  研究热门    ││
│  │  笔记内容    │  │  评论观点    │  │  内容风格    │  │  话题趋势    ││
│  │             │  │             │  │             │  │             ││
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘│
│         │                │                │                │        │
│         └────────────────┴────────────────┴────────────────┘        │
│                                 │                                  │
│                                 ▼                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │             │  │             │  │             │  │             ││
│  │   📊        │  │   📥        │  │   🎯        │  │   ⚙️        ││
│  │   数据看板   │  │   数据导出   │  │   竞品监控   │  │   系统设置   ││
│  │             │  │             │  │             │  │             ││
│  │  可视化展示  │  │  导出 Excel  │  │  追踪博主    │  │  Cookie管理  ││
│  │  历史数据    │  │  导出 JSON  │  │  笔记更新    │  │  API配置    ││
│  │             │  │             │  │             │  │             ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 功能模块详情

#### 4.2.1 笔记分析

```
┌─────────────────────────────────────────────────────────────────────┐
│  📝 笔记分析                                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  笔记链接: [ ________________________________________ ] [ 分析 ]   │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  笔记标题: 如何选择适合自己的护肤品                             │  │
│  │  作者: @护肤达人小美 | 点赞: 2.3w | 收藏: 8900 | 评论: 456    │  │
│  │  发布时间: 2024-03-15 | 话题: #护肤# #种草#                   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────────┐│
│  │ 📊 内容分析        │  │ 💬 评论洞察        │  │ 📈 互动分析      ││
│  ├───────────────────┤  ├───────────────────┤  ├─────────────────┤│
│  │ 类型: 干货分享     │  │ 总评论: 456        │  │ 点赞/粉丝比: 2%  ││
│  │ 情绪: 正面 78%     │  │ 有效评论: 380      │  │ 收藏率: 3.8%     ││
│  │ 关键词: 成分/肤质  │  │ 平均字数: 28       │  │ 评论率: 0.2%     ││
│  └───────────────────┘  └───────────────────┘  └─────────────────┘│
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                       数据图表展示                            │  │
│  │                                                               │  │
│  │    30 ┤          ╭─╮                                        │  │
│  │    25 ┤      ╭─╮╭─╯ ╰─╮    ╭─╮                              │  │
│  │    20 ┤  ╭─╮╭─╯╰─────╯╰─╮╭─╯ ╰─╮                           │  │
│  │    15 ┤╭─╯╰╯           ╰─╯     ╰─╮                          │  │
│  │    10 ┤╰──────────────────────╯                             │  │
│  │     5 ┤                                                       │  │
│  │     0 ┼────────────────────────────────────────              │  │
│  │        一月    二月    三月    四月    五月                   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 4.2.2 评论洞察

```
┌─────────────────────────────────────────────────────────────────────┐
│  💬 评论洞察                                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  笔记链接: [ ________________________________________ ] [ 获取评论 ] │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  总评论数: 456  │  有效分析: 380  │  平均情感: 😊 正面       │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│  │  ✅ 有用总结                 │  │  ⚠️ 避坑指南                 │  │
│  ├─────────────────────────────┤  ├─────────────────────────────┤  │
│  │ • 产品性价比高，适合学生党   │  │ • 实物与图片有色差          │  │
│  │ • 包装精美，物流速度快      │  │ • 客服响应较慢              │  │
│  │ • 肤感清爽，不油腻          │  │ • 量有点少，不适合多人       │  │
│  │ • 成分安全，敏感肌可用      │  │ • 保质期需要注意            │  │
│  └─────────────────────────────┘  └─────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  ❓ 待确认事项                                               │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │ • 是否正品？有用户质疑                                      │  │
│  │ • 适合什么肤质？干皮/油皮反馈不同                           │  │
│  │ • 和某大牌比有什么区别？                                    │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  词云图                                                     │  │
│  │                        性价比                               │  │
│  │                   好用    包装        物流                   │  │
│  │              推荐    质量不错        速度快                  │  │
│  │         使用感受    效果好        颜色差异                 │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 4.2.3 用户画像

```
┌─────────────────────────────────────────────────────────────────────┐
│  👤 用户画像                                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  用户链接: [ ________________________________________ ] [ 查询 ]    │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  博主: @护肤达人小美                                          │  │
│  │  粉丝: 12.5w  │  获赞: 45.6w  │  笔记: 89  │  收藏: 3.2w     │  │
│  │  等级: 金冠    │  认证: 美妆达人 │  地域: 北京                   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  内容风格雷达图                                               │  │
│  │                                                               │  │
│  │             种草                      │ 80%                   │  │
│  │              │                       │                       │  │
│  │              │        干货           │ 75%        │          │  │
│  │         测评 ────────────────────────│ 85%                  │  │
│  │              │        分享           │ 70%        │          │  │
│  │              │                       │            Vlog      │  │
│  │            生活                      │ 40%        │ 60%      │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────┐  ┌───────────────────────────────┐  │
│  │  粉丝画像                  │  │  互动分析                     │  │
│  ├───────────────────────────┤  ├───────────────────────────────┤  │
│  │ 女粉: 85% | 男粉: 15%      │  │  场均点赞: 2300                │  │
│  │ 18-25岁: 60%              │  │  场均评论: 156                 │  │
│  │ 26-35岁: 30%              │  │  场均收藏: 890                 │  │
│  │ 主要地域: 北上广深         │  │  收藏率: 38.7%                 │  │
│  └───────────────────────────┘  └───────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 4.2.4 数据看板

```
┌─────────────────────────────────────────────────────────────────────┐
│  📊 数据看板                                    时间: [最近7天 ▼]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │  📝 笔记数   │  │  💬 评论数   │  │  👥 用户数   │  │  🔍 搜索数  ││
│  │     1,234   │  │    56,789   │  │      567    │  │     890    ││
│  │  ↑ 12.5%   │  │  ↑ 8.3%    │  │  ↑ 15.2%   │  │  ↓ 3.1%   ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  趋势图                                                       │  │
│  │                                                               │  │
│  │  笔记数 ──  评论数 ─ ─                                        │  │
│  │     ╱╲    ╱╲    ╱╲                                           │  │
│  │    ╱  ╲  ╱  ╲  ╱  ╲                                          │  │
│  │ ──╱────╲╱────╲╱────╲──                                        │  │
│  │  周一  周二  周三  周四  周五  周六  周日                      │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────┐  ┌───────────────────────────┐  │
│  │  TOP 5 热门话题                │  │  TOP 5 高互动笔记          │  │
│  ├───────────────────────────────┤  ├───────────────────────────┤  │
│  │ 1. #春季穿搭#        2.3w     │  │ 1. 护肤干货分享    4562    │  │
│  │ 2. #零食推荐#        1.8w     │  │ 2. 家居好物        3891    │  │
│  │ 3. #健身打卡#        1.5w     │  │ 3. 美食教程        3201    │  │
│  │ 4. #护肤心得#        1.2w     │  │ 4. 穿搭分享        2890    │  │
│  │ 5. #旅行攻略#        0.9w     │  │ 5. 彩妆测评        2567    │  │
│  └───────────────────────────────┘  └───────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 技术栈选型

| 层级 | 技术方案 | 理由 |
|------|----------|------|
| **前端框架** | Vue 3 + Vite | 响应式、轻量、生态好 |
| **UI 组件库** | Element Plus | 中文文档完善 |
| **图表库** | ECharts | 丰富的图表类型 |
| **状态管理** | Pinia | Vue 3 官方推荐 |
| **HTTP 客户端** | Axios | 成熟稳定 |
| **后端框架** | FastAPI | 异步性能好、自动文档 |
| **数据库** | SQLite (MVP) / PostgreSQL (生产) | 简单/生产级 |
| **缓存** | Redis | 高性能缓存 |
| **ORM** | SQLAlchemy 2.0 | 异步支持、类型安全 |
| **LLM** | OpenAI / Claude | 评论分析 |

---

## 5. 数据存储设计

### 5.1 数据库模型

```sql
-- 用户表
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',  -- admin, user, viewer
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 笔记表
CREATE TABLE notes (
    id VARCHAR(36) PRIMARY KEY,
    note_id VARCHAR(50) UNIQUE NOT NULL,  -- 小红书笔记 ID
    title VARCHAR(500),
    content TEXT,
    author_id VARCHAR(50),
    author_name VARCHAR(100),
    liked_count INT DEFAULT 0,
    collected_count INT DEFAULT 0,
    commented_count INT DEFAULT 0,
    share_count INT DEFAULT 0,
    tags TEXT,  -- JSON 数组
    raw_data TEXT,  -- 原始 JSON
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 评论表
CREATE TABLE comments (
    id VARCHAR(36) PRIMARY KEY,
    comment_id VARCHAR(50) NOT NULL,  -- 小红书评论 ID
    note_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(50),
    user_name VARCHAR(100),
    content TEXT,
    liked_count INT DEFAULT 0,
    parent_comment_id VARCHAR(50),  -- 二级评论指向
    sentiment VARCHAR(20),  -- positive, neutral, negative
    is_analyzed BOOLEAN DEFAULT FALSE,
    raw_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (note_id) REFERENCES notes(id)
);

-- 分析结果表
CREATE TABLE analysis_results (
    id VARCHAR(36) PRIMARY KEY,
    note_id VARCHAR(36) NOT NULL,
    summary TEXT,  -- JSON 数组
    pitfalls TEXT,  -- JSON 数组
    uncertain TEXT,  -- JSON 数组
    sentiment_stats TEXT,  -- JSON
    analyzed_by VARCHAR(36),  -- user_id
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (note_id) REFERENCES notes(id)
);

-- Cookie 存储表（加密）
CREATE TABLE cookies (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    platform VARCHAR(20) NOT NULL,  -- xiaohongshu
    encrypted_cookie TEXT NOT NULL,  -- AES-256 加密
    iv VARCHAR(32) NOT NULL,  -- 初始向量
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 搜索历史表
CREATE TABLE search_history (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    keyword VARCHAR(200),
    search_type VARCHAR(20),  -- note, user
    results_count INT,
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 操作日志表
CREATE TABLE operation_logs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    action VARCHAR(50),
    resource_type VARCHAR(20),
    resource_id VARCHAR(50),
    details TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_notes_note_id ON notes(note_id);
CREATE INDEX idx_comments_note_id ON comments(note_id);
CREATE INDEX idx_comments_user ON comments(user_id);
CREATE INDEX idx_cookies_user ON cookies(user_id);
CREATE INDEX idx_search_history_user ON search_history(user_id);
```

### 5.2 Redis 缓存设计

```python
# 缓存键设计
CACHE_KEYS = {
    # 笔记缓存 (1小时)
    "note:{note_id}": {
        "ttl": 3600,
        "desc": "笔记详情"
    },
    # 评论缓存 (30分钟)
    "comments:{note_id}": {
        "ttl": 1800,
        "desc": "笔记评论"
    },
    # 用户信息缓存 (2小时)
    "user:{user_id}": {
        "ttl": 7200,
        "desc": "用户信息"
    },
    # 搜索结果缓存 (15分钟)
    "search:{keyword}:{page}": {
        "ttl": 900,
        "desc": "搜索结果"
    },
    # 限流计数
    "rate:{user_id}:{endpoint}": {
        "ttl": 60,
        "desc": "速率限制计数"
    }
}
```

---

## 6. API 设计

### 6.1 API 规范

```yaml
openapi: 3.0.0
info:
  title: 小红书数据平台 API
  version: 1.0.0
  description: 安全的小红书数据采集和分析平台

servers:
  - url: https://api.example.com/v1
    description: 生产环境
  - url: http://localhost:8000/v1
    description: 开发环境

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

paths:
  /auth/login:
    post:
      summary: 用户登录
      tags: [认证]
      security: []
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required: [username, password]
              properties:
                username: { type: string }
                password: { type: string }
      responses:
        '200':
          description: 登录成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token: { type: string }
                  token_type: { type: string }
                  expires_in: { type: integer }

  /notes/{note_id}:
    get:
      summary: 获取笔记详情
      tags: [笔记]
      security: [{ bearerAuth: [] }]
      parameters:
        - name: note_id
          in: path
          required: true
          schema: { type: string }
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Note'

  /notes/{note_id}/comments:
    get:
      summary: 获取笔记评论
      tags: [评论]
      security: [{ bearerAuth: [] }]
      parameters:
        - name: note_id
          in: path
          required: true
        - name: page
          in: query
          schema: { type: integer, default: 1 }
        - name: page_size
          in: query
          schema: { type: integer, default: 20, maximum: 100 }
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  items: { type: array, items: { $ref: '#/components/schemas/Comment' } }
                  total: { type: integer }
                  page: { type: integer }
                  page_size: { type: integer }

  /notes/{note_id}/analyze:
    post:
      summary: 分析笔记评论
      tags: [分析]
      security: [{ bearerAuth: [] }]
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                max_comments: { type: integer, default: 100 }
                model_provider: { type: string, enum: [openai, claude, mock] }
      responses:
        '200':
          description: 分析完成
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AnalysisResult'

  /users/{user_id}:
    get:
      summary: 获取用户信息
      tags: [用户]
      security: [{ bearerAuth: [] }]

  /users/{user_id}/notes:
    get:
      summary: 获取用户笔记列表
      tags: [用户]
      security: [{ bearerAuth: [] }]

  /search:
    get:
      summary: 搜索笔记/用户
      tags: [搜索]
      security: [{ bearerAuth: [] }]
      parameters:
        - name: q
          in: query
          required: true
        - name: type
          in: query
          enum: [notes, users]
        - name: sort
          in: query
          enum: [general, time_descending, popularity_descending]

  /cookies:
    post:
      summary: 添加 Cookie（管理员）
      tags: [系统]
      security: [{ bearerAuth: [] }]
    get:
      summary: 获取 Cookie 状态
      tags: [系统]
      security: [{ bearerAuth: [] }]

schemas:
  Note:
    type: object
    properties:
      id: { type: string }
      note_id: { type: string }
      title: { type: string }
      content: { type: string }
      author: { type: object }
      stats:
        type: object
        properties:
          liked: { type: integer }
          collected: { type: integer }
          commented: { type: integer }

  Comment:
    type: object
    properties:
      id: { type: string }
      content: { type: string }
      user: { type: object }
      liked_count: { type: integer }
      sub_comments: { type: array, items: { type: object } }

  AnalysisResult:
    type: object
    properties:
      summary: { type: array, items: { type: string } }
      pitfalls: { type: array, items: { type: string } }
      uncertain: { type: array, items: { type: string } }
      sentiment:
        type: object
        properties:
          positive: { type: number }
          neutral: { type: number }
          negative: { type: number }
```

### 6.2 核心 API 实现

```python
# src/api/routes/notes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.deps import get_db, get_current_user
from src.api.schemas import NoteResponse, NoteListResponse
from src.services.note_service import NoteService

router = APIRouter(prefix="/notes", tags=["笔记"])

@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取笔记详情"""
    # 1. 尝试从缓存获取
    cached = await cache.get(f"note:{note_id}")
    if cached:
        return cached
    
    # 2. 尝试从数据库获取
    note = await NoteService.get_by_note_id(db, note_id)
    
    # 3. 如果数据库没有，爬取
    if not note:
        cookie = await CookieManager.get_active_cookie(db)
        if not cookie:
            raise HTTPException(status_code=400, detail="请先配置 Cookie")
        
        note = await NoteService.scrape_and_save(db, note_id, cookie)
    
    # 4. 缓存结果
    await cache.set(f"note:{note_id}", note, ttl=3600)
    
    return note


@router.get("/{note_id}/comments", response_model=NoteListResponse)
async def get_comments(
    note_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取笔记评论（分页）"""
    comments = await NoteService.get_comments(db, note_id, page, page_size)
    total = await NoteService.count_comments(db, note_id)
    
    return {
        "items": comments,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/{note_id}/analyze")
async def analyze_note(
    note_id: str,
    max_comments: int = 100,
    model_provider: str = "mock",
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """分析笔记评论（调用 LLM）"""
    # 1. 获取评论
    comments = await NoteService.get_all_comments(db, note_id, max_comments)
    
    # 2. 调用 LLM 分析
    analyzer = CommentAnalyzer(provider=model_provider)
    result = await analyzer.analyze(comments)
    
    # 3. 保存结果
    await AnalysisService.save_result(db, note_id, result, current_user.id)
    
    return result
```

---

## 7. 部署方案

### 7.1 Docker Compose 部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/app.db
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    volumes:
      - ./data:/app/data
      - ./static:/app/static
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped

volumes:
  redis_data:
```

### 7.2 环境变量

```bash
# .env
# 应用配置
APP_NAME=小红书数据平台
APP_VERSION=1.0.0
DEBUG=false

# 安全配置
SECRET_KEY=your-secret-key-here  # 生成: python -c "import secrets; print(secrets.token_hex(32))"
ENCRYPTION_KEY=your-encryption-key  # AES-256 密钥

# 数据库
DATABASE_URL=sqlite:///./data/app.db
# 生产环境: postgresql://user:pass@localhost:5432/app

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM API
OPENAI_API_KEY=sk-xxx
CLAUDE_API_KEY=sk-ant-xxx
LLM_PROVIDER=openai

# Cookie 加密
COOKIE_ENCRYPTION_ENABLED=true
```

---

## 8. 开发路线图

### 8.1 Phase 1: MVP（1-2周）

| 任务 | 描述 | 优先级 |
|------|------|--------|
| 项目初始化 | 创建目录结构、配置 | P0 |
| 用户认证 | 注册/登录/JWT | P0 |
| Cookie 管理 | 安全存储、加密 | P0 |
| 笔记爬取 | 单笔记详情爬取 | P0 |
| 评论获取 | 获取并存储评论 | P0 |
| 基础 Web UI | 功能选择界面 | P1 |
| 笔记详情页 | 显示笔记内容和统计 | P1 |

### 8.2 Phase 2: 核心功能（2-3周）

| 任务 | 描述 | 优先级 |
|------|------|--------|
| 评论分析 | LLM 驱动的评论分析 | P0 |
| 数据看板 | 统计图表展示 | P1 |
| 搜索功能 | 关键词搜索笔记 | P1 |
| 用户画像 | 用户信息爬取和分析 | P2 |
| 数据导出 | Excel/JSON 导出 | P2 |

### 8.3 Phase 3: 高级功能（持续迭代）

| 任务 | 描述 | 优先级 |
|------|------|--------|
| 批量爬取 | 定时任务、批量处理 | P2 |
| 竞品监控 | 监控指定用户/话题 | P2 |
| 代理池 | IP 轮换、防封禁 | P3 |
| 微信小程序 | 移动端支持 | P3 |

---

## 附录

### A. 技术栈汇总

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端框架 | Vue 3 | 3.4+ |
| 构建工具 | Vite | 5.0+ |
| UI 组件 | Element Plus | 2.5+ |
| 图表 | ECharts | 5.4+ |
| 后端框架 | FastAPI | 0.109+ |
| 数据库 | SQLite/PostgreSQL | - |
| 缓存 | Redis | 7.0+ |
| ORM | SQLAlchemy | 2.0+ |
| 认证 | JWT | - |
| 加密 | AES-256-GCM | - |

### B. 参考资料

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Vue 3 文档](https://vuejs.org/)
- [Element Plus](https://element-plus.org/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)

---

*文档版本: v1.0.0*
*最后更新: 2026-04-11*
